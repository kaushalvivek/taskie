import sys
import os
sys.path.append(os.environ['PROJECT_PATH'])
from tasks.report import Reporter

reporter = Reporter()

# Trigger the report generation
reporter.trigger_report()