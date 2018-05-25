#!/usr/bin/env python

import os
import re

from jenkinsapi.jenkins import Jenkins
from slacker import Slacker


jenkins_url = os.getenv('JENKINS_URL')
jenkins_username = os.getenv('JENKINS_USERNAME')
jenkins_token = os.getenv('JENKINS_TOKEN')
server = Jenkins(jenkins_url, username=jenkins_username, password=jenkins_token)

slack_token = os.getenv('SLACK_TOKEN')
slack_channel = os.getenv('SLACK_CHANNEL')
slack = Slacker(slack_token)


def get_change_in_test_results(job_name):
    job = server.get_job(job_name)
    build_ids = sorted([id for id in job.get_build_ids()], reverse=True)

    failure_history = []
    for id in build_ids:
        build = job.get_build(id)
        matrix_runs = build.get_matrix_runs()
        for run in matrix_runs:
            desc = run.get_description()
            if desc and 'rhel-7.4-x86_64 / stable-2.5' in desc:
                res = re.search("\((.*) failed (.*) error\)", desc)
                if res and len(failure_history) < 2:
                    total_failures = int(res.group(1)) + int(res.group(2))
                    failure_history.append(total_failures)
        if len(failure_history) == 2:
            break

    return failure_history[0] - failure_history[1] 


def post_slack_msg(text):
    slack.chat.post_message(slack_channel, text, icon_emoji=':ansible:')
   

def create_test_update(job_name):
    change = get_change_in_test_results(job_name)
    emoji_map = {20: ':tornado:',
                 15: ':thunder_cloud_and_rain:',
                 10: ':rain_cloud:',
                 5: ':cloud:',
                 0: ':barely_sunny:',
                 -5: ':mostly_sunny:',
                 -10: ':sunrise_over_mountains:',
                 -15: ':sunrise:'}
    emoji = ':tornado:'
    for level in sorted(emoji_map.keys()):
        if change <= level:
            emoji = emoji_map[level]
            break
    
    if change > 0:
        compare_term = 'more '
    elif change == 0:
        compare_term = ''
    else:
        compare_term = 'fewer '
        change = -change

    post_slack_msg('{0} has {1} {2}failures {3}'.format(job_name, change, compare_term, emoji))


if __name__ == '__main__':
    create_test_update('Test_Tower_Integration')
