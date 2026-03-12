#!/bin/bash
# Sets up daily smoke test cron job
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_JOB="0 3 * * * cd $SCRIPT_DIR/.. && python3 check_interface.py >> /var/log/sg-smoke.log 2>&1"
(crontab -l 2>/dev/null | grep -v "check_interface.py"; echo "$CRON_JOB") | crontab -
echo "Cron job installed: $CRON_JOB"
