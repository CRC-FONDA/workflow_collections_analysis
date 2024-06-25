from .utility import update_collection
from db_operations.db_connector import DBConnector
db = DBConnector()


def annotate_graphs_with_n_commits():
    f1 = {"graph": {"$exists": True}}
    query1 = db.workflow_structures.find(f1)
    for repo in query1:
        f2 = {"repo": repo["repo"]}
        n_commits = db.full_commits.count_documents(f2)
        print("REPO: "+repo["repo"])
        print(n_commits)
        update_collection(repo["repo"], "commits.n_commits", n_commits)
        print("--------------------------------------------")


def annotate_graphs_with_commit_sizes():
    f1 = {"graph": {"$exists": True}}
    query1 = db.workflow_structures.find(f1)
    i = 0
    number_of_repos = db.workflow_structures.count_documents(f1)
    for repo in query1:
        i += 1
        print("("+str(i)+"/"+str(number_of_repos)+") REPO: " + repo["repo"])
        commit_lines = []
        f2 = {"repo": repo["repo"]}
        query2 = db.full_commits.find(f2)
        for commit in query2:
            total = commit["commit_content"]["stats"]["total"]
            commit_lines.append(total)
        total_sum = sum(commit_lines)
        total_avg = total_sum / len(commit_lines) if commit_lines else 0
        commit_lines.sort(reverse=True)
        commit_lines = commit_lines[1:]
        total_sum_without_max = sum(commit_lines)
        total_avg_without_max = total_sum_without_max / len(commit_lines) if commit_lines else 0

        update_collection(repo["repo"], "commits.line_changes.total_sum", total_sum)
        update_collection(repo["repo"], "commits.line_changes.total_avg", total_avg)
        update_collection(repo["repo"], "commits.line_changes.total_sum_without_max", total_sum_without_max)
        update_collection(repo["repo"], "commits.line_changes.total_avg_without_max", total_avg_without_max)

        print("--------------------------------------------")

