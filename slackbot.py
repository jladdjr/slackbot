#!/usr/bin/env python

from datetime import datetime
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

job_name = os.getenv('JOB_NAME')
matrix_job = os.getenv('MATRIX_JOB', False)
build_label = os.getenv('BUILD_LABEL')
test_result_pattern = os.getenv('TEST_RESULT_PATTERN')

show_button_owner = os.getenv('SHOW_BUTTON_OWNER')

def get_test_results():
    job = server.get_job(job_name)
    build_ids = sorted([id for id in job.get_build_ids()], reverse=True)

    failure_history = []
    for id in build_ids:
        build = job.get_build(id)
        if matrix_job:
            matrix_runs = build.get_matrix_runs()
            for run in matrix_runs:
                desc = run.get_description()
                if desc and build_label in desc:
                    res = re.search(test_result_pattern, desc)
                    if res and len(failure_history) < 2:
                        total_failures = int(res.group(1)) + int(res.group(2))
                        failure_history.append(total_failures)
        else:
            desc = build.get_description()
            if desc and build_label in desc:
                res = re.search(test_result_pattern, desc)
                if res and len(failure_history) < 2:
                    total_failures = int(res.group(1)) + int(res.group(2))
                    failure_history.append(total_failures)

        if len(failure_history) == 2:
            break

    return failure_history[0], (failure_history[0] - failure_history[1])


def post_slack_msg(text):
    slack.chat.post_message(slack_channel, text, icon_emoji=':ansible:')
   

def create_test_update():
    total_failures, change = get_test_results()
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
        description = '{0} has {1} more failures'.format(job_name, change)
    elif change == 0:
        description = '{0} has the same number of failures'.format(job_name)
    else:
        change = -change
        description = '{0} has {1} fewer failures'.format(job_name, change)

    day_of_the_week = datetime.today().weekday()
    button_owner_map = {0: '<@U0EKSNVMM>', #jladd
                        1: '<@U033J8Q34>', #cwang
                        2: '<@SA3BKGW3E>', #qe,
                        3: '<@SA3BKGW3E>', #qe,
                        4: '<@U9T44HF35>'} #unlikelyzero

    button_owner_msg = ''
    if show_button_owner.lower() == 'true' and day_of_the_week < 5:
        button_owner_msg = '\nButton: {0}'.format(button_owner_map[day_of_the_week])

    post_slack_msg('{0} {1}\nTotal failures: {2}{3}'.format(description, emoji, total_failures, button_owner_msg))


if __name__ == '__main__':
    create_test_update()
