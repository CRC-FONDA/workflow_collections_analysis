from utility.graph_utility import get_n_nodes_from_dag_string
from db_operations.db_connector import DBConnector
db = DBConnector()


def get_commit_pairs_of_graph_change():
    repos = db.dag_histories.distinct("repo")
    m = len(repos)
    i = 0
    for repo in repos:
        i += 1
        print("("+str(i)+"/"+str(m)+") "+repo)
        commits = db.dag_histories.find({"$and": [
            {"repo": repo},
            {"dag": {"$exists": True}},
            {"dag": {"$ne": None}}
        ]})
        commits = [x for x in commits]
        commits.sort(key=lambda x: x["commit_number"], reverse=True)
        n_nodes = []
        for j in range(len(commits)):
            n_nodes.append(get_n_nodes_from_dag_string(commits[j]["dag"]))
        # debug results
        #for j in range(len(commits)):
        #    print("commit_number="+str(commits[j]["commit_number"])+", n_nodes="+str(n_nodes[j]))

        for j in range(1, len(commits)):
            if n_nodes[j-1] != n_nodes[j]:
                yield commits[j-1], commits[j]







def broken_aggregation():
    query = db.dag_histories.aggregate(
        [
            {
                "$group": {
                    "_id": "$repo",
                    "commits": {
                        "$push": {
                            "old_id": "$_id",
                            "sha": "$sha",
                            "dag": "$dag"
                        }
                    }
                }
            }
        ], allowDiskUse=True
    )
    i = 1
    for x in query:
        print(i, x["_id"], x.keys())
        i += 1

