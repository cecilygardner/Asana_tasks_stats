from __future__ import print_function, division
from datetime import date, datetime, timedelta

import argparse
import json

import dateutil.parser as date_parser
import numpy as np
import pytz


import asana


def gen_parser():
    now = pytz.utc.localize(datetime.utcnow())
    thirty_days_ago = now - timedelta(days=30)

    def parse_tz_aware_dt(dt_str):
        return pytz.utc.localize(date_parser.parse(dt_str))

    parser = argparse.ArgumentParser(
        description="Generate statistics for the facilities team.")
    parser.add_argument(
        '--start-date', type=parse_tz_aware_dt, default=thirty_days_ago,
        help='Start date for the date range to run the report on.')
    parser.add_argument(
        '--end-date', type=parse_tz_aware_dt, default=now,
        help='End date for the date range to run the report on.')
    return parser


def grab_all_tasks_in_project(asana_client, args.start_date, asana_config):
    task_params = {
        "project": 339123161478549,
        "completed_since": start_date.isoformat()
    }

    tasks = list(asana_client.tasks.find_all(
        params=task_params,
        fields=[
            'completed', 'created_at', 'completed_at', 'name', 'assignee']))

    tasks = [t for t in tasks if not t['name'].endswith(':')]

    return tasks


def find_and_print_tasks(tasks):
    incomplete_tasks = 0
    complete_tasks = 0

    for t in tasks:
        if t['completed']:
            complete_tasks += 1
        else:
            incomplete_tasks += 1

    percent_complete = (
        complete_tasks / (complete_tasks + incomplete_tasks)) * 100
    task_information = (
        "Completed tasks (last 30 days): {}\nIncomplete tasks in project: {}\n"
        "Percent of Tasks Complete (last 30 days): {:.0f}%\n").format(
            complete_tasks, incomplete_tasks, percent_complete)

    print("Calculating task information")
    print(task_information)
    return task_information


def days_data_for_tasks(tasks, asana_config, start_date, end_date):
    completed_tasks = [t for t in tasks if t['completed'] is True]
    completed_tasks = [
        t for t in completed_tasks if
        start_date <= date_parser.parse(t['completed_at']) < end_date
    ]

    task_durations = []

    for t in completed_tasks:
        created_date = date_parser.parse(t['created_at'])
        closed_date = date_parser.parse(t['completed_at'])
        days_to_close = (closed_date - created_date).days

        task_durations.append(days_to_close)

    print("Calculating stats")
    median = np.median(task_durations)
    std = np.std(task_durations)
    var = np.var(task_durations)
    mean = np.mean(task_durations)

    std_below = int(mean - (std))
    std_above = int(mean + (std))

    above_std_links = []
    below_std_links = []

    for t in completed_tasks:
        created_date = date_parser.parse(t['created_at'])
        closed_date = date_parser.parse(t['completed_at'])
        days_to_close = (closed_date - created_date).days
        if days_to_close > std_above:
            link = (
                "https://app.asana.com/0/{project_id}/{task_id}/ : {}".format(
                    days_to_close, project_id=[asana_config['project_id']],
                    task_id=t["id"]))
            above_std_links.append(link)
        elif 0 < days_to_close < std_below:
            link = (
                "https://app.asana.com/0/{project_id}/{task_id}/ : {}".format(
                    days_to_close, project_id=[asana_config['project_id']],
                    task_id=t["id"]))
            below_std_links.append(link)

    str_above_std_links = '\n'.join(above_std_links)
    str_below_std_links = '\n'.join(below_std_links)

    if len(str_above_std_links) < 1:
        str_above_std_links = "None"
    if len(str_below_std_links) < 1:
        str_below_std_links = "None"

    tasks_stats = (
        "\nStatistics:\nMean days: {}\nMedian days: {}\nStd: {}\nVar: {}\n\n"
        "1 std below the mean: {}\n1 std above the mean: {}\n\nThese tasks "
        "are affecting your average close time.\n\nThese tasks are at least "
        "1 std above the mean:\n{}\n\nThese tasks are at least 1 std below "
        "the mean:\n{}".format(
            mean, median, std, var, std_below, std_above, str_above_std_links,
            str_below_std_links))

    return tasks_stats




def read_config():
    with open('asana_config.json') as config_fobj:
        return json.load(config_fobj)


def post_all_in_asana_task(
        asana_client, asana_config, task_information, tasks_stats):
    todays_date_str = date.today().strftime("%m/%d/%Y")
    name = "Results {} - {}".format(todays_date_str, asana_config['name'])
    task_details = (task_information + tasks_stats)

    params = {
        "workspace": asana_config['workspace_id'], "projects": [asana_config['project_id']],
        "name": name, "notes": task_details}

    asana_client.tasks.create(params)


def main():
    parser = gen_parser()
    args = parser.parse_args()
    asana_config = read_config()
    asana_client = asana.Client.access_token(asana_config['personal_access_token'])
    tasks = grab_all_tasks_in_project(asana_client, args.start_date, asana_config)
    tasks_stats = days_data_for_tasks(tasks, args.start_date, args.end_date)
    task_information = find_and_print_tasks(tasks)
    room_list = read_room_list_from_json()
    post_all_in_asana_task(
        asana_client, task_information, tasks_stats)


if __name__ == "__main__":
    main()
