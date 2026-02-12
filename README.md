# ENGL 325 · Discussion Pulse

Analytics dashboards for ENGL 325 Advanced Business Writing discussion groups.

## Structure

```
ENGL325-Pulse/
  index.html            ← Student-facing dashboard (embed in Canvas)
  instructor.html       ← Your grading/tracking view (bookmark, don't share)
  data/
    week2/              ← One folder per week
    week3/
    week4/
      discussion_student_summary.csv
      discussion_group_summary.csv
      discussion_posts_raw.csv
      qualitative_assessment.csv    ← Optional (from Claude analysis)
    week5/
    ...
```

## Canvas Embed

Students see: `https://billjackson4242.github.io/ENGL325-Pulse/`

To embed in Canvas, add an iframe to a page or announcement:

```html
<iframe src="https://billjackson4242.github.io/ENGL325-Pulse/" width="100%" height="800" frameborder="0"></iframe>
```

Or just post the direct link. The page is self-contained and mobile-friendly.

## Weekly Workflow (Monday morning, ~20 minutes)

### Step 1: Scrape & Parse (Code You)
1. Go to Canvas → Discussion → this week's group threads
2. Open browser DevTools → copy the discussion HTML/text
3. Paste into a .txt file
4. Send to Code You with the parser prompt
5. Code You generates 3 CSVs:
   - `discussion_student_summary.csv`
   - `discussion_group_summary.csv`
   - `discussion_posts_raw.csv`

### Step 2: Qualitative Analysis (Claude/App You)
1. Upload the 3 CSVs to Claude
2. Ask for qualitative assessment
3. Claude generates `qualitative_assessment.csv` with columns:
   - StudentName, Group, Week, Role, RoleFulfilled, Substantive, RiskTaking, Flag, FlagReason, FeedbackNotes
4. Save as `qualitative_assessment.csv`

### Step 3: Upload to GitHub
1. Go to this repo on GitHub
2. Navigate to `data/` folder
3. Create new folder: `week5` (or whatever week)
4. Upload all 4 CSVs into that folder
5. Commit

### Step 4: Enable the Week
Edit `index.html` and `instructor.html` — find the WEEKS array and set `available: true` for the new week:

```javascript
{ key: 'week5', label: 'Wk 5', folder: 'week5', rotation: 'Rotation 2', available: true },
```

Also add the instructor note and patterns for the new week.

Commit and push. GitHub Pages updates within ~60 seconds.

### Step 5 (Optional): Post Patterns
Copy/adapt the "Patterns Worth Noticing" section content into a Canvas announcement for the class.

## Adding a New Week (Checklist)

- [ ] CSVs in `data/weekN/` folder
- [ ] `available: true` in both HTML files' WEEKS array
- [ ] Instructor note written in student dashboard's WEEKS config
- [ ] Patterns written in student dashboard's PATTERNS config
- [ ] Commit + push
- [ ] Verify at live URL

## Qualitative CSV Format

The qualitative assessment CSV should have these columns (Claude will generate this):

| Column | Values | Notes |
|--------|--------|-------|
| StudentName | "Last, First" or "First Last" | Dashboard handles both formats |
| Group | "Group A" etc. | |
| Week | "3" or "Week 3" | |
| Role | Role name | |
| RoleFulfilled | Yes / Partial / No | |
| Substantive | Yes / Moderate / No | |
| RiskTaking | High / Moderate / Low / None | |
| Flag | None / Concern / ABSENT / etc. | Free text |
| FlagReason | Brief explanation | Only if Flag != None |
| FeedbackNotes | Full narrative | Your detailed assessment |

## Notes

- Student dashboard shows **group-level data only** — no individual names
- Instructor dashboard shows everything including AI flags
- Both dashboards read the same CSV files
- The qualitative assessment is only shown on the instructor dashboard
- Week nav buttons auto-disable for weeks without data
