import json
import pandas as pd

def process_nf_pipelines_data():
    with open('./data/nf_pipelines.json', 'r') as f:
        data = json.load(f)

    # process data and create DataFrame
    d = []
    for pipeline in data['remote_workflows']:
        full_name = pipeline['full_name']
        name = full_name.replace('nf-core/', '')
        git_url = f'https://github.com/nf-core/{name}.git'

        for releases in pipeline['releases']:
            active_tag = releases['tag_name']
            break

        nf_url = f'https://nf-co.re/{name}/{active_tag}'
        test_command = f'nextflow run {full_name} -r {active_tag} -profile test --outdir {name}'
        test_dag_command = f'nextflow run {full_name} -r {active_tag} -profile test --outdir {name} -with-dag {name}_dag.dot'

        d.append({
            'name': name,
            'full_name': full_name,
            'test_command': test_command,
            'repository': git_url,
            'test_dag_command': test_dag_command,
            'domain': nf_url,
            'was_generated': False
        })

    # Convert to DataFrame and save to CSV
    df = pd.DataFrame(d)
    df.to_csv('./data/nf_pipelines_dataframe.csv', encoding='utf-8', index=False)

