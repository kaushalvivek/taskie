import sys
import os
import logging
sys.path.append(os.environ['PROJECT_PATH'])
from tasks.report import Reporter

def send_reminder():
    # This is a placeholder for the actual reminder sending logic
    print("Reminder sent.")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

reporter = Reporter(logger=logger)

if len(sys.argv) > 1:
    if sys.argv[1] == "trigger-report":
        reporter.trigger_report()
    elif sys.argv[1] == "send-reminder":
        reporter.send_reminder()
    else:
        print("Invalid argument. Please use 'trigger-report' or 'send-reminder'.")
else:
    print("No argument provided. Please specify 'trigger-report' or 'send-reminder'.")
