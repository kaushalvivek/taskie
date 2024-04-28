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
from models.report import Reminder, Report, Config
from tools.decider import Decider

class Reporter:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.linear = LinearClient(logger)
        self.decider = Decider(logger=logger)
        with open(f"{os.environ['PROJECT_PATH']}/config/report.yaml", 'r') as file:
            config_data = yaml.safe_load(file)
        self.config = Config(**config_data)
    
    def trigger_report(self):
        roadmap_id = self.config.roadmap_id
        report = self._generate_report(roadmap_id)
        self.logger.info(f"Report generated for roadmap: {roadmap_id}")
        self.logger.debug(f"Report: {report.model_dump_json()}")

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

    def _get_executive_summary(self, projects_with_updates: List[Project], projects_without_updates: List[Project]) -> str:
        self.logger.info(f"Generating executive summary")
        return f"Projects with updates: {len(projects_with_updates)},\
              Projects without updates: {len(projects_without_updates)}"

    def _generate_report(self, roadmap_id: str) -> Report:
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
        
        rprint(projects_with_updates)
        quit()
        
        reminders = self._get_reminders(projects_without_updates)

        exec_summary = self._get_executive_summary(projects_with_updates, projects_without_updates)
        return Report(reminders=reminders, best_updated_project=best_updated_project, exec_summary=exec_summary)

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
