import os
from platform import uname

os.chdir(os.path.dirname(__file__))

message = f'merge to github from {uname().node}'

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

for i in range(3):
    push_pull(message)