from utility.dag_histories_utility import (
    get_commit_pairs_of_graph_change,
)

from db_operations.db_connector import DBConnector
db = DBConnector()


def fill_collection():
    i = 0
    for x, y in get_commit_pairs_of_graph_change():
        i += 1
        print(i)
        doc = {
            "commit_ids": [x["_id"], y["_id"]],
        }
        db.commit_difference_pairs.insert_one(doc)


def update_with_repo():
    m = str(db.commit_difference_pairs.count_documents({}))
    i = 0
    query = db.commit_difference_pairs.find()
    for pair in query:
        i += 1
        commit_id = pair["commit_ids"][0]
        repo = db.dag_histories.find({
            "_id": commit_id
        }).next()["repo"]

        print("(" + str(i) + "/" + m + ") " + repo)

        status = db.commit_difference_pairs.find_one_and_update(
            {"_id": pair["_id"]},
            {"$set": {"repo": repo}}
        )


def update_with_graph_difference():
    m = str(db.commit_difference_pairs.count_documents({}))
    i = 0
    for x, y, _id in get_difference_commits():
        i += 1
        print(i)
        try:
            n_nodes_diff = abs(x["graph"]["n_nodes"] - y["graph"]["n_nodes"])
            n_parallel_pairs_diff = abs(x["graph"]["n_parallel_pairs"] - y["graph"]["n_parallel_pairs"])
            n_l_rules_diff = abs(x["graph"]["n_logical_rules"] - y["graph"]["n_logical_rules"])
            n_nodes = [x["graph"]["n_nodes"], y["graph"]["n_nodes"]]
            db.commit_difference_pairs.find_one_and_update(
                {"_id": _id},
                {"$set": {
                    "n_nodes": n_nodes,
                    "n_nodes_diff": n_nodes_diff,
                    "n_parallel_pairs_diff": n_parallel_pairs_diff,
                    "n_l_rules_diff": n_l_rules_diff,
                }})
        except KeyError as e:
            print(e)


def get_difference_commits():
    query = db.commit_difference_pairs.find()
    for pair in query:
        commit_ids = pair["commit_ids"]
        docs = db.dag_histories.find({
            "$or": [
                {"_id": commit_ids[0]},
                {"_id": commit_ids[1]},
            ]})
        yield docs.next(), docs.next(), pair["_id"]


def get_dag_histories_from_pair(pair):
    commit_ids = pair["commit_ids"]
    docs = db.dag_histories.find({
        "$or": [
            {"_id": commit_ids[0]},
            {"_id": commit_ids[1]},
        ]})
    return docs.next(), docs.next()








