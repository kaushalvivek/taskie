import sys
import os
import logging
sys.path.append(os.environ['PROJECT_PATH'])
from tasks.report import Reporter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

reporter = Reporter(logger=logger)
# Trigger the report generation
reporter.trigger_report_for_roadmap(roadmap_id=os.environ['ROADMAP_ID'])

