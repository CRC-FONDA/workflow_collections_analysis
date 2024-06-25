import urllib.request
import json
import time

from utility.graph_utility import (
    get_n_nodes_from_dag_string,
    update_dag_history_data,
    get_graph_from_commit_dag_string,
)
from analysis.workflow_structure.graph_analysis.parallelism import determine_parallelism
from db_operations.db_connector import DBConnector
db = DBConnector()


def annotate_with_commit_lines():
    filter = {"commit_data": {"$exists": False}}
    n_docs = str(db.dag_histories.count_documents(filter))
    query = db.dag_histories.find(filter)

    i = 0
    for commit in query:
        i += 1
        repo = commit["repo"]
        sha = commit["sha"]
        git_url = "https://api.github.com/repos/" + repo + "/commits/" + sha

        try:
            req = urllib.request.Request(git_url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            req.add_header('Authorization', 'token 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')
            response = urllib.request.urlopen(req)

        except Exception as e:
            print("failed to get commit content for "+repo+", "+sha+", error: "+str(e))
            continue

        # handle github rate limit
        headers = response.headers.as_string()
        header = "X-RateLimit-Remaining:"
        begin = headers.find(header) + len(header)
        end = headers.find("\n", begin)
        limit = int(headers[begin:end])

        if limit < 100:
            time.sleep(60)

        # extract data from response
        response = json.load(response)
        files = dict()
        for file in response["files"]:
            filename = file["filename"]
            remove_keys = [
                "filename",
                "blob_url",
                "raw_url",
                "contents_url"
            ]
            for key in remove_keys:
                del file[key]
            files[filename] = file
        commit_data = {
            "stats": response["stats"],
            "files": files
        }

        status = db.dag_histories.find_one_and_update(
            {"_id": commit["_id"]},
            {"$set": {"commit_data": commit_data}}
        )
        if status is None:
            print("failed to update document for "+repo+", "+sha)

        # print progress
        print("(" + str(i) + "/" + n_docs + ", limit="+str(limit)+") " + repo + ", " + sha)


def annotate_with_predecessors():
    repos = db.dag_histories.distinct("repo")
    m = len(repos)
    i = 0
    for repo in repos:
        i += 1
        print("(" + str(i) + "/" + str(m) + ") " + repo)
        f = {"$and": [
            {"repo": repo},
            {"dag": {"$ne": None}}
        ]}
        commits = db.dag_histories.find(f)
        commits = [x for x in commits]
        commits.sort(key=lambda x: x["commit_number"], reverse=True)
        # commit with the highest commit number comes first and is the oldest commit for this repo
        k = len(commits)
        for j in range(1, k):
            print("  looking at commit "+str(j)+"/"+str(k-1))
            successor = commits[j]
            if False and "n_nodes_from_dag_string" in successor.keys():
                successor_n_nodes = successor["n_nodes_from_dag_string"]
            else:
                successor_n_nodes = get_n_nodes_from_dag_string(successor["dag"])
                db.dag_histories.find_one_and_update(
                    {"_id": successor["_id"]},
                    {"$set": {"n_nodes_from_dag_string": successor_n_nodes}}
                )

            predecessor = commits[j - 1]
            if False and "n_nodes_from_dag_string" in predecessor.keys():
                predecessor_n_nodes = predecessor["n_nodes_from_dag_string"]
            else:
                predecessor_n_nodes = get_n_nodes_from_dag_string(predecessor["dag"])
                db.dag_histories.find_one_and_update(
                    {"_id": predecessor["_id"]},
                    {"$set": {"n_nodes_from_dag_string": predecessor_n_nodes}}
                )

            if successor_n_nodes != predecessor_n_nodes:
                # do dag metadata analysis for both commits
                for commit in [predecessor, successor]:
                    graph = get_graph_from_commit_dag_string(commit)
                    # update metadata from graph
                    _id = commit["_id"]
                    (
                        n_nodes,
                        n_parallel_pairs,
                        n_logical_rules,
                        longest_path,
                        max_degree,
                        avg_degree,
                    ) = determine_parallelism(graph, repo=commit["repo"], local=False, _id=_id,
                                              dag_string=commit["dag"])
                    update_dag_history_data(_id, "graph.n_nodes", n_nodes)
                    update_dag_history_data(_id, "graph.n_parallel_pairs", n_parallel_pairs)
                    update_dag_history_data(_id, "graph.n_logical_rules", n_logical_rules)
                    update_dag_history_data(_id, "graph.longest_path", longest_path)
                    update_dag_history_data(_id, "graph.max_degree", max_degree)
                    update_dag_history_data(_id, "graph.avg_degree", avg_degree)

                # update successor commit with predecessor _id
                status = db.dag_histories.find_one_and_update(
                    {"_id": successor["_id"]},
                    {"$set": {"different_n_nodes_predecessor_id": predecessor["_id"]}}
                )
                if status is None:
                    print("    failed to update document for " + repo + ", commit_number=" + commits[j]["commit_number"])
                else:
                    print("    successfully updated commit:", predecessor_n_nodes, successor_n_nodes)
            else:
                print("    same number of nodes:", predecessor_n_nodes, successor_n_nodes)




