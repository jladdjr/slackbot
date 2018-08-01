#!/usr/bin/env python

import os

from github import Github
from slacker import Slacker

github_username = os.getenv('GITHUB_USERNAME')
github_password = os.getenv('GITHUB_PASSWORD')
github_repo = os.getenv('GITHUB_REPO')
github_milestone = os.getenv('GITHUB_MILESTONE')

slack_token = os.getenv('SLACK_TOKEN')
slack_channel = os.getenv('SLACK_CHANNEL')
slack = Slacker(slack_token)


def post_slack_msg(text):
    slack.chat.post_message(slack_channel, text, icon_emoji=':ansible:')


def create_issue_update():
    git = Github(github_username, github_password)
    repo = git.get_repo(github_repo)
    milestones = repo.get_milestones(state="open")
    for milestone in milestones:
        if milestone.title.lower() == github_milestone.lower():
            current_milestone = milestone
            break
    else:
        raise Exception("Failed to find milestone '{}'".format(github_milestone))

    issues = repo.get_issues(milestone=current_milestone)
    num_issues = len([i for i in issues if not i.pull_request])

    return "{} open issues in milestone `{}`".format(num_issues, github_milestone)

post_slack_msg(create_issue_update())

if __name__ == '__main__':
    create_issue_update()
