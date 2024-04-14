'''
The reporter service is responsible for generating the project report.
'''
import sys
import os
from typing import List
from tqdm import tqdm
sys.path.append(os.environ['PROJECT_PATH'])
from tools.linear.service import LinearClient
from models.linear import ProjectState, Project
from models.report import Reminder, Report
from tools.decider import Decider

class Reporter:
    def __init__(self):
        self.linear = LinearClient()
        self.decider = Decider()
    
    def trigger_report(self):
        self._generate_report()

    def _get_project_with_best_update(self, projects: List[Project]) -> Project:
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
        return projects[best_project_index]

    def _get_reminders(self, projects: List[Project]) -> List[Reminder]:
        user_reminders = {}
        for project in projects:
            if project.lead.id not in user_reminders:
                user_reminders[project.lead.id] = []
            user_reminders[project.lead.id].append(project)
        reminders = []
        for _, projects in user_reminders.items():
            reminders.append(Reminder(user=projects[0].lead, projects=projects))
        return reminders

    def _generate_report(self) -> Report:
        current_projects = self._get_current_projects()
        projects_with_updates, projects_without_updates = [], []
        for project in current_projects:
            if project.project_updates and len(project.project_updates.nodes) > 0:
                projects_with_updates.append(project)
            else:
                projects_without_updates.append(project)
        best_updated_project = self._get_project_with_best_update(projects_with_updates)
        reminders = self._get_reminders(projects_without_updates)
        exec_summary = self._generate_exec_summary(projects_with_updates, projects_without_updates)
        return Report(reminders=reminders, best_updated_project=best_updated_project, exec_summary=exec_summary)

    def _get_current_projects(self) -> List[Project]:
        projects = self.linear.list_projects()
        projects = [project for project in projects if project.state in [ProjectState.PLANNED, ProjectState.STARTED]]
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
