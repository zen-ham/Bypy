import os


os.chdir(os.path.dirname(__file__))

message = f'merge to github from kiddy'


def push(message):
    os.system('git add .')
    os.system(f'git commit -m "{message}"')
    os.system('git push -u origin master')


def pull():
    os.system('git pull origin master')


def init(repo_url):
    os.system('git init')
    os.system('git add .')
    os.system(f'git commit -m "Initial commit"')
    os.system(f'git remote add origin {repo_url}.git')
    os.system('git push -u origin master')


def push_pull(message):
    push(message)
    pull()


def set_to_merge():
    os.system('git config pull.rebase false')


set_to_merge()
for i in range(3):
    push_pull(message)