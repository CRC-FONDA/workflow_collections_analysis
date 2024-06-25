from db_operations.db_connector import DBConnector

connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
db_name = "git_scraping"
old_db = DBConnector(connection_string, db_name, "data_v1")
shallow_db = DBConnector(connection_string, db_name, "data_v2_small")
deep_db = DBConnector(connection_string, db_name, "data_v3_small")


def create_shallow_lightweight_db():
    query = old_db.coll.aggregate([
        {"$unwind": "$commit_content.files"},
        {"$unwind": "$commit_content.files.hunks"},
        {"$project": {
            "_id": 1,
            "standardised": 1,
            "repo": 1,
            "commit_content.files.filename": 1,
            "commit_content.files.includes": 1,
            "commit_content.files.modules": 1,
            "commit_content.files.hunks.added": 1,
            "commit_content.files.hunks.deleted": 1,
            "commit_content.files.hunks.hunk_lines": 1
        }}
    ])
    cnt = 0
    for document in query:

        document["old_id"] = document["_id"]
        del document["_id"]
        document["filename"] = document["commit_content"]["files"]["filename"]
        document["added"] = document["commit_content"]["files"]["hunks"]["added"]
        document["deleted"] = document["commit_content"]["files"]["hunks"]["deleted"]
        document["hunk_lines"] = document["commit_content"]["files"]["hunks"]["hunk_lines"]
        try:
            document["includes"] = document["commit_content"]["files"]["includes"]
        except KeyError as e:
            document["includes"] = None
        try:
            document["modules"] = document["commit_content"]["files"]["modules"]
        except KeyError as e:
            document["modules"] = None
        del document["commit_content"]

        shallow_db.coll.insert_one(document)
        print(str(cnt)+": inserted doc: "+str(document["old_id"]))
        cnt += 1


def create_deep_lightweight_db():
    query = shallow_db.coll.aggregate([
        {"$group": {
            "_id": "$repo",
            "items": {"$push": "$$ROOT"}
        }}
    ], allowDiskUse=True)
    cnt = 0
    for repo in query:
        items = repo["items"]
        files = {}
        for item in items:
            filename = item["filename"]
            hunk = {
                "old_id": item["old_id"],
                "added": item["added"],
                "deleted": item["deleted"],
                "hunk_lines": item["hunk_lines"]
            }
            if filename in files:
                files[filename]["hunks"].append(hunk)
            else:
                files[filename] = {
                    "includes": item["includes"],
                    "modules": item["modules"],
                    "hunks": [hunk]
                }
        doc = {
            "repo": str(repo["_id"]),
            "standardised": items[0]["standardised"],
            "files": files
        }
        deep_db.coll.insert_one(doc)
        print(str(cnt)+": inserted doc fo repo: " + str(doc["repo"]))
        cnt += 1


def display_random_data():
    repo = deep_db.coll.aggregate([{"$sample": {"size": 1}}]).next()
    print("repo: " + repo["repo"])
    print("standardised: " + str(repo["standardised"]))
    print("files:")
    for key, value in repo["files"].items():
        print("-------------------------------------------------------------------------------------------")
        print(key + ": ")
        print("includes: "+str(value["includes"]))
        print("modules: " + str(value["modules"]))
        for hunk in value["hunks"]:
            print(hunk)
    return repo


