"""
Weekly Influencer Update Scheduler

Options:
  1. Windows Task Scheduler (recommended):
     schtasks /create /tn "ETF_Influencer_Update" /tr "python C:\\Users\\c\\etf-marketing-qa\\backend\\influencer_updater.py" /sc weekly /d MON /st 09:00

  2. Run this script as a daemon:
     python weekly_scheduler.py

  3. Cron (Linux/Mac):
     0 9 * * 1 cd /path/to/backend && python influencer_updater.py
"""

import time
import datetime
import schedule
from influencer_updater import update_all


def job():
    print(f"\n{'='*60}")
    print(f"Scheduled Update: {datetime.datetime.now()}")
    print(f"{'='*60}")
    update_all()


# Run every Monday at 9:00 AM
schedule.every().monday.at("09:00").do(job)

print("=== ETF Influencer Weekly Scheduler ===")
print("Scheduled: Every Monday at 09:00")
print("Press Ctrl+C to stop\n")

# Run immediately on first start
job()

while True:
    schedule.run_pending()
    time.sleep(60)
