from pymongo import MongoClient


def insert_repo_history(data):
    connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
    client = MongoClient(connection_string)
    db = client.git_scraping
    db.test_data.insert_one(data)


def get_filtered_diff_count():
    connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
    client = MongoClient(connection_string)
    db = client.git_scraping


def test_db():
    connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
    client = MongoClient(connection_string)
    db = client.git_scraping
    coll = db['dummy']
    cursor = coll.find({"file": {"$exists": True}})
    return cursor


def get_full_coll(coll_name):
    connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
    client = MongoClient(connection_string)
    db = client.git_scraping
    coll = db[coll_name]
    cursor = coll.find({})
    return [i for i in cursor]


def insert_coll(coll_name, doc):
    connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
    client = MongoClient(connection_string)
    db = client.git_scraping
    coll = db[coll_name]
    coll.insert_one(doc)


def clear_coll(coll_name):
    connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
    client = MongoClient(connection_string)
    db = client.git_scraping
    coll = db[coll_name]
    coll.delete_many({})


def db_op():
    connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
    client = MongoClient(connection_string)
    db = client.git_scraping
    coll = db.list_collection_names()
    return coll
