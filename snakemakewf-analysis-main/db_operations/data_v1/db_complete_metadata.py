from db_operations.db_connector import DBConnector

connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
db_name = "git_scraping"
coll_name = "data_v1"
db = DBConnector(connection_string, db_name, coll_name)

def get_mid_level_metadata():
    query = db.coll.aggregate([
        {"$group": {
            "_id": "null",
            "avg_files": {"$avg": {"$size": "$commit_content.files"}}
        }}
    ])
    avg_files = query.next()["avg_files"]
    query = db.coll.aggregate([
        {"$unwind": "$commit_content.files"},
        {"$match": {"commit_content.files.filename": {"$regex": "Snakefile"}}},
        {"$group": {
            "_id": "null",
            "snakefile_cnt": {"$count": {}},
            "avg_snakefile_add": {"$avg": "$commit_content.files.additions"},
            "avg_snakefile_del": {"$avg": "$commit_content.files.deletions"}
        }}
    ])
    result1 = query.next()
    query = db.coll.aggregate([
        {"$unwind": "$commit_content.files"},
        {"$unwind": "$commit_content.files.hunks"},
        {"$group": {
            "_id": "null",
            "hunk_cnt": {"$count": {}},
        }}
    ])
    result2 = query.next()
    out = {}
    out["avg_files"] = avg_files
    out.update(result1)
    out.update(result2)
    return out


def get_mid_level_metadata_maunual():
    cursor = db.coll.find({})
    commit_cnt = 0
    files_cnt = 0
    snakefile_cnt = 0
    snakefile_additions_cnt = 0
    snakefile_deletions_cnt = 0
    for commit in cursor:
        commit_cnt += 1
        files_cnt += len(commit["commit_content"]["files"])
        for file in commit["commit_content"]["files"]:
            if "snakemake" in file["filename"]:
                snakefile_cnt += 1
                snakefile_additions_cnt += file["additions"]
                snakefile_deletions_cnt += file["deletions"]
    return files_cnt / commit_cnt, snakefile_cnt, snakefile_additions_cnt / snakefile_cnt, snakefile_deletions_cnt / snakefile_cnt


def get_top_level_metadata():
    repo_groups = db.coll.aggregate([
        {"$group": {
            "_id": "$repo",
            "number_of_commits": {"$count": {}, },
        }}
    ])
    repo_groups_list = [x for x in repo_groups]
    number_of_repos = len(repo_groups_list)
    sorted_repo_commit_counts = sorted([x["number_of_commits"] for x in repo_groups_list])
    avg_file_num, snakefile_cnt, avg_snakefile_add, avg_snakefile_del = db.get_mid_level_metadata()
    data = {
        "number_of_commits": db.coll.count_documents({}),
        "number_of_repos": number_of_repos,
        "avg_commits_per_repo": db.coll.aggregate([
            {"$group": {
                "_id": "$repo",
                "number_of_commits": {"$count": {}}
            }},
            {"$group": {
                "_id": "null",
                "avg_commits": {"$avg": "$number_of_commits"}
            }}
        ]).next()["avg_commits"],
        "commit_count_25_percentile": sorted_repo_commit_counts[int(number_of_repos / 4)],
        "commit_count_50_percentile": sorted_repo_commit_counts[int(number_of_repos / 2)],
        "commit_count_75_percentile": sorted_repo_commit_counts[int((number_of_repos / 4) * 3)],
        "avg_file_num": avg_file_num,
        "snakefile_cnt": snakefile_cnt,
        "avg_snakefile_add": avg_snakefile_add,
        "avg_snakefile_del": avg_snakefile_del,
        "index_information": db.coll.index_information(),
        "list_indexes": db.coll.list_indexes().next()
    }
    return data
