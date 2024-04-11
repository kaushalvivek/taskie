'''
This is the main file that drives execution for the project manager, across it's various tasks.
Tasks today include:
1. Collect, and summarise project updates from the team, in a report.
'''

from tasks.report import Reporter

reporter = Reporter()

# Trigger the report generation
reporter.trigger_report()