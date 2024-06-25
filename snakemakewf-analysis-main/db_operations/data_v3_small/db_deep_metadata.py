from code.db_connector import DBConnector
from db_operations.data_v3_small.query_lightweight_db import get_workflow_files, test_for_workflowfile

connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
db_name = "git_scraping"
deep_db = DBConnector(connection_string, db_name, "data_v3_small")
metadata_path = "../../metadata/deep_metadata.txt"


def get_full_metadata():
    num_repos = 0
    num_hunks = 0
    num_files = 0
    num_files_with_include = 0
    num_files_with_module = 0
    avg_hunk_add = 0
    avg_hunk_del = 0
    num_snakefiles = 0
    num_snakefile_hunks = 0
    num_snakefiles_with_include = 0
    num_snakefiles_with_module = 0
    avg_snakefile_hunk_add = 0
    avg_snakefile_hunk_del = 0
    num_workflowfiles = 0
    num_workflowfile_hunks = 0
    num_workflowfiles_with_include = 0
    num_workflowfiles_with_module = 0
    avg_workflowfile_hunk_add = 0
    avg_workflowfile_hunk_del = 0

    repos = deep_db.coll.find({})
    repo_hunks_list = []
    snakefile_hunks_list = []
    workflowfile_hunks_list = []
    for repo in repos:
        num_repos += 1
        print("collecting for repo: (" + str(num_repos)+") "+repo["repo"])
        repo_hunks = 0
        workflow_files = get_workflow_files(repo)
        for filename, file in repo["files"].items():
            is_snakefile = True if "nakefile" in filename else False
            snakefile_hunks = 0
            is_workflowfile = test_for_workflowfile(workflow_files, filename)
            workflowfile_hunks = 0
            num_files += 1
            if file["includes"]:
                num_files_with_include += 1
            if file["modules"]:
                num_files_with_module += 1
            if is_snakefile:
                num_snakefiles += 1
                if file["includes"]:
                    num_snakefiles_with_include += 1
                if file["modules"]:
                    num_snakefiles_with_module += 1
            if is_workflowfile:
                num_workflowfiles += 1
                if file["includes"]:
                    num_workflowfiles_with_include += 1
                if file["modules"]:
                    num_workflowfiles_with_module += 1
            for hunk in file["hunks"]:
                num_hunks += 1
                repo_hunks += 1
                avg_hunk_add += hunk["added"]
                avg_hunk_del += hunk["deleted"]
                if is_snakefile:
                    num_snakefile_hunks += 1
                    snakefile_hunks += 1
                    avg_snakefile_hunk_add += hunk["added"]
                    avg_snakefile_hunk_del += hunk["deleted"]
                if is_workflowfile:
                    num_workflowfile_hunks += 1
                    workflowfile_hunks += 1
                    avg_workflowfile_hunk_add += hunk["added"]
                    avg_workflowfile_hunk_del += hunk["deleted"]
            if is_snakefile:
                snakefile_hunks_list.append(snakefile_hunks)
            if is_workflowfile:
                workflowfile_hunks_list.append(workflowfile_hunks)
        repo_hunks_list.append(repo_hunks)

    num_files_per_repo = num_files / num_repos
    avg_hunk_per_repo = num_hunks / num_repos
    avg_hunk_add = avg_hunk_add / num_hunks
    avg_hunk_del = avg_hunk_del / num_hunks
    avg_snakefile_hunk_add = avg_snakefile_hunk_add / num_snakefile_hunks
    avg_snakefile_hunk_del = avg_snakefile_hunk_del / num_snakefile_hunks
    avg_hunk_per_snakefile = num_snakefile_hunks / num_snakefiles
    avg_workflowfile_hunk_add = avg_workflowfile_hunk_add / num_workflowfile_hunks
    avg_workflowfile_hunk_del = avg_workflowfile_hunk_del / num_workflowfile_hunks
    avg_hunk_per_workflowfile = num_workflowfile_hunks / num_workflowfiles

    repo_hunks_list.sort()
    hunk_count_25_percentile = repo_hunks_list[int(num_repos / 4)]
    hunk_count_50_percentile = repo_hunks_list[int(num_repos / 2)]
    hunk_count_75_percentile = repo_hunks_list[int((num_repos / 4) * 3)]

    snakefile_hunks_list.sort()
    snakefile_hunk_count_25_percentile = snakefile_hunks_list[int(num_snakefiles / 4)]
    snakefile_hunk_count_50_percentile = snakefile_hunks_list[int(num_snakefiles / 2)]
    snakefile_hunk_count_75_percentile = snakefile_hunks_list[int((num_snakefiles / 4) * 3)]

    workflowfile_hunks_list.sort()
    workflowfile_hunk_count_25_percentile = workflowfile_hunks_list[int(num_workflowfiles / 4)]
    workflowfile_hunk_count_50_percentile = workflowfile_hunks_list[int(num_workflowfiles / 2)]
    workflowfile_hunk_count_75_percentile = workflowfile_hunks_list[int((num_workflowfiles / 4) * 3)]

    metadata = {
        "num_repos": num_repos,
        "num_hunks": num_hunks,
        "avg_hunk_per_repo": avg_hunk_per_repo,
        "hunk_count_25_percentile": hunk_count_25_percentile,
        "hunk_count_50_percentile": hunk_count_50_percentile,
        "hunk_count_75_percentile": hunk_count_75_percentile,
        "num_files": num_files,
        "num_files_per_repo": num_files_per_repo,
        "num_files_with_include": num_files_with_include,
        "num_files_with_module": num_files_with_module,
        "avg_hunk_add": avg_hunk_add,
        "avg_hunk_del": avg_hunk_del,
        "num_snakefiles": num_snakefiles,
        "num_snakefile_hunks": num_snakefile_hunks,
        "num_snakefiles_with_include": num_snakefiles_with_include,
        "num_snakefiles_with_module": num_snakefiles_with_module,
        "avg_snakefile_hunk_add": avg_snakefile_hunk_add,
        "avg_snakefile_hunk_del": avg_snakefile_hunk_del,
        "avg_hunk_per_snakefile": avg_hunk_per_snakefile,
        "snakefile_hunk_count_25_percentile": snakefile_hunk_count_25_percentile,
        "snakefile_hunk_count_50_percentile": snakefile_hunk_count_50_percentile,
        "snakefile_hunk_count_75_percentile": snakefile_hunk_count_75_percentile,
        "num_workflowfiles": num_workflowfiles,
        "num_workflowfile_hunks": num_workflowfile_hunks,
        "num_workflowfiles_with_include": num_workflowfiles_with_include,
        "num_workflowfiles_with_module": num_workflowfiles_with_module,
        "avg_workflowfile_hunk_add": avg_workflowfile_hunk_add,
        "avg_workflowfile_hunk_del": avg_workflowfile_hunk_del,
        "avg_hunk_per_workflowfile": avg_hunk_per_workflowfile,
        "workflowfile_hunk_count_25_percentile": workflowfile_hunk_count_25_percentile,
        "workflowfile_hunk_count_50_percentile": workflowfile_hunk_count_50_percentile,
        "workflowfile_hunk_count_75_percentile": workflowfile_hunk_count_75_percentile,
    }
    print("-------------------------------------------------------------------------------------")
    print(repo_hunks_list)
    print("-------------------------------------------------------------------------------------")
    print(snakefile_hunks_list)
    return metadata


def write_metadata(metadata):
    with open(metadata_path, "a") as f:
        for key, value in metadata.items():
            f.write(key + ": "+str(value) + "\n")



write_metadata(get_full_metadata())
print("done!")
