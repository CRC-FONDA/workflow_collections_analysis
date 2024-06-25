import json
import os
import pandas as pd

def generate_nfcore_pipelines_data():

    if not os.path.exists('data'):
        os.makedirs('data')

    nfcore_json_cmd = 'nf-core list --json > ./data/pipelines.json'
    os.system(nfcore_json_cmd)

    # read JSON data from 'data/pipelines.json'
    with open('./data/pipelines.json', 'r') as file:
        json_data = file.read()

    # remove new lines, had some issues in the beginning
    json_data = json_data.replace('\n', '')

    # rewrite the cleaned JSON
    with open('./data/nf_pipelines.json', 'w') as file:
        file.write(json_data)

    # try to parse the JSON
    try:
        parsed_data = json.loads(json_data)
        print('JSON parsed successfully!')
    except json.JSONDecodeError as e:
        print('JSON Decode Error:', e)

    with open('./data/nf_pipelines.json') as f:
        data = json.load(f)

    d = []
    for pipeline in data['remote_workflows']:
        full_name = pipeline['full_name']
        name = pipeline['name']
        name = full_name.replace('nf-core/', '')
        git_url = f'https://github.com/nf-core/{name}.git'

        for releases in pipeline['releases']:
            active_tag = releases['tag_name']
            break

        nf_url = f'https://nf-co.re/{name}/{active_tag}'
        test_command = f'nextflow run {full_name} -r {active_tag} -profile test --outdir {name}'
        test_dag_command = f'nextflow run {full_name} -r {active_tag} -profile test --outdir {name} -with-dag {name}_dag.dot'

        # append columns to df
        d.append({
            'name': name,
            'full_name': full_name,
            'test_command': test_command,
            'repository': git_url,
            'test_dag_command': test_dag_command,
            'domain': nf_url,
            'was_generated': False,
            'command_executed': False
        })

    df = pd.DataFrame(d)

    df.to_csv('./data/nf_pipelines_dataframe.csv', encoding='utf-8', index=False)
