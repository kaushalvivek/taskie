import os
import requests
import sys
sys.path.append(os.environ['PROJECT_PATH'])
from models.linear import Project


LINEAR_API_URL = "https://api.linear.app/graphql"

class LinearClient:
    def __init__(self):
        self.api_key = os.getenv('LINEAR_API_KEY')
        pass

    def _query(self, query):
        headers = {'Authorization': self.api_key}
        response = requests.post(LINEAR_API_URL, json={'query': query}, headers=headers)
        return response.json()

    def fetch_projects(self):
        query = '''
            query {
                projects {
                    nodes {
                        id
                        name
                        description
                        state
                        targetDate
                        projectUpdates {
                            nodes {
                                id
                                createdAt
                                body
                                url
                                user {
                                    name
                                    id
                                    email
                                }
                            }
                        
                        }
                    }
                }
            }
        '''
        json_response = self._query(query).json()
        json_projects = json_response['data']['projects']['nodes']
        projects = [Project(**project) for project in json_projects]
        return projects