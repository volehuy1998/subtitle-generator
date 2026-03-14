# Postmortem: [Incident Title]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P0 / P1 / P2 / P3
**Impact:** [What was affected, how many users, which features]
**Author:** @username

## Summary

[1-2 sentence summary of the incident]

## Timeline (all times UTC)

| Time | Event |
|------|-------|
| HH:MM | [First signal / alert fired] |
| HH:MM | [Investigation started] |
| HH:MM | [Root cause identified] |
| HH:MM | [Mitigation applied] |
| HH:MM | [Service restored] |

## Root Cause

[Systemic cause, not individual blame. What condition or sequence of events led to the failure?]

## Detection

[How was the incident detected? Alert, user report, monitoring?]
[How long between the incident starting and detection?]

## Resolution

[What was done to fix the immediate issue?]
[Was it a rollback, config change, code fix, or manual intervention?]

## What Went Well

- [Detection was fast because...]
- [Monitoring caught the issue before users noticed...]
- [Runbook was accurate and helpful...]

## What Could Be Improved

- [Detection gap: no alert for X condition]
- [Runbook was missing step Y]
- [Communication delay of Z minutes]

## Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Preventive action] | @person | YYYY-MM-DD | TODO |
| [Detection improvement] | @person | YYYY-MM-DD | TODO |
| [Process improvement] | @person | YYYY-MM-DD | TODO |

## Lessons Learned

[Key takeaways for the team. What should we remember for next time?]

---

*This postmortem follows Google's blameless postmortem practice (SRE Book, Chapter 15).*
*"Everyone had good intentions and did the right thing with the information they had."*
