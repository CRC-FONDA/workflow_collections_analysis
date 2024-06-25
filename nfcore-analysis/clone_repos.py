import os
import pandas as pd

def clone_repositories():
    data = pd.read_csv('./data/nf_pipelines_dataframe.csv', encoding='utf-8')

    # check if 'git_repos' folder exists, if not create
    git_repos_folder = 'git_repos'
    if not os.path.exists(git_repos_folder):
        os.makedirs(git_repos_folder)

    os.chdir(git_repos_folder)

    for index, row in data.iterrows():
        repo_url = row['repository']
        name = row['name']

        # check if the repo is already in folder
        if not os.path.exists(name):

            os.system(f'git clone {repo_url}')

        print(f'{name} cloned')

    os.chdir('..')
