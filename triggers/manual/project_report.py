import sys
import os
import logging
sys.path.append(os.environ['PROJECT_PATH'])
from tasks.report import Reporter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

reporter = Reporter(logger=logger)
# Trigger the report generation
reporter.trigger_report()

