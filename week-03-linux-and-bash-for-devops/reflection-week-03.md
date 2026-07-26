# Reflection – Week 03

**Author: Eze Favour**

---

## 1. Biggest Technical Insight I Got This Week

Deploying an application is only the beginning. Once it goes live, the real work starts — someone has to make sure it's healthy, available, secure, and running exactly as users expect. This week I got to experience what that responsibility feels like. The Production Maintenance Drill taught me that DevOps isn't about writing more code — it's about thinking like the person responsible for keeping a production application running.

## 2. Biggest Insight I Got About Myself This Week

When something breaks, I don't panic — I investigate. During the Nginx configuration failure simulation, I stayed calm, checked the logs, ran `nginx -t`, found the syntax error, fixed it, and verified recovery. This is exactly the muscle I built across a decade in customer operations: stay calm, find the fault, fix it, document it.

## 3. My Biggest Challenge

The bash scripting automation drill stretched me. Creating scripts that check scores, handle conditions, and produce meaningful output required thinking in logic flows rather than just running commands. Getting the counter script to work correctly with file persistence took several attempts before it clicked.

## 4. One System I Will Implement From This Week

Always run `nginx -t` before reloading Nginx. Always verify with `curl -I` after deployment. Always check logs before assuming you know what's wrong. These three habits are now non-negotiable in my workflow — they're small actions that prevent big incidents.

## 5. Key Takeaways

- `systemctl`, `ss`, `journalctl`, `tail`, `grep` are the diagnostic tools that separate a DevOps engineer from someone who just deploys code.
- SSH key-based authentication is not optional — it's the baseline for production security.
- Every open port is a potential attack vector. Only expose what's necessary.
- A rollback plan isn't paranoia — it's professionalism.
- Cloud resources cost money. Stop or terminate them when you're done.

## 6. My Week 03 Highlight

The highlight was simulating a real Nginx configuration failure and recovering it. Breaking something on purpose, watching it fail, then methodically fixing it gave me confidence that I can handle production incidents. It's one thing to read about troubleshooting — it's another to do it.
