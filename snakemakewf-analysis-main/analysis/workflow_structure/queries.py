from db_operations.db_connector import DBConnector
db = DBConnector()


def print_dags_with_checkpoint_or_input_func():
    i = 0
    f = {"$and": [
        {"features": {"$ne": None}},
        {"graph": {"$exists": True}},
    ]}
    query = db.workflow_structures.find(f)
    for x in query:
        # print(x.keys())
        print("REPO: " + x["repo"])
        for y1, y2 in x["features"].items():
            print(y1, y2)
            print("-------------------------------------------------------------")
            i += 1
    print(i)


def find_dags_with_commit_history():
    f1 = {"graph": {"$exists": True}}
    query1 = db.workflow_structures.find(f1)
    for repo in query1:
        f2 = {"repo": repo["repo"]}
        n_commits = db.full_commits.count_documents(f2)
        print("REPO: "+repo["repo"])
        print(n_commits)
        print("--------------------------------------------")


def find_repos_with_expected_dag_changes():
    f1 = {"graph": {"$exists": True}}
    query1 = db.workflow_structures.find(f1)
    data = []
    for repo in query1:
        data.append((
            repo["repo"],
            repo["graph"]["n_nodes"],
            repo["commits"]["line_changes"]["total_avg_without_max"],
        ))

    n_nodes_list = [x[1] for x in data]
    max_n_nodes = max(n_nodes_list)
    min_n_nodes = min(n_nodes_list)
    commit_avg_list = [x[2] for x in data]
    max_commit_avg = max(commit_avg_list)
    min_commit_avg = min(commit_avg_list)

    normalized_data = []
    diff_n = max_n_nodes - min_n_nodes
    diff_avg = max_commit_avg - min_commit_avg
    for d in data:
        n = (d[1] - min_n_nodes) / diff_n
        avg = (d[2] - min_commit_avg) / diff_avg
        normalized_data.append((d[0], n, avg, n * avg))
    normalized_data.sort(key=lambda x: x[3], reverse=True)
    #for x in normalized_data:
    #    print(x)
    return normalized_data









