"""
Week 5 All Groups Discussion Parser
Parses markdown-format discussion exports for Groups A, B, C into three standard CSVs.
"""
import csv
import re
import os
from datetime import datetime
from collections import defaultdict
import math

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
WEEK_NUMBER = "Week 5"

# Files and their group names
GROUP_FILES = {
    "Group A": "_ENGL_325_VL7_Advanced_Business_Writing_Spring_2026_Jan_12_May_8__Weeks_5_6_Group_A__2026-02-18.md",
    "Group B": "_ENGL_325_VL7_Advanced_Business_Writing_Spring_2026_Jan_12_May_8__Weeks_5_6_Group_B__2026-02-18.md",
    "Group C": "_ENGL_325_VL7_Advanced_Business_Writing_Spring_2026_Jan_12_May_8__Weeks_5_6_Group_C__2026-02-18.md",
}

# Week 5 role assignments from role_assignments.csv
ROLE_ASSIGNMENTS = {
    "Group A": {
        "Jessica Padgett": ("Facilitator", "Business/Management"),
        "Nathan Haygood": ("Cast Mapper", "Technical/Applied"),
        "Lexi Minzey": ("Solution Designer", "Healthcare/Service"),
        "Mekyle Harris": ("Message Designer", "Criminal Justice"),
        "Lindsey T Allen": ("Delivery Specialist", "Business/Management"),
        "Jason Bogue": ("Cultural Analyst", "Technical/Applied"),
    },
    "Group B": {
        "Liz Ann Dumas": ("Facilitator", "Business/Management"),
        "Tyler Craig": ("Cast Mapper", "Technical/Applied"),
        "Brianna E Hamilton": ("Solution Designer", "Healthcare/Service"),
        "Alixandria Williamson": ("Message Designer", "Criminal Justice"),
        "Payton N Hamblin": ("Delivery Specialist", "Business/Management"),
        "Chandler Atton": ("Cultural Analyst", "Other"),
    },
    "Group C": {
        "Klay Niltasuwan": ("Facilitator", "Business/Management"),
        "Brennan Monarch": ("Cast Mapper", "Technical/Applied"),
        "Cody Batho": ("Solution Designer", "Healthcare/Technical"),
        "Michael Helsel": ("Message Designer", "Technical/Applied"),
        "Allie Barber": ("Delivery Specialist", "Business/Management"),
        "Sam Baldwin": ("Cultural Analyst", "Business/Management"),
    },
}

ALL_STUDENT_NAMES = set()
for group_roles in ROLE_ASSIGNMENTS.values():
    ALL_STUDENT_NAMES.update(group_roles.keys())

# Role keywords for detection
ROLE_KEYWORDS = {
    "Facilitator": ["facilitate", "guide", "direction", "consensus", "what does everyone think",
                     "let's focus on", "moving forward", "on track", "let me know", "as a group"],
    "Cast Mapper": ["stakeholder", "power dynamic", "relationship", "who is involved", "interests",
                     "CAST", "context", "audience", "strategy", "tone", "power"],
    "Message Designer": ["frame", "tone", "audience", "message", "communicate", "persuade",
                          "draft", "letter", "wording", "craft"],
    "Solution Designer": ["solution", "propose", "recommendation", "alternative", "actionable",
                           "checklist", "plan", "outline", "approach"],
    "Delivery Specialist": ["medium", "channel", "timing", "format", "delivery", "how to send",
                             "structure", "clear", "follow", "email", "letter"],
    "Cultural Analyst": ["culture", "cultural", "trust", "organizational", "workplace", "power",
                          "hierarchy", "centralized", "owner-driven", "brand", "reputation"],
}

# Authenticity markers
AUTHENTICITY_PATTERNS = [
    r"\bin my experience\b", r"\bat my job\b", r"\bwhen I worked\b", r"\bI think\b",
    r"\bI believe\b", r"\bI'm\b", r"\bdon't\b", r"\bwon't\b", r"\bcan't\b",
    r"\bwouldn't\b", r"\bshouldn't\b", r"\bcouldn't\b", r"\bto be honest\b",
    r"\bhonestly\b", r"\bmaybe\b", r"\bactually wait\b", r"\blet me rephrase\b",
    r"\bI also want\b", r"\bI was excited\b", r"\bmy son\b", r"\bI've been\b",
    r"\bfrom my experience\b", r"\bI had been\b", r"\bI always find myself\b",
    r"\bI guess\b", r"\bI'm not sure\b",
]

# AI pattern flags
AI_PATTERNS = [
    r"This response does an excellent job",
    r"I completely agree with",
    r"You make an excellent point",
    r"This is a very thoughtful response",
    r"one method to further this concept",
    r"it could be beneficial to",
    r"it would also be beneficial",
    r"Here are \d+ considerations",
    r"Key areas include",
    r"it is also important to note",
    r"ensures? that .+ (?:is|are) both .+ and",
    r"demonstrates? .+ understanding",
]


def parse_posts(filepath, group_name):
    """Parse the markdown discussion file into post dicts."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    header_pattern = re.compile(
        r"^### (.+?) \| Depth (\d+) \| (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)$",
        re.MULTILINE
    )

    matches = list(header_pattern.finditer(content))
    posts = []

    for i, match in enumerate(matches):
        name = match.group(1).strip()
        depth = int(match.group(2))
        timestamp_str = match.group(3)

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        post_content = content[start:end].strip()

        # Clean up HTML entities
        post_content = post_content.replace("&nbsp;", " ")
        post_content = re.sub(r"\s+", " ", post_content).strip()

        # Skip instructor posts
        if name == "Bill A Jackson":
            continue

        dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%I:%M %p")
        day_of_week = dt.strftime("%A")
        timestamp_formatted = dt.strftime("%Y-%m-%d %I:%M %p")

        posts.append({
            "name": name,
            "depth": depth,
            "datetime": dt,
            "timestamp": timestamp_formatted,
            "date": date_str,
            "time": time_str,
            "day_of_week": day_of_week,
            "content": post_content,
            "group": group_name,
            "index": i,
        })

    return posts


def assign_threading(posts):
    """Determine ReplyingTo and ThreadStarter based on depth."""
    current_thread_starter = None

    for post in posts:
        if post["depth"] == 0:
            post["post_type"] = "main"
            post["replying_to"] = ""
            post["thread_starter"] = post["name"]
            current_thread_starter = post["name"]
        else:
            post["post_type"] = "reply"
            post["replying_to"] = current_thread_starter or ""
            post["thread_starter"] = current_thread_starter or ""

    return posts


def count_words(text):
    return len(text.split())


def count_questions(text):
    return text.count("?")


def mentions_other_student(text, author, group_students):
    """Check if text mentions another student by first or full name."""
    text_lower = text.lower()
    for name in group_students:
        if name == author:
            continue
        if name.lower() in text_lower:
            return True
        first = name.split()[0].lower()
        if len(first) > 2 and first in text_lower:
            return True
    return False


def count_role_keywords(text, role):
    if not role or role not in ROLE_KEYWORDS:
        return 0, ""
    text_lower = text.lower()
    found = []
    for kw in ROLE_KEYWORDS[role]:
        if kw.lower() in text_lower:
            found.append(kw)
    return len(found), "; ".join(found)


def count_authenticity_markers(text):
    text_lower = text.lower()
    count = 0
    for pattern in AUTHENTICITY_PATTERNS:
        if re.search(pattern, text_lower):
            count += 1
    return count


def count_ai_patterns(text):
    text_lower = text.lower()
    count = 0
    for pattern in AI_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            count += 1
    return count


def generate_raw_csv(all_posts, output_path):
    """Generate discussion_posts_raw.csv for all groups."""
    fieldnames = [
        "StudentName", "Timestamp", "Date", "Time", "DayOfWeek",
        "PostType", "ReplyingTo", "ThreadStarter", "Content",
        "WordCount", "QuestionCount", "MentionsOtherStudent",
        "GroupName", "WeekNumber", "RoleKeywordFound",
        "AuthenticityMarkers", "AIPatternFlags"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for post in all_posts:
            group = post["group"]
            group_students = set(ROLE_ASSIGNMENTS[group].keys())
            role_info = ROLE_ASSIGNMENTS[group].get(post["name"])
            role = role_info[0] if role_info else ""
            rk_count, rk_found = count_role_keywords(post["content"], role)

            writer.writerow({
                "StudentName": post["name"],
                "Timestamp": post["timestamp"],
                "Date": post["date"],
                "Time": post["time"],
                "DayOfWeek": post["day_of_week"],
                "PostType": post["post_type"],
                "ReplyingTo": post["replying_to"],
                "ThreadStarter": post["thread_starter"],
                "Content": post["content"],
                "WordCount": count_words(post["content"]),
                "QuestionCount": count_questions(post["content"]),
                "MentionsOtherStudent": mentions_other_student(post["content"], post["name"], group_students),
                "GroupName": group,
                "WeekNumber": WEEK_NUMBER,
                "RoleKeywordFound": rk_found if rk_found else "",
                "AuthenticityMarkers": count_authenticity_markers(post["content"]),
                "AIPatternFlags": count_ai_patterns(post["content"]),
            })

    print(f"  Raw CSV: {len(all_posts)} posts written")


def generate_student_summary(all_posts, output_path):
    """Generate discussion_student_summary.csv for all groups."""
    students = defaultdict(lambda: {
        "posts": [], "main_posts": 0, "replies": 0,
        "total_words": 0, "questions": 0, "replied_to": set(),
        "inbound_replies": 0, "inbound_reply_students": set(),
        "referenced_others": False, "referenced_others_count": 0,
        "dates": set(), "first_dt": None, "last_dt": None,
        "role_explicitly_named": False, "role_keywords_used": 0,
        "authenticity_score": 0, "ai_pattern_score": 0,
        "threads_started": 0, "threads_participated": set(),
    })

    # First pass
    for post in all_posts:
        key = (post["name"], post["group"])
        s = students[key]
        s["posts"].append(post)
        wc = count_words(post["content"])
        s["total_words"] += wc
        s["questions"] += count_questions(post["content"])
        s["dates"].add(post["date"])
        s["authenticity_score"] += count_authenticity_markers(post["content"])
        s["ai_pattern_score"] += count_ai_patterns(post["content"])

        group_students = set(ROLE_ASSIGNMENTS[post["group"]].keys())
        role_info = ROLE_ASSIGNMENTS[post["group"]].get(post["name"])
        role = role_info[0] if role_info else ""
        rk_count, _ = count_role_keywords(post["content"], role)
        s["role_keywords_used"] += rk_count

        if role and role.lower() in post["content"].lower():
            s["role_explicitly_named"] = True

        if post["post_type"] == "main":
            s["main_posts"] += 1
            s["threads_started"] += 1
        else:
            s["replies"] += 1
            if post["replying_to"]:
                s["replied_to"].add(post["replying_to"])

        if post["thread_starter"]:
            s["threads_participated"].add(post["thread_starter"])

        if mentions_other_student(post["content"], post["name"], group_students):
            s["referenced_others"] = True
            s["referenced_others_count"] += 1

        dt = post["datetime"]
        if s["first_dt"] is None or dt < s["first_dt"]:
            s["first_dt"] = dt
        if s["last_dt"] is None or dt > s["last_dt"]:
            s["last_dt"] = dt

    # Second pass: inbound replies
    for post in all_posts:
        if post["post_type"] == "reply" and post["replying_to"]:
            target = post["replying_to"]
            target_key = (target, post["group"])
            if target_key in students and target != post["name"]:
                students[target_key]["inbound_replies"] += 1
                students[target_key]["inbound_reply_students"].add(post["name"])

    fieldnames = [
        "StudentName", "GroupName", "WeekNumber", "AssignedRole",
        "TotalPosts", "MainPosts", "Replies", "TotalWords", "AvgWordsPerPost",
        "QuestionsAsked", "UniqueStudentsRepliedTo", "InboundReplies",
        "InboundReplyStudents", "UniqueStudentsEngaged",
        "ReferencedOthers", "ReferencedOthersCount",
        "PostedEarly", "DaysActive", "FirstPostDay", "LastPostDay",
        "FirstPostTimestamp", "RoleExplicitlyNamed", "RoleKeywordsUsed",
        "AuthenticityScore", "AIPatternScore",
        "ThreadsStarted", "ThreadsParticipatedIn"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for group_name in ["Group A", "Group B", "Group C"]:
            group_roles = ROLE_ASSIGNMENTS[group_name]
            for name in sorted(group_roles.keys()):
                key = (name, group_name)
                s = students[key]
                total_posts = len(s["posts"])
                role = group_roles[name][0]

                if total_posts == 0:
                    writer.writerow({
                        "StudentName": name,
                        "GroupName": group_name,
                        "WeekNumber": WEEK_NUMBER,
                        "AssignedRole": role,
                        "TotalPosts": 0, "MainPosts": 0, "Replies": 0,
                        "TotalWords": 0, "AvgWordsPerPost": 0,
                        "QuestionsAsked": 0, "UniqueStudentsRepliedTo": 0,
                        "InboundReplies": 0, "InboundReplyStudents": 0,
                        "UniqueStudentsEngaged": 0,
                        "ReferencedOthers": False, "ReferencedOthersCount": 0,
                        "PostedEarly": False, "DaysActive": 0,
                        "FirstPostDay": "N/A", "LastPostDay": "N/A",
                        "FirstPostTimestamp": "N/A",
                        "RoleExplicitlyNamed": False, "RoleKeywordsUsed": 0,
                        "AuthenticityScore": 0, "AIPatternScore": 0,
                        "ThreadsStarted": 0, "ThreadsParticipatedIn": 0,
                    })
                    continue

                unique_replied_to = s["replied_to"] - {name}
                inbound_students = s["inbound_reply_students"]
                unique_engaged = unique_replied_to | inbound_students

                posted_early = any(
                    post["datetime"] <= datetime(2026, 2, 12, 23, 59, 59)
                    for post in s["posts"]
                )

                writer.writerow({
                    "StudentName": name,
                    "GroupName": group_name,
                    "WeekNumber": WEEK_NUMBER,
                    "AssignedRole": role,
                    "TotalPosts": total_posts,
                    "MainPosts": s["main_posts"],
                    "Replies": s["replies"],
                    "TotalWords": s["total_words"],
                    "AvgWordsPerPost": round(s["total_words"] / total_posts, 1),
                    "QuestionsAsked": s["questions"],
                    "UniqueStudentsRepliedTo": len(unique_replied_to),
                    "InboundReplies": s["inbound_replies"],
                    "InboundReplyStudents": len(inbound_students),
                    "UniqueStudentsEngaged": len(unique_engaged),
                    "ReferencedOthers": s["referenced_others"],
                    "ReferencedOthersCount": s["referenced_others_count"],
                    "PostedEarly": posted_early,
                    "DaysActive": len(s["dates"]),
                    "FirstPostDay": s["first_dt"].strftime("%A") if s["first_dt"] else "N/A",
                    "LastPostDay": s["last_dt"].strftime("%A") if s["last_dt"] else "N/A",
                    "FirstPostTimestamp": s["first_dt"].strftime("%Y-%m-%d %I:%M %p") if s["first_dt"] else "N/A",
                    "RoleExplicitlyNamed": s["role_explicitly_named"],
                    "RoleKeywordsUsed": s["role_keywords_used"],
                    "AuthenticityScore": s["authenticity_score"],
                    "AIPatternScore": s["ai_pattern_score"],
                    "ThreadsStarted": s["threads_started"],
                    "ThreadsParticipatedIn": len(s["threads_participated"]),
                })

    total_students = sum(len(g) for g in ROLE_ASSIGNMENTS.values())
    print(f"  Student summary: {total_students} students written")


def generate_group_summary(all_posts, output_path):
    """Generate discussion_group_summary.csv for all groups."""
    fieldnames = [
        "GroupName", "WeekNumber", "TotalStudents", "ActiveStudents",
        "TotalPosts", "TotalMainPosts", "TotalReplies",
        "AvgPostsPerStudent", "AvgRepliesPerStudent",
        "TotalWords", "AvgWordsPerPost", "AvgWordsPerStudent",
        "TotalQuestions", "ThreadCount", "AvgThreadDepth", "MaxThreadDepth",
        "ParticipationSpread", "CrossEngagement", "EarlyPostingRate",
        "StudentsWhoPosted", "StudentsWhoDidNotPost",
        "GroupAuthenticityScore", "GroupAIPatternScore"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for group_name in ["Group A", "Group B", "Group C"]:
            group_posts = [p for p in all_posts if p["group"] == group_name]
            group_roles = ROLE_ASSIGNMENTS[group_name]
            total_students = len(group_roles)
            active_students = len(set(p["name"] for p in group_posts))
            total_posts = len(group_posts)
            main_posts = sum(1 for p in group_posts if p["post_type"] == "main")
            total_replies = sum(1 for p in group_posts if p["post_type"] == "reply")
            total_words = sum(count_words(p["content"]) for p in group_posts)
            total_questions = sum(count_questions(p["content"]) for p in group_posts)

            thread_count = main_posts
            avg_thread_depth = round(total_replies / main_posts, 2) if main_posts > 0 else 0
            max_depth = max(p["depth"] for p in group_posts) if group_posts else 0

            # Participation spread
            posts_per_student = defaultdict(int)
            for p in group_posts:
                posts_per_student[p["name"]] += 1
            for name in group_roles:
                if name not in posts_per_student:
                    posts_per_student[name] = 0
            counts = list(posts_per_student.values())
            mean_posts = sum(counts) / len(counts)
            variance = sum((c - mean_posts) ** 2 for c in counts) / len(counts)
            spread = round(math.sqrt(variance), 2)

            # Cross engagement
            actual_connections = set()
            for p in group_posts:
                if p["post_type"] == "reply" and p["replying_to"] and p["replying_to"] != p["name"]:
                    actual_connections.add((p["name"], p["replying_to"]))
            possible = total_students * (total_students - 1)
            cross_engagement = f"{round(len(actual_connections) / possible * 100, 1)}%" if possible > 0 else "0.0%"

            # Early posting rate
            early_students = set()
            for p in group_posts:
                if p["datetime"] <= datetime(2026, 2, 12, 23, 59, 59):
                    early_students.add(p["name"])
            early_rate = f"{round(len(early_students) / total_students * 100, 1)}%"

            auth_score = sum(count_authenticity_markers(p["content"]) for p in group_posts)
            ai_score = sum(count_ai_patterns(p["content"]) for p in group_posts)

            writer.writerow({
                "GroupName": group_name,
                "WeekNumber": WEEK_NUMBER,
                "TotalStudents": total_students,
                "ActiveStudents": active_students,
                "TotalPosts": total_posts,
                "TotalMainPosts": main_posts,
                "TotalReplies": total_replies,
                "AvgPostsPerStudent": round(total_posts / total_students, 1),
                "AvgRepliesPerStudent": round(total_replies / total_students, 2),
                "TotalWords": total_words,
                "AvgWordsPerPost": round(total_words / total_posts, 1) if total_posts else 0,
                "AvgWordsPerStudent": round(total_words / total_students, 1),
                "TotalQuestions": total_questions,
                "ThreadCount": thread_count,
                "AvgThreadDepth": avg_thread_depth,
                "MaxThreadDepth": max_depth,
                "ParticipationSpread": spread,
                "CrossEngagement": cross_engagement,
                "EarlyPostingRate": early_rate,
                "StudentsWhoPosted": active_students,
                "StudentsWhoDidNotPost": total_students - active_students,
                "GroupAuthenticityScore": auth_score,
                "GroupAIPatternScore": ai_score,
            })

    print(f"  Group summary: 3 rows written")


def main():
    all_posts = []

    for group_name, filename in GROUP_FILES.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  WARNING: {filename} not found, skipping {group_name}")
            continue

        print(f"Parsing {group_name}...")
        posts = parse_posts(filepath, group_name)
        posts = assign_threading(posts)
        print(f"  Found {len(posts)} student posts")
        all_posts.extend(posts)

    print(f"\nTotal posts across all groups: {len(all_posts)}")

    raw_path = os.path.join(OUTPUT_DIR, "discussion_posts_raw.csv")
    summary_path = os.path.join(OUTPUT_DIR, "discussion_student_summary.csv")
    group_path = os.path.join(OUTPUT_DIR, "discussion_group_summary.csv")

    generate_raw_csv(all_posts, raw_path)
    generate_student_summary(all_posts, summary_path)
    generate_group_summary(all_posts, group_path)

    # Validation report
    print("\n--- VALIDATION ---")
    for group_name in ["Group A", "Group B", "Group C"]:
        group_posts = [p for p in all_posts if p["group"] == group_name]
        group_students = set(p["name"] for p in group_posts)
        expected = set(ROLE_ASSIGNMENTS[group_name].keys())
        missing = expected - group_students
        print(f"\n{group_name}:")
        print(f"  Posts: {len(group_posts)}")
        print(f"  Active students: {len(group_students)} / {len(expected)}")
        if missing:
            print(f"  ABSENT: {', '.join(sorted(missing))}")
        else:
            print(f"  All students posted.")

        # Check for names not in roster
        unknown = group_students - expected
        if unknown:
            print(f"  UNKNOWN NAMES (not in roster): {', '.join(sorted(unknown))}")

    zero_word = [p for p in all_posts if count_words(p["content"]) == 0]
    if zero_word:
        print(f"\nPosts with zero words: {len(zero_word)}")

    print(f"\nCSVs written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
