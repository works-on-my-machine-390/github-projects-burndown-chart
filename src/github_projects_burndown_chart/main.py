import argparse
from datetime import timedelta

from chart.burndown import *
from config import config
from discord import webhook
from gh.api_wrapper import get_organization_project, get_repository_project, get_project_v2
from gh.project import Project
from util import calculators, colors
from util.stats import *
from util.calculators import *


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description='Generate a burndown chart for a GitHub project.')
    parser.add_argument("project_type", choices=['repository', 'organization'],
                        help="The type of project to generate a burndown chart for. Can be either 'organization' or 'repository'.")
    parser.add_argument("project_name",
                        help="The name of the project as it appears in the config.json")
    parser.add_argument("--filepath",
                        help="The filepath where the burndown chart is saved.")
    parser.add_argument("--discord", action='store_true',
                        help="If present, posts the burndown chart to the configured webhook")
    return parser.parse_args()


def download_project_data(project_type: str, project_version: int) -> Project:
    project = None
    if project_version == 2:
        project = get_project_v2(project_type)

    if project_type == 'repository':
        project = project or get_repository_project()
    elif project_type == 'organization':
        project = project or get_organization_project()

    milestone_title = config.sprint_milestone_title()
    if milestone_title:
        project.filter_cards_by_milestone(milestone_title)

    for issue_type in config.excluded_issue_types():
        project.exclude_cards_by_issue_type(issue_type)

    return project


def prepare_chart_data(stats: ProjectStats):
    color = colors()
    sprint_name = config.sprint_milestone_title() or stats.project.name
    data = BurndownChartData(
        sprint_name=sprint_name,
        utc_chart_start=config.utc_sprint_start(),
        utc_chart_end=config.utc_chart_end() or config.utc_sprint_end(),
        utc_sprint_start=config.utc_sprint_start(),
        utc_sprint_end=config.utc_sprint_end(),
        total_points=stats.total_points,
        series=[
            BurndownChartDataSeries(
                name=pts_type,
                data=stats.remaining_points_by_date(
                    calculators(stats.project)[pts_type]),
                format=dict(color=next(color))
            ) for pts_type in config['settings'].get('calculators', ['closed'])
        ],
        points_label=f"Outstanding {'Points' if config['settings']['points_label'] else 'Issues'}"
    )
    return data


if __name__ == '__main__':
    args = parse_cli_args()
    config.set_project(args.project_type, args.project_name)
    project = download_project_data(args.project_type, config['settings'].get('version', 1))
    stats = ProjectStats(project, config.utc_sprint_start(),
                         config.utc_chart_end() or config.utc_sprint_end())
    # Generate the burndown chart
    burndown_chart = BurndownChart(prepare_chart_data(stats))
    if args.discord:
        chart_path = "./tmp/chart.png"
        burndown_chart.generate_chart(chart_path)
        webhook.post_burndown_chart(chart_path)
    elif args.filepath:
        burndown_chart.generate_chart(args.filepath)
    else:
        burndown_chart.render()

    sprint_end_cutoff = config.utc_sprint_end() + timedelta(hours=23, minutes=59)
    unclosed_issues = project.unclosed_issues_as_of(sprint_end_cutoff)
    print(f"Unclosed issues by sprint end ({str(config.utc_sprint_end())[:10]}):")
    if not unclosed_issues:
        print("- None")
    for issue in unclosed_issues:
        assignees = ', '.join(issue.assignees) if issue.assignees else 'Unassigned'
        print(f"- #{issue.number} | {issue.title} | {assignees}")

    print('Done')
