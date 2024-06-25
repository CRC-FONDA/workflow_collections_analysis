import pandas as pd
import os

def execute_pipeline_commands():
    current_directory = os.getcwd()

    df = pd.read_csv('./data/nf_pipelines_dataframe.csv', encoding='utf-8')

    if not os.path.exists('dags'):
        os.makedirs('dags')

    if not os.path.exists('execution_tests'):
        os.makedirs('execution_tests')

    os.chdir('execution_tests')
    
    # change version, to generate DAGS of pipelines written in DSL1
    #change_version = 'export NXF_VER="22.09.3-edge"'
    #os.system(change_version)
    
    dag_gen = False
    
    for index, row in df.iterrows():
        pipeline_command = row['test_command']
        pipeline = row['name']
        #pipeline_dag = f'../dags/{pipeline}_dag.dot'
        pipeline_dag = os.path.join('..', 'dags', f'{pipeline}_dag.dot')
        #pipeline_png = f'../dags/{pipeline}_dag.png'
        pipeline_png = os.path.join('..', 'dags', f'{pipeline}_dag.png')


        if os.path.exists(pipeline_dag) or row['was_generated']:
            print(f'The file {pipeline_dag} already exists in the folder!')
        else:
            run_test_dag = f'{pipeline_command} -with-dag {pipeline_dag}'
            print(f'The command: {run_test_dag} will be executed for {pipeline}.')
            os.system(run_test_dag)
            run_dot_png = f'dot -Tpng {pipeline_dag} -o {pipeline_png}'
            os.system(run_dot_png)
            dag_gen = True
        
        if not os.path.exists(pipeline_dag):
            print(f'No DAG for the pipeline {pipeline} was generated.')
            dag_gen = False

        # to update the df
        df.at[index, 'was_generated'] = dag_gen
	
    os.chdir(current_directory)
    df.to_csv('./data/nf_pipelines_dataframe.csv', encoding='utf-8', index=False)

    true_count = df['was_generated'].sum()
    all_count = len(df)
    print(f'For {true_count} pipelines out of {all_count} was a DAG generated.')
    print('Script completely executed.')
