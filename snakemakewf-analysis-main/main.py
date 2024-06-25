#from .analysis.clustering.shell_clustering import kmeans_clustering
from .analysis.clustering.vectorizer import ShellCodeTFIDFVectorizer
#from .analysis.input_wildcards.input_wildcards import update_rules_with_input_output_wildcards, inspect_input_output_wildcards

#from .analysis.operators.full_text_operators import analyse_operators
#from .analysis.operators.common_tools import plot_operator_domains_by_workflow
#from .analysis.operators.operators import (
#    update_rule_collection_with_operators,
#    clean_operator_entries,
#    update_rule_collection_with_config_operator_entries,
#    get_operators_overview,
#    get_config_operator_matches_overview,
#    operator_analysis,
#    plot_config_operator_matches_data,
#)

#from .analysis.operators.operators import inspect_operator_collection
#from .analysis.operators.dag_analysis import iterate_graphs_with_operators
#from .analysis.branching.branching import run_branching_analysis

from .building_collections.final_state_full_repo import add_repo_to_collection
#from.building_collections.update_collection.final_state_no_content_fix import update_no_content_files
from .db_operations.migrate_mongodb import migrate_mongodb

import bson

from .db_operations.db_connector import DBConnector
db = DBConnector()

# ChatGPT API secret key:
chat_gpt_key = "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"


def probe_db():
    repos = db.dag_histories.distinct("repo")
    print(repos)
    print(len(repos))


def probe_db1():
    x = db.dag_histories.aggregate([
        {"$group": {"_id": "$repo", "count": {"$sum": 1}}}
    ])
    for y in x:
        print(y)


def probe_db2():
    docs = db.dag_histories.find({"repo": "gitter-lab/ssps"})

    for doc in docs:
        print("repo: "+doc["repo"]+", commit_number: "+str(doc["commit_number"])+", document size: "+str(len(bson.BSON.encode(doc))))
        print("sha: "+doc["sha"]+", commit_message: "+doc["commit_message"])
        print("date: "+doc["date"]+", author: "+doc["author"])
        print("--------------------------------------------------------")


def probe_dag_history_metadata():
    query = db.dag_histories.find(
        {"graph": {"$exists": True}}
    )

    i = 1
    for x in query:
        #print(x.keys())
        print("("+str(i)+") repo="+x["repo"]+", commit_number="+str(x["commit_number"])+", metadata="+str(x["graph"]))
        i += 1


def probe_difference_commits():
    query = db.commit_difference_pairs.aggregate([
        {"$group": {"_id": "$repo", "commit_ids": {"$push": "$commit_ids"}}}
    ])

    i = 0
    for x in query:
        i += 1
        print(i, x["_id"], len(x["commit_ids"]))


def fill_final_state_full_repo():
    i = 0
    f1 = {"dag": {"$ne": None}}
    for doc in db.workflow_structures.find(f1):
        i += 1
        repo = doc["repo"]
        print(i, repo)
        query = db.final_state_full_repo.find({"repo": repo})
        if next(query, None):
            print("alrady collected " + repo)
            continue
        add_repo_to_collection(repo)


#fill_final_state_full_repo()
#query = db.final_state_full_repo.find()
#i = 0
#for doc in query:
#    i += 1
#    print(i, doc["repo"], doc["scrape_time"])

#snakefile_path = "/home/seb/Fonda/A6/22-12-control-patterns/skip/Snakefile"

#with open(snakefile_path, "r") as f:
#    snakefile = f.readlines()


def test_vectorizer():
    vectorizer = ShellCodeTFIDFVectorizer()
    f1 = {"shell_lines": {"$exists": True, "$not": {"$size": 0}}}
    rules = db.rules.find(f1)
    for rule in rules:
        for line in rule["shell_lines"]:
            print(line)
        v = vectorizer.vectorize(rule["shell_lines"])
        print("Resulting vector:", v)
        return


#operator_analysis()


def inspection():
    f1 = {}
    n1 = db.rules.count_documents(f1)

    f2 = {"shell_lines": {"$exists": True}}
    n2 = db.rules.count_documents(f2)

    f3 = {"shell_lines": {"$exists": True, "$not": {"$size": 0}}}
    n3 = db.rules.count_documents(f3)

    for rule in db.rules.find({"shell_lines": {"$exists": True, "$size": 0}}):
        for line in rule["lines"]:
            print(line)
        print("-------------------------------------")

    _ = db.rules.find({}).next()
    print("keys:", _.keys())
    print("all rules:", n1)
    print("rules with shell_lines:", n2)
    print("rules with non-empty shell_lines:", n3)


def check_db_status():
    collections = db.db.list_collection_names()
    for col in collections:
        print(col)
        print(db.db[col].stats())

    print("----------------------------")
    db.db.stats()

    exit()


# update_no_content_files()
# run_branching_analysis()

migrate_mongodb()

print("done!")

