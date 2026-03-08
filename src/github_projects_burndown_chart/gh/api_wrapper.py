import logging
import os
import requests
from datetime import date
import hashlib
import json
import tempfile

from config import config, secrets
from .project import Project, ProjectV1, ProjectV2
from .queries import OrganizationProject, OrganizationProjectV2, RepositoryProject, RepositoryProjectV2

# Set up logging
__logger = logging.getLogger(__name__)
__ch = logging.StreamHandler()
__ch.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
__logger.addHandler(__ch)


__project_v2_queries = {
    'repository': RepositoryProjectV2,
    'organization': OrganizationProjectV2,
}


def get_repository_project() -> Project:
    query_variables = config['query_variables']
    query_response = gh_api_query(RepositoryProject, query_variables)
    project_data = query_response['data']['repository']['project']
    if not project_data:
        __logger.critical(
            'GitHub did not return a Repository Project (v1) for the configured repo/project number.')
        __logger.critical(
            'If this is a GitHub Projects v2 board, set `settings.version` to `2` in config.json.')
        exit(1)
    return ProjectV1(project_data)


def get_organization_project() -> Project:
    query_variables = config['query_variables']
    query_response = gh_api_query(OrganizationProject, query_variables)
    project_data = query_response['data']['organization']['project']
    if not project_data:
        __logger.critical(
            'GitHub did not return an Organization Project (v1) for the configured org/project number.')
        __logger.critical(
            'If this is a GitHub Projects v2 board, set `settings.version` to `2` in config.json.')
        exit(1)
    return ProjectV1(project_data)


def get_project_v2(project_type) -> Project:
    query = __project_v2_queries[project_type]
    query_variables = config['query_variables'].copy()
    query_response = gh_api_query(query, query_variables)
    project_data = query_response['data'][project_type]['projectV2']
    if not project_data:
        __logger.critical(
            f"GitHub did not return a {project_type} Project v2 for the configured project_number.")
        __logger.critical(
            'Check `query_variables` in config.json (organization_name/repo_name and project_number).')
        exit(1)
    page_info = project_data['items']['pageInfo']
    while page_info['hasNextPage']:
        query_variables['cursor'] = page_info['endCursor']
        query_response = gh_api_query(query, query_variables)
        items = query_response['data'][project_type]['projectV2']['items']
        project_data['items']['nodes'].extend(items['nodes'])
        page_info = items['pageInfo']

    return ProjectV2(project_data)


def gh_api_query(query: str, variables: dict) -> dict:
    response = __get_from_cache(query, variables)
    if not response:
        response = __get_from_api(query, variables)
        __cache_response(query, variables, response)
    return response


def prepare_payload(query, variables):
    return {'query': query, 'variables': variables}


def __get_from_api(query, variables):
    headers = {'Authorization': 'bearer %s' % secrets['github_token']} \
        if 'github_token' in secrets else {}

    response = requests.post(
        'https://api.github.com/graphql',
        headers=headers,
        json=prepare_payload(query, variables)).json()

    # Gracefully report failures due to bad credentials
    if response.get('message') and response['message'] == 'Bad credentials':
        __logger.critical(response['message'])
        __logger.critical('Failed to extract project data from GitHub due '
                          'to an invalid access token.')
        __logger.critical('Please set the `github_token` key in the '
                          '`src/secrets.json` file to a valid access token with access '
                          'to the repo specified in the `src/config.json` file.')
        exit(1)
    # Gracefully report failures due to errors
    elif response.get('errors'):
        __logger.critical('Failed to extract project data from GitHub due to '
                          'an error.')
        __logger.critical(response['errors'])
        exit(1)
    return response


def __get_from_cache(query, variables):
    temp_path = __temp_path(query, variables)
    if os.path.exists(temp_path):
        with open(temp_path, 'r') as f:
            return json.load(f)
    return None


def __cache_response(query, variables, response):
    temp_path = __temp_path(query, variables)
    with open(temp_path, 'w') as f:
        json.dump(response, f)


def __temp_path(query, variables):
    temp_dir = tempfile.gettempdir()
    payload = prepare_payload(query, variables)
    payload.update({'today': str(date.today())})
    filename = f"{hashlib.sha256(json.dumps(payload).encode('utf-8')).hexdigest()}.json"
    temp_path = os.path.join(temp_dir, filename)
    return temp_path
