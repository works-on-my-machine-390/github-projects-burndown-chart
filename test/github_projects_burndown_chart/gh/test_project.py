import unittest
import os
import sys
import types
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'src', 'github_projects_burndown_chart')))

config_stub = types.ModuleType('config')


class _ConfigStub:
    def __getitem__(self, key: str):
        if key == 'settings':
            return {'points_label': 'Points: '}
        raise KeyError(key)


config_stub.config = _ConfigStub()
sys.modules['config'] = config_stub

from gh.project import Card, Column, Project


class ProjectStub(Project):
    def __init__(self, columns):
        self.columns = columns

class TestProject(unittest.TestCase):

    def test_card_parses_milestone_title(self):
        card = Card({
            'createdAt': '2026-02-09T00:00:00Z',
            'labels': {'nodes': [{'name': 'Points: 3'}]},
            'milestone': {'title': 'Sprint 1'}
        })
        self.assertEqual('Sprint 1', card.milestone_title)

    def test_project_filters_cards_by_milestone(self):
        sprint_1_card = Card({
            'createdAt': '2026-02-09T00:00:00Z',
            'labels': {'nodes': [{'name': 'Points: 2'}]},
            'milestone': {'title': 'Sprint 1'}
        })
        sprint_2_card = Card({
            'createdAt': '2026-02-10T00:00:00Z',
            'labels': {'nodes': [{'name': 'Points: 5'}]},
            'milestone': {'title': 'Sprint 2'}
        })
        project = ProjectStub([Column([sprint_1_card, sprint_2_card])])

        project.filter_cards_by_milestone('Sprint 2')

        self.assertEqual(1, len(project.cards))
        self.assertEqual('Sprint 2', project.cards[0].milestone_title)
        self.assertEqual(5, project.total_points)

    def test_project_filter_excludes_cards_without_milestone(self):
        unscoped_card = Card({
            'createdAt': '2026-02-09T00:00:00Z',
            'labels': {'nodes': [{'name': 'Points: 2'}]}
        })
        sprint_2_card = Card({
            'createdAt': '2026-02-10T00:00:00Z',
            'labels': {'nodes': [{'name': 'Points: 5'}]},
            'milestone': {'title': 'Sprint 2'}
        })
        project = ProjectStub([Column([unscoped_card, sprint_2_card])])

        project.filter_cards_by_milestone('Sprint 2')

        self.assertEqual(1, len(project.cards))
        self.assertEqual('Sprint 2', project.cards[0].milestone_title)

    def test_project_excludes_acceptance_testing_issue_type(self):
        acceptance_testing_card = Card({
            'createdAt': '2026-02-09T00:00:00Z',
            'labels': {'nodes': [{'name': 'Points: 2'}]},
            'issueType': {'name': 'Acceptance Testing'}
        })
        feature_card = Card({
            'createdAt': '2026-02-10T00:00:00Z',
            'labels': {'nodes': [{'name': 'Points: 5'}]},
            'issueType': {'name': 'Feature'}
        })
        project = ProjectStub([Column([acceptance_testing_card, feature_card])])

        project.exclude_cards_by_issue_type('Acceptance Testing')

        self.assertEqual(1, len(project.cards))
        self.assertEqual('Feature', project.cards[0].issue_type_name)
        self.assertEqual(5, project.total_points)

    def test_project_lists_unclosed_issues_as_of_date(self):
        closed_issue = Card({
            '__typename': 'Issue',
            'number': 11,
            'title': 'Done task',
            'createdAt': '2026-02-09T00:00:00Z',
            'closedAt': '2026-02-10T00:00:00Z',
            'labels': {'nodes': [{'name': 'Points: 1'}]}
        })
        unclosed_issue = Card({
            '__typename': 'Issue',
            'number': 12,
            'title': 'Open task',
            'createdAt': '2026-02-09T00:00:00Z',
            'labels': {'nodes': [{'name': 'Points: 1'}]},
            'assignees': {'nodes': [{'login': 'octocat'}]}
        })
        open_pull_request = Card({
            '__typename': 'PullRequest',
            'number': 20,
            'title': 'PR task',
            'createdAt': '2026-02-09T00:00:00Z',
            'labels': {'nodes': [{'name': 'Points: 1'}]}
        })
        project = ProjectStub([Column([closed_issue, unclosed_issue, open_pull_request])])

        results = project.unclosed_issues_as_of(datetime(2026, 2, 12, tzinfo=timezone.utc))

        self.assertEqual(1, len(results))
        self.assertEqual(12, results[0].number)
        self.assertEqual('Open task', results[0].title)
        self.assertEqual(['octocat'], results[0].assignees)