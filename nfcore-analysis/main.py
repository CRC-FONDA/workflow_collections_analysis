from parse_nf_json import generate_nfcore_pipelines_data
from create_dag_commands import process_nf_pipelines_data
from execute_dag_commands import execute_pipeline_commands
from clone_repos import clone_repositories

def main():
	print('Start main script ...')
	#generate_nfcore_pipelines_data()
	#process_nf_pipelines_data()
	#execute_pipeline_commands()
	clone_repositories()

if __name__ == "__main__":
	main()
