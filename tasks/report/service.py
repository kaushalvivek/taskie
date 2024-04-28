'''
The reporter service is responsible for generating the project report.
'''
import sys
import os
import logging
import yaml
from typing import List
from tqdm import tqdm
from rich import print as rprint
sys.path.append(os.environ['PROJECT_PATH'])
from tools.linear import LinearClient
from models.linear import ProjectStates, Project, ProjectStatus
from models.report import Reminder, Config
from tools.decider import Decider
from tools.writer import Writer

class Reporter:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.linear = LinearClient(logger)
        self.decider = Decider(logger=logger)
        with open(f"{os.environ['PROJECT_PATH']}/config/report.yaml", 'r') as file:
            config_data = yaml.safe_load(file)
        self.config = Config(**config_data)
        self.writer = Writer(logger=logger)
    
    def trigger_report(self):
        roadmap_id = self.config.roadmap_id
        report = self._generate_report(roadmap_id)
        self.logger.info(f"Report generated for roadmap: {roadmap_id}")
        self.logger.debug(f"Report: {report}")

    def _get_project_with_best_update(self, projects: List[Project]) -> Project:
        # ignore all projects by admin, if admin is populated
        if self.config.admin_user_email:
            projects = [project for project in projects if project.lead.email != self.config.admin_user_email]
        self.logger.info(f"Getting project with best update for {len(projects)} projects")
        context = "Project leads for different projects have provided an update on the status and progress of \
the respective projects they are leading. We want to identify the project with the best update so that we can \
highlight it in the report and share it with the team."
        criteria = [
            "Update clearly articulates the progress made",
            "Update provides a clear path forward",
            "Update reflects on misses, if any, and how they were addressed",
        ]
        options = []
        for project in projects:
                latest_update = project.project_updates.nodes[0]
                options.append(f"{project.name} - {latest_update.body}")
        best_project_index = self.decider.get_best_option(context, options, criteria)
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

    def _write_report(self, projects_with_updates: List[Project], projects_without_updates: List[Project], best_updated_project: Project) -> str:

        report = f'''Out of {len(projects_with_updates) + len(projects_without_updates)} projects, \
{len(projects_with_updates)} have an update from their leads and {len(projects_without_updates)} are missing an update from their leads.

👑 The best update, according to my infinite elephant wisdom, is on {best_updated_project.name}, added by {best_updated_project.lead.name}. 👑
'''
        risky_projects = [project for project in projects_with_updates if project.status is not ProjectStatus.ON_TRACK]
        if len(risky_projects) > 0:
            summarizer_input = "\n\n".join([f"{project.name} - {project.project_updates.nodes[0].body}" for project in risky_projects])
            risk_summary = self.writer.summarize(
                context='''Project leads have provided updates on projects that are off track, or at risk. Our goal is to write an excellent 
executive summary of the risk with these projects and emphasise on the WHY by taking insights from the shared update. The output MUST 
be in bullet points. Be VERY brief. ONLY includ the following bullet points for each project:
- (Project Name)
  - why not on track: (a VERY BRIEF reach here)
  - what next: (a VERY BRIEF summary of what the project lead has shared)
... and so on, for each project.
''',
                word_limit=50,
                input=summarizer_input
            )
            report += f"\n\nThere are some projects that are off track or at risk. Here is a brief summary:\n\n{risk_summary}"

        if len(projects_without_updates) > 0:

            reminders = self._get_reminders(projects_without_updates)

            reminder_text = f'''\n\nThere are {len(projects_without_updates)} projects that are missing an update from their leads. 
A gentle reminder to the following folks to add a project update ASAP:'''
            
            for reminder in reminders:
                reminder_text += f"\n\n{reminder.user.name}:"
                for project in reminder.projects:
                    reminder_text += f"\n - {project.name}"

            report += reminder_text

        return report

    def _generate_report(self, roadmap_id: str) -> str:
        self.logger.info(f"Generating report for roadmap: {roadmap_id}")
        roadmap_projects = self.linear.list_projects_in_roadmap(roadmap_id)
        
        for idx, project in tqdm(enumerate(roadmap_projects), desc="Pulling full projects"):
            roadmap_projects[idx] = self.linear.get_project_by_id(project.id)
        
        current_projects = []
        for project in roadmap_projects:
            if project.state in [ProjectStates.PLANNED, ProjectStates.STARTED]:
                current_projects.append(project)
        self.logger.info(f"{len(current_projects)} projects are in progress or planned")
        
        
        projects_with_updates, projects_without_updates = [], []
        for project in current_projects:
            if project.project_updates and len(project.project_updates.nodes) > 0:
                projects_with_updates.append(project)
            else:
                projects_without_updates.append(project)
        self.logger.info(f"{len(projects_with_updates)} projects with updates, {len(projects_without_updates)} projects without updates")
        
        if len(projects_with_updates) > 0:
            best_updated_project = self._get_project_with_best_update(projects_with_updates)
        else:
            self.logger.info(f"No projects with updates found")
            best_updated_project = None
        
        for idx, project in tqdm(enumerate(projects_with_updates), desc="Updating project statuses"):
            status_idx = self.decider.get_best_option(
                context=f'''Project Leads have provided updates on the projects they are leading. Based on the provided updates, you have to figure out 
what's the best current status for the project. Here are the details about the project:
{project.model_dump_json()}''', 
                options=[status.value for status in ProjectStatus],
                criteria=[
                    "If the project lead explicitly mentions the project's status, then that's the obvious correct choice.",
                    "If the project flags a risk or delay, in the project, then the status should be flagged accordingly.",
                    "Use the project's latest update to infer the status.",
                ]
                )
            projects_with_updates[idx].status = list(ProjectStatus)[status_idx]

        report = self._write_report(projects_with_updates, projects_without_updates, best_updated_project)
        self.logger.info(f"\n\nReport: {report}")
        return report

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
    
    def _send_report(self):
        raise NotImplementedError("Service not implemented yet")
