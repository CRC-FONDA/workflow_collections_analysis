from ...utility.final_state_utility import iterate_all_files
from ...utility.parsers.snakefile_parser import iterate_snakefile_lines_with_context
from ...db_operations.db_connector import DBConnector
db = DBConnector()


def run_branching_analysis():
    print("Do the branching analysis")

    for repo, file_name, file_content in iterate_all_files():
        if file_name != "Snakefile":
            continue

        print("repo:", repo)
        print("file_name:", file_name)
        print("file_content:", file_content)

        for i, line, context_key in iterate_snakefile_lines_with_context(file_content):
            print(i, context_key, line)

        exit()

