'''
The reporter service is responsible for generating the project report.
'''
import sys
import os
import logging
import yaml
import redis
from datetime import datetime, timedelta
from typing import List
from tqdm import tqdm
sys.path.append(os.environ['PROJECT_PATH'])
from tools.linear import LinearClient
from tools.slack import SlackClient
from models.linear import ProjectStates, Project, ProjectStatus
from models.report import Reminder, Config, Report, RiskUpdate, ReminderType
from tools.decider import Decider
from tools.writer import Writer

PROJECT_UPDATE_CUTOFF_DAYS = 4

class Reporter:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.linear = LinearClient(logger)
        self.decider = Decider(logger=logger, model="gpt-4-turbo")
        with open(f"{os.environ['PROJECT_PATH']}/config/report.yaml", 'r') as file:
            config_data = yaml.safe_load(file)
        self.config = Config(**config_data)
        self.writer = Writer(logger=logger, model="gpt-4-turbo")
        self.slack = SlackClient(logger=logger)
        self.cache = redis.Redis()

    def send_reminder(self, type: ReminderType):
        current_projects = self._get_current_projects()
        reminders = self._get_reminders(current_projects)
        if type == ReminderType.UPDATE:
            reminder_block = self._get_reminder_block(reminders=reminders, intro="Hey team! A gentle reminder to the following folks to add a project update before EOD:")
        if type == ReminderType.PLANNING:
            reminder_block = self._get_reminder_block(reminders=reminders, intro="Hey team! A gentle reminder to the following folks to update/add new project milestones today, for next sprint's planning:")
        self.slack.post_message(blocks=[reminder_block], channel_id=self.config.reporting_channel_id)
               
    def trigger_report(self):
        report = None
        report = self._generate_report()
        self.logger.debug(f"Report: {report}")
        slack_message_blocks = self._write_slack_message(report)
        self.slack.post_message(blocks=slack_message_blocks, channel_id=self.config.reporting_channel_id)
        self.logger.info(f"Report sent to {self.config.reporting_channel_id}")
        return

    def _get_best_update(self, projects: List[Project]) -> Project:
        # ignore all projects by admin, if admin is populated
        if self.config.admin_user_email:
            projects = [project for project in projects if project.lead.email != self.config.admin_user_email]
        self.logger.info(f"Getting project with best update for {len(projects)} projects")
        context = "Project leads for different projects have provided an update on the status and progress of \
the respective projects they are leading. Your goal is to identify the project with the best update so that we can \
highlight it in the report and share it with the team."
        criteria = [
            "Update clearly articulates the progress and decisions made so far",
            "Update flags risks, if any, to the set timelines and provides a clear path forward",
            "Update reflects on misses, if any, and how they were addressed",
        ]
        options = []
        for project in projects:
                latest_update = project.project_updates.nodes[0]
                options.append(f"{project.name} - {latest_update.body}")
        best_project_index, chain_of_thought = self.decider.get_best_option(context, options, criteria, with_chain_of_thought=True)
        
        self.logger.info(f"Best updated project: {projects[best_project_index].name}")
        self.logger.debug(projects[best_project_index].model_dump_json())
        
        return projects[best_project_index]

    def _get_reminders(self, projects: List[Project]) -> List[Reminder]:
        self.logger.info(f"Generating reminders for {len(projects)} projects")
        user_reminders = {}
        for project in projects:
            if project.lead.id not in user_reminders:
                user_reminders[project.lead.id] = []
            user_reminders[project.lead.id].append(project)
        reminders = []
        for _, projects in user_reminders.items():
            reminders.append(Reminder(user=projects[0].lead, projects=projects))
        self.logger.info(f"Generated {len(reminders)} reminders")
        self.logger.debug(reminders)
        return reminders

    def _get_reminder_block(self, reminders: List[Reminder], intro:str):
        reminders_text = "\n".join([f"- *{self.slack.get_tag_for_user(reminder.user.email,self.config.email)}*: {', '.join([project.name for project in reminder.projects])}." for reminder in reminders])
        block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{intro}\n\n{reminders_text}"
                }
            }
        return block

    def _write_slack_message(self, report: Report):
        
        message_blocks = []
        
        message_blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Project Report",
                "emoji": True
            }
        })
        
        message_blocks.append({"type": "divider"})
        
        # Introduction Section
        message_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"👋 Hi @here, out of <{self.config.roadmap_view_url}|{len(report.projects_with_updates) + len(report.projects_without_updates)} projects>, {len(report.projects_with_updates)} have an update from their leads and {len(report.projects_without_updates)} are missing an update."
            }
        })

        # Best Update Section
        if report.best_update:
            message_blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✨ Best Update",
                    "emoji": True
                }
            })
            message_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"The best update, according to GPT, is on *{report.best_update.name}*, added by *{self.slack.get_tag_for_user(report.best_update.lead.email, self.config.email)}*. 👏"
                }
            })
        
        if report.risks:
            message_blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "👀 Risks",
                    "emoji": True
                }
            })
            risks_text = "\n\n".join([f"*{risk.project_name}* ({risk.project_milestone}):\n- _why at risk?_: {risk.why}\n- _next steps_: {risk.what_next}" for risk in report.risks])
            message_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"There are {len(report.risks)} projects that are at risk. Here's a brief summary:\n\n{risks_text}"
                }
            })
        
        if report.reminders:
            message_blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔔 Reminders",
                    "emoji": True
                }
            })
            message_blocks.append(self._get_reminder_block(reminders=report.reminders,
                intro="The following projects are missing an update from their leads -- a gentle reminder to add one ASAP:"))
        return message_blocks

    def _get_project_risks(self, projects: List[Project]) -> List[RiskUpdate]:
        risky_projects = [project for project in projects if project.status is not ProjectStatus.ON_TRACK]
        self.logger.info(f"Getting risks for {len(risky_projects)} projects")
        
        project_risks = []
        
        for project in tqdm(risky_projects, desc="Processing risky projects"):
            risk_update = self.writer.parse(
                context='''Project leads have provided updates on projects that are off track, or at risk. Our goal is to write an excellent
executive summary of the risk with these projects and emphasize on the WHY by taking insights from the shared update. The output MUST
be in the provided output format.
''',
                input=f"{project.name} - {project.project_updates.nodes[0].body}",
                output_model=RiskUpdate
            )
            self.logger.debug(risk_update)
            risk_update.project_name = project.name
            project_risks.append(risk_update)
        return project_risks

    def _enrich_projects_with_status(self, projects: List[Project]) -> List[Project]:
        for idx, project in tqdm(enumerate(projects), desc="Updating project statuses"):
            status_idx = self.decider.get_best_option(
                context=f'''Project Leads have provided updates on the projects they are leading. Based on the provided updates, you have to figure out 
what's the best current status for the project. Here are the details about the project:
{project.model_dump_json()}''', 
                options=[status.value for status in ProjectStatus],
                criteria=[
                    "If the project lead explicitly mentions the project's status, then that's the obvious correct choice.",
                    "If the lead flags a risk, or a delay, in the project, then the status should be set accordingly.",
                    "Use the project's latest update to infer the status.",
                ])
            projects[idx].status = list(ProjectStatus)[status_idx] 
        return projects

    def _generate_report(self) -> Report:
        self.logger.info(f"Generating report ...")
        current_projects = self._get_current_projects()
        
        projects_with_updates, projects_without_updates = [], []
        for project in current_projects:
            if not project.project_updates or len(project.project_updates.nodes) == 0:
                projects_without_updates.append(project)
                continue
            
            created_at_timestamp = datetime.strptime(project.project_updates.nodes[0].created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            
            if project.project_updates and \
                len(project.project_updates.nodes) > 0 and \
                created_at_timestamp > datetime.now() - timedelta(days=PROJECT_UPDATE_CUTOFF_DAYS):
                projects_with_updates.append(project)
                
            else:
                projects_without_updates.append(project)
                
        self.logger.info(f"{len(projects_with_updates)} projects with updates, {len(projects_without_updates)} projects without updates")
        
        projects_with_updates = self._enrich_projects_with_status(projects_with_updates)

        return Report(
            reminders=self._get_reminders(projects_without_updates),
            best_update=self._get_best_update(projects_with_updates),
            risks=self._get_project_risks(projects_with_updates),
            projects_with_updates=projects_with_updates,
            projects_without_updates=projects_without_updates
        )

    def _get_current_projects(self) -> List[Project]:
        projects = self.linear.list_projects()
        projects = [project for project in projects if project.state in [ProjectStates.PLANNED, ProjectStates.STARTED]]
        current_projects = []
        for project in tqdm(projects):
            fetched_project = self.linear.get_project_by_id(project.id)
            for team in fetched_project.teams.nodes:
                if team.is_epd():
                    current_projects.append(fetched_project)
                    break
            
        return current_projects

