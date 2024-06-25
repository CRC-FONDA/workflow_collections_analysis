import os
import subprocess
from pymongo import MongoClient
from datetime import datetime

# connection to mongodb database
connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
client = MongoClient(connection_string)
db = client["git_scraping"]
collection = db["workflow_structures_v1"]

# read list of repos
with open("all_repos.txt", "r") as f:
    repo_list = [line.strip() for line in f.readlines()]

error_log = "logs/errors.txt"
clone_log = "logs/clone.txt"
dag_log = "logs/dag.txt"
dryrun_log = "logs/dryrun.txt"
general_log = "logs/general.txt"

for repo in repo_list:
    # check if repo already is in database
    cursor = collection.find({"repo": repo})
    probe = next(cursor, None)
    if probe:
        with open(general_log, "a") as f:
            f.write("repo "+repo+" already in collection\n")
        continue
    
    # create document for new repo
    doc = {
            "repo": repo,
            "scrape_time": datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            }

    repo_suf = repo[repo.find("/"):]
    
    repo_string_replaced = repo.replace("/", "_")
    repo_dir = "repos/"+repo_string_replaced

    subprocess.run(["mkdir", repo_dir])
    
    # clone github repository
    with open(general_log, "a") as f:
        f.write("attempt to clone "+repo+"\n")
    input_string = " "
    try:
        result = subprocess.run(
                ["git", "clone", "https://github.com/"+repo],
                cwd=repo_dir+"/",
                text = True,
                timeout = 600,
                # input = input_string.encode(),
                )
        if result.returncode == 0:
            cloned = True
        else:
            cloned = False
            with open(error_log, "a") as f:
                f.write("for "+repo+" an unknown error occurred during cloning\n")
            with open(clone_log, "a") as f:
                f.write("for "+repo+" an unknown error occurred during cloning\n")
    except Exception as e:
        with open(error_log, "a") as f:
            f.write("for "+repo+": an error occurred during cloning\n")
        with open(clone_log, "a") as f:
            f.write("git clone failed for "+repo+" with exception: "+str(e)+" and standard error: "+result.stderr+"\n")
        cloned = False
    doc["cloned"] = cloned

    # create dag
    if cloned:
        with open(general_log, "a") as f:
            f.write("attempt to create dag for "+repo+"\n")
        # execute snakemake dag run
        try:
            result = subprocess.run(
                    ["snakemake", "--dag"],
                    capture_output = True,
                    text = True,
                    cwd=repo_dir+repo_suf,
                    timeout = 1200,
                    # stdout=subprocess.PIPE,
                    )
            # print("FOR REPO "+repo+" PROCESS RETURNCODE: "+str(result.returncode))
            if result.returncode == 0:
                doc["dag"] = result.stdout
            else:
                doc["dag"] = None
                with open(error_log, "a") as f:
                    f.write("for "+repo+" there was an error at --dag execution\n")
                with open(dag_log, "a") as f:
                    f.write("for "+repo+" there was an error at --dag execution:\n")
                    f.write(result.stderr)
                    f.write("\n")
            with open(repo_dir+"/dag.txt", "w") as f:
                f.write(result.stdout)
                f.write(result.stderr)
                f.write("\n")
        except Exception as e:
            with open(error_log, "a") as f:
                f.write("for "+repo+" there was an error at --dag execution\n")
            with open(dag_log, "a") as f:
                f.write("for "+repo+" there was an error at dag execution: "+str(e)+"\n")
            doc["dag"] = None
        with open(general_log, "a") as f:
            f.write("attempt to create dag pdf for "+repo+"\n")
        try:
            subprocess.run(["snakemake --dag | dot -Tpdf > ../dag.pdf"], cwd=repo_dir+repo_suf, shell=True)
        except Exception as e:
            with open(error_log, "a") as f:
                f.write("dag to pdf failed for "+repo+"\n")
            with open (dag_log, "a") as f:
                f.write("dag to pdf failed for "+repo+" with exception: "+str(e)+"\n")

        # execute snakemake dryrun
        with open(general_log, "a") as f:
            f.write("attempt dryrun for "+repo+"\n")
        try:
            result = subprocess.run(
                    ["snakemake", "-n", "-r"],
                    capture_output = True,
                    text = True,
                    cwd=repo_dir+repo_suf,
                    # stdout=subprocess.PIPE,
                    )
            if result.returncode == 0:
                doc["dryrun"] = result.stdout
            else:
                doc["dryrun"] = None
                with open(error_log, "a") as f:
                    f.write("for "+repo+" there was an error at dryrun execution\n")
                with open(dryrun_log, "a") as f:
                    f.write("for "+repo+" there was an error at dryrun execution:\n")
                    f.write(result.stderr)
                    f.write("\n")
            with open (repo_dir+"/dryrun.txt", "w") as f:
                f.write(result.stdout)
                f.write(result.stderr)
        except Exception as e:
            with open(error_log, "a") as f:
                f.write("for "+repo+" there was an error at dryrun execution\n")
            with open(dag_log, "a") as f:
                f.write("for "+repo+" there was an error at dryrun execution: "+str(e)+"\n")
            doc["dryrun"] = None

    with open(repo_dir+"/metadata.txt", "w") as f:
        f.write("repo: "+repo)

    if os.path.exists(repo_dir+repo_suf):
        subprocess.run(["yes | rm -r "+repo_dir+repo_suf], shell=True)

    # store data in collection document
    with open(general_log, "a") as f:
        f.write("attempt to store document in mongodb for "+repo+"\n")
    try:
        collection.insert_one(doc)
    except Exception as e:
        with open(error_log, "a") as f:
            f.write("document insertion to mongodb failed for repo "+repo+" with exception: "+str(e)+"\n")


