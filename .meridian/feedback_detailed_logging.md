---
name: feedback_detailed_logging
description: User values detailed logging for inventory management, problem identification, and planning
type: feedback
---

Keep careful, detailed, and clear logs at all times.

**Why:** User relies on logs for inventory management, identifying problems, and planning improvements. The existing per-step pipeline logging (probe, extract, model_load, transcribe with PERF metrics, RAM/CPU tracking) is the standard to maintain.

**How to apply:** When adding new features or modifying existing ones, always include structured log output with timing, resource usage, and contextual identifiers (task_id, step name). Never remove or reduce logging detail. Use the existing `TASK_EVENT`, `STEP`, `PERF` log patterns as templates.
