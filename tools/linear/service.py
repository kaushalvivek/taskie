import os
import requests
import sys
from typing import List
from rich import print as rprint 
sys.path.append(os.environ['PROJECT_PATH'])
from models.linear import Project, Ticket, TicketState, Team
import json


LINEAR_API_URL = "https://api.linear.app/graphql"

class LinearClient:
    def __init__(self):
        self.api_key = os.getenv('LINEAR_API_KEY')

    def _query(self, query, variables) -> dict:
        headers = {'Authorization': self.api_key}
        response = requests.post(LINEAR_API_URL, json={'query': query, 'variables': variables}, headers=headers)
        return response.json()

    def get_project_by_id(self, id) -> Project:
        query = '''
            query($id: String!) {
                project(id: $id) {
                    id
                    name
                    description
                    state
                    targetDate
                    progress
                    url
                    teams {
                        nodes {
                            id
                            name
                        }
                    }
                    projectUpdates {
                        nodes {
                            id
                            createdAt
                            body
                            url
                            diffMarkdown
                            user {
                                name
                                id
                                email
                            }
                        }
                    }
                    projectMilestones {
                        nodes {
                            id
                            name
                            description
                            targetDate
                            createdAt
                        }
                    }
                    lead {
                        name
                        id
                        email
                    }
                }
            }
        '''
        variables = {'id': id}
        json_response = self._query(query, variables)
        json_project = json_response['data']['project']
        return Project(**json_project)

    def list_projects(self) -> List[Project]:
        query = '''
            query($after: String, $first: Int) {
                projects(after: $after, first: $first) {
                    nodes {
                        id
                        name
                        description
                        state
                        targetDate
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        '''
        projects = []
        has_next_page = True
        cursor = None
        while has_next_page:
            variables = {'after': cursor, 'first': 10} if cursor else {}
            json_response = self._query(query, variables)
            json_projects = json_response['data']['projects']['nodes']
            projects += [Project(**project) for project in json_projects]
            has_next_page = json_response['data']['projects']['pageInfo']['hasNextPage']
            cursor = json_response['data']['projects']['pageInfo']['endCursor']
        return projects
    
    def list_teams(self) -> list[Team]:
        query = """
            query {
                teams {
                    nodes {
                        id
                        name
                    }
                }
            }
            """
        json_response = self._query(query, {})
        response = json_response['data']['teams']['nodes']
        teams = [Team(**team) for team in response]
        return teams
    
    def list_states_for_team(self, team: Team) -> list[TicketState]:
        query = """
            query ($filter: WorkflowStateFilter!){
                workflowStates(filter: $filter) {
                    nodes {
                        id
                        name
                        team {
                            id
                            name
                        }
                    }
                }
            }
            """
        variables = {
            "filter": {
                "team": {
                    "id": {
                        'eq': team.id
                    }
                }
            }
        }
        json_response = self._query(query, variables)
        states = json_response['data']['workflowStates']['nodes']
        ticket_states = [TicketState(**state) for state in states]
        team_states = [state for state in ticket_states if state.team.id == team.id]
        return team_states
    
    def create_ticket(self, ticket: Ticket):
        query = '''
            mutation($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    issue {
                        id
                        title
                        description
                        state {
                            name
                        }
                        priority
                        labelIds
                        team {
                            id
                        }
                    }
                }
            }
        '''
        variables = {
            'input': {
                'id': ticket.id,
                'title': ticket.title,
                'description': ticket.description,
                'priority': ticket.priority,
                # 'labelIds': ['bug'],
                'stateId': ticket.state.id,
                'teamId': ticket.team.id
            }
        }
        return self._query(query, variables)
    
    def attach_slack_message_to_ticket(self, ticket: Ticket):
        query = '''
            mutation($issueId: String!, $url: String!) {
                attachmentLinkSlack(issueId: $issueId, url: $url) {
                    success
                }
            }
        '''
        variables = {
            'issueId': ticket.id,
            'url': ticket.slack_message_url,
        }
        return self._query(query, variables)
        
