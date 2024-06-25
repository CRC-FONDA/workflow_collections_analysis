from ...db_operations.db_connector import DBConnector
db = DBConnector()


def scan_notebook_dags(path_prefix="github_scraping/analysis/notebooks/"):
    with open(path_prefix + "notebook_repos.txt", "r") as f:
        repos = [line.strip() for line in f.readlines()]

    total = 0
    cloned = 0
    dags = 0

    for repo in repos:
        total += 1
        repo_data = db.workflow_structures.find({"repo": repo}).next()
        print(total, repo, "cloned =", repo_data["cloned"], "dag_type =", type(repo_data["dag"]))
        if repo_data["cloned"]:
            cloned += 1
        if repo_data["dag"] is not None:
            dags += 1
            print(repo_data["dag"])


    print("total = "+str(total)+", cloned = "+str(cloned)+", dags = "+str(dags))
