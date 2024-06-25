from db_operations.db_connector import DBConnector

db = DBConnector()

data = db.final_state.find({"repo": "KonstantinBurkin/cbai"})

for x in data:
    print(x["repo"])
    print(x["workflow_files"])
    for key in x["files"].keys():
        print(key)
    print(x["files"]["Asset_2.svg"].keys())

#no unique workflow file (rules/qc.smk) in repo: KonstantinBurkin/cbai
#no unique workflow file (rules/stats.smk) in repo: KonstantinBurkin/cbai
#no unique workflow file (rules/filtering.smk) in repo: KonstantinBurkin/cbai
