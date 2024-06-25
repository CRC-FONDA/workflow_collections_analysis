from db_operations.db_connector import DBConnector
db = DBConnector()


def update_collection(repo, field, value):
    status = db.workflow_structures.find_one_and_update(
        {"repo": repo},
        {"$set": {field: value}}
    )
    if status is None:
        print("Unable to update "+repo+" with field="+str(field)+", value="+str(value))