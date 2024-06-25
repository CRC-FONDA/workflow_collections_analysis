def query_snakefile_commits(self):
    return self.coll.aggregate([
        {"$match": {"commit_content.files.filename": {"$regex": "Snakefile"}}},
        {"$unwind": "$commit_content.files"},
        {"$match": {"commit_content.files.filename": {"$regex": "Snakefile"}}},
        {"$project": {"commit_content.files.filename": 1, "commit_content.files.additions": 1,
                      "commit_content.files.deletions": 1, "commit_content.files.changes": 1,
                      "commit_content.files.patch": 1}}
    ])