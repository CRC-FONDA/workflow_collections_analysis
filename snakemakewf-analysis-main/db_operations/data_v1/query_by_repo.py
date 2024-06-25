from db_operations.db_connector import DBConnector

connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
db_name = "git_scraping"
coll_name = "data_v1"
db = DBConnector(connection_string, db_name, coll_name)


def get_full_data_by_repo():
    query = db.coll.aggregate([
        {"$group": {
            "_id": "$repo",
            "items": {"$push": "$$ROOT"}
        }}
    ], allowDiskUse=True)
    repos = query.next()
    return repos
