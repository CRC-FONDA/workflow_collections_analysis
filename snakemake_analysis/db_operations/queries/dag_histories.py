from ..db_connector import DBConnector
db = DBConnector()


def write_metadata():
    f0 = {"commit_data": {"$exists": True}}

    f2 = {"$and": [
        # {"dag": {"$exists": True}},
        {"dag": {"$ne": None}}
    ]}
    f3 = {"graph": {"$exists": True}}
    f4 = {"different_n_nodes_predecessor_id": {"$exists": True}}
    f5 = {"$and": [
        {"different_n_nodes_predecessor_id": {"$exists": True}},
        {"commit_data.stats.total": {"$lt": 10}}
    ]}

    n1 = db.dag_histories.count_documents({})
    n2 = db.dag_histories.count_documents(f2)
    n3 = db.dag_histories.count_documents(f3)
    n4 = db.dag_histories.count_documents(f4)
    n5 = db.dag_histories.count_documents(f5)

    print("\nCollection: dag_histories")
    print("total number of commits:", n1)
    print("number of commits with constructed dag:", n2)
    print("number of commits with graph metadata information:", n3)
    print("number of commits with a predecessor with different n of nodes:", n4)
    print("the same and with less than 10 total changes in this commit:", n5)

    # keys of random document
    print("\nCollection: dag_histories")
    random_doc = db.dag_histories.aggregate([
        {"$match": {
            "graph": {"$exists": True}
        }},
        {"$sample": {
            "size": 1
        }},
    ]).next()
    print("MAIN DOCUMENT", random_doc.keys())
    if "graph" in random_doc.keys():
        print("GRAPH", random_doc["graph"].keys())

    print("\nCollection: workflow_structures")
    random_doc = db.workflow_structures.aggregate([
        {"$match": {
            "graph": {"$exists": True}
        }},
        {"$sample": {
            "size": 1
        }},
    ]).next()
    print("MAIN DOCUMENT", random_doc.keys())
    if "graph" in random_doc.keys():
        print("GRAPH", random_doc["graph"].keys())



def get_sorted_difference_hunks():
    aggregate = db.dag_histories.aggregate([
        {"$match": {
            "$and": [
                {"different_n_nodes_predecessor_id": {"$exists": True}},
                {"commit_data.stats.total": {"$lt": 20}},
            ]
        }},
        {"$lookup": {
            "from": "dag_histories",
            "localField": "different_n_nodes_predecessor_id",
            "foreignField": "_id",
            "as": "predecessor"
        }},
        {"$set": {
            "predecessor": {"$first": "$predecessor"}
        }},
        {"$project": {
            "n_predecessor": "$predecessor.n_nodes_from_dag_string",
            '_id': 1,
            'repo': 1,
            'commit_number': 1,
            'sha': 1,
            'commit_message': 1,
            'date': 1,
            'author': 1,
            'dag': 1,
            'dryrun': 1,
            'graph': 1,
            'commit_data': 1,
            'different_n_nodes_predecessor_id': 1,
            'n_nodes_from_dag_string': 1,
        }},
        {"$match": {
            "n_predecessor": {"$ne": None}
        }},
        {"$set": {
            "n_nodes_diff": {"$abs": {"$subtract": ["$n_nodes_from_dag_string", "$n_predecessor"]}}
        }},
        {"$sort": {
            "n_nodes_diff": -1
        }},
    ], allowDiskUse=True)

    for result in aggregate:
        yield result


def write_diff_hunk(doc):
    print(doc["n_nodes_from_dag_string"], doc["n_predecessor"], doc["n_nodes_diff"])
    print(doc["commit_data"]["stats"])
    print("----------------------------------")
    for key, value in doc["commit_data"]["files"].items():
        print("filename = " + key)
        for x, y in value.items():
            print(x, y)
        print("----------------------------------")
    print("################################################################")



