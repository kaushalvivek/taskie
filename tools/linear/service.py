import os
import requests
import sys
from typing import List
sys.path.append(os.environ['PROJECT_PATH'])
from models.linear import Project
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