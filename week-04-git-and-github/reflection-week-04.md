# Reflection – Week 04

**Author: Eze Favour**

---

## 1. Biggest Technical Insight I Got This Week

Git is not just a save button — it's a time machine with safety rails. Learning to stage selectively, write meaningful commit messages, branch for features, and merge cleanly changed how I think about version control. The pre-commit hook was particularly eye-opening: a fixed rule that blocks dangerous patterns (secrets, oversized files) before they ever reach the repository. Decades before AI, Git already had the same safety-gate idea that Claude Code hooks implement today.

## 2. Biggest Insight I Got About Myself This Week

I tend to commit too broadly — staging everything at once instead of making focused, atomic commits. The assignment forced me to separate an "Initial UI scaffold" commit from an "Update homepage content" commit, and I saw immediately why this matters: when you need to roll back one change without losing another, atomic commits save you.

## 3. My Biggest Challenge

The open-source collaboration workflow (fork → clone → remote → branch → commit → sync → push → PR) has a lot of moving parts. Configuring remotes correctly and understanding the difference between `origin` and `upstream` took several attempts before it felt natural. I also had to be careful not to open a PR against the shared upstream repo by mistake.

## 4. One System I Will Implement From This Week

Before every commit, I will run `git diff --staged` to review exactly what I'm about to commit. Before every push, I will check `git log --oneline` to make sure my commit history tells a clear story. These two habits cost 30 seconds and prevent hours of cleanup.

## 5. Key Takeaways

- Fixed-rule pre-commit hooks catch what they're programmed to catch — every time, without fail.
- AI-assisted review (like `/pr-ready`) catches nuanced issues a fixed rule can't anticipate: mixed changes, missing context, unclear intent.
- Together they provide defense in depth: the hook prevents obvious mistakes, the AI catches subtle ones.
- The Agentic Loop (Gather → Analyze → Human Act → Verify) applies everywhere — not just to AI, but to Git workflows too.
- The human must always stay in the loop. AI suggests, humans decide and act.

## 6. My Week 04 Highlight

Building a real pre-commit hook that blocks commits containing secrets and oversized files, then pairing it with a `/pr-ready` Claude skill that drafts PR descriptions — and proving both work end-to-end. This wasn't theory. It was a genuine safety net I can use in every project going forward.
