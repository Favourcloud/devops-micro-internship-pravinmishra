# How to Fork & Submit Your Assignments

## What You're Looking At

This is the **official DevOps Micro Internship repository** by Pravin Mishra.

**Week 0** is submitted via Google Form (selection assignment — before you join the program).

**From Week 1 onwards**, all assignments are submitted via GitHub. You create your own personal copy of this repo — called a **fork** — and work there. Your fork is yours. Every assignment you submit lives in your fork.

---

## Step 1 — Fork This Repo

1. Make sure you are logged into your GitHub account
2. Go to: https://github.com/pravinmishraaws/devops-micro-internship-pravinmishra
3. Click the **Fork** button at the top-right
4. Under "Owner", select **your GitHub username**
5. Keep the repo name as `devops-micro-internship-pravinmishra`
6. Click **Create fork**

You now have your own copy at:
```
https://github.com/YOUR-USERNAME/devops-micro-internship-pravinmishra
```

---

## Step 2 — Clone It to Your Computer

Open your terminal and run:

```bash
git clone https://github.com/YOUR-USERNAME/devops-micro-internship-pravinmishra
cd devops-micro-internship-pravinmishra
```

---

## Step 3 — Fill In Your Details

Open `README.md` and update the **About Me** section with your:
- Name
- LinkedIn profile URL
- Location
- Background
- Goal

---

## Step 4 — Complete Your Weekly Assignment

1. Open the folder for the current week (e.g. `week-03-linux-and-bash-for-devops/`)
2. Open each `assignment-XX-*.md` file inside that folder (e.g. `assignment-01-....md`)
3. Fill in your answers where you see "Add your screenshot here" and other placeholder text
4. Add your screenshots to the `screenshots/` folder inside that week
5. Update the progress table in the main `README.md`:
   - Change ⬜ to 🔄 when you start
   - Change 🔄 to ✅ when you finish
   - Paste your public LinkedIn `/posts/` URL in the LinkedIn Post column
   - Paste your published blog URL in the Blog Post column; check its length and personal badge link below

> **Week 02 only:** `week-02-agentic-ai/assignment-briefs/` holds the detailed assignment briefs (scenario, objective, learning outcomes) and `week-02-agentic-ai/assignment-solutions/` holds a fully worked example for reference — your own answers still go in the `assignment-XX-*.md` files in the week folder root.

---

### Rubric Checks Before Submission

The [published grading rules](https://dmi.pravinmishra.com/how-it-works.html), checked on 15 September 2026, require:

- **Assignment files:** keep the exact expected folder and filename. Submit genuine, original answers with at least 50 words after code blocks, HTML comments, headings and table formatting are stripped. Untouched templates, copied answer keys and template placeholder text fail. Do not delete placeholders from unfinished work just to satisfy an automated check.
- **LinkedIn:** put each week's public post URL in the root README's **Weekly Progress** table. It must begin with `https://www.linkedin.com/posts/`; a profile, shortened URL or `/feed/update/` URL is not the accepted form. Obtain the real canonical URL from the published post rather than inventing a slug. A link elsewhere in an assignment is not enough.
- **Blog:** put the publicly accessible article URL in the same table. The article must contain at least 200 words and an actual clickable link to **your own** badge page. A relative reflection-file path, a mention of DMI or a link to a different DMI page does not satisfy the missing public-article/personal-credit requirements.
- **Evidence:** preserve real results and unfinished tasks. Passing the automated writing checks does not establish technical correctness. Every submitted screenshot must still meet the name/username rule below.
- **Attendance:** only the instructor's attendance record controls those points; GitHub changes cannot correct them.

### Personal Blog Credit Footer

For this fork, add this footer to the **published article itself** where it is missing:

> This post is part of my DevOps Micro Internship with Agentic AI — Cohort 3, led by Pravin Mishra. [Follow my graded progress](https://dmi.pravinmishra.com/s/Favourcloud.html).

In Medium, use the editor's link control to link “Follow my graded progress” to `https://dmi.pravinmishra.com/s/Favourcloud.html`. Confirm that the published text opens that exact page; pasting Markdown as literal text is not sufficient. Keep the original mentor/community credit required by the assignment. Learners using another fork must use their own username, not `Favourcloud`.

As of 15 September, the published Week 01, Week 04 and Week 05 articles linked in this fork's README still need this footer. The Week 03 article already contains the correct link. A local Markdown edit does not update Medium.

---

## Step 5 — Push Your Changes

```bash
git add .
git commit -m "Week 03 - Linux for DevOps assignment"
git push
```

If you work on a feature branch, review and merge the submission into your fork's graded default branch (`main` in this fork). Pushing only the feature branch does not update the default-branch submission. Do not overwrite `main` or merge unrelated work just to trigger grading.

The dashboard reports the date of its last review run, not live local changes. After the reviewed changes reach the graded branch, wait for the next instructor review; a successful push alone is not proof of updated points.

---

## Step 6 — Submit

Paste your **forked repo URL** into the Google Form submission link shared in the Discord / live session.

```
https://github.com/YOUR-USERNAME/devops-micro-internship-pravinmishra
```

---

## How to Sync Updates from the Original Repo

When Pravin updates this repo (new weeks, corrections, new content), you can pull those updates into your fork:

```bash
# Do this once to link the original repo
git remote add upstream https://github.com/pravinmishraaws/devops-micro-internship-pravinmishra

# Each time you want to sync
git fetch upstream
git merge upstream/main
git push
```

---

## What Your Repo Looks Like vs. The Original

| | **Pravin's Repo (this one)** | **Your Fork** |
|---|---|---|
| README.md | Placeholder — "Your Name" | Filled with your real details |
| Week folders | Empty templates | Your actual answers + screenshots |
| Progress table | All ⬜ Not Started | Updates as you complete weeks |
| Achievements | Empty | Your Champion badges & rank |
| Stack badges | All commented out | Uncommented as you earn them |

---

## Rules

- Every screenshot must show **your name or username** — no copying from others
- Each week's LinkedIn post must include the credit line (see each week's assignment-*.md files)
- Submit before the deadline shared in the live session

---

> Questions? Ask in the Discord: https://discord.pravinmishra.com?utm_source=github&utm_medium=readme
