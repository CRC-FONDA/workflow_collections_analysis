from db_operations.db_connector import DBConnector
from bson.objectid import ObjectId
import base64

connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
db_name = "git_scraping"
coll_name = "data_v1"
db = DBConnector(connection_string, db_name, coll_name)


def filter():
    data = db.coll.find({"repo": "CambridgeSemiticsLab/Gesenius_data"})
    cnt = 0
    filtered = []
    for x in data:
        print("new data")
        print(x.keys())
        print(x["author"])
        print(x["commit_content"].keys())
        print(x["commit_content"]["files"][0])
        if cnt < 5:
            for xx in x["commit_content"]["files"]:
                if "Snakefile" in xx["filename"] and xx["additions"] == 1 and xx["deletions"] == 1:
                    filtered.append(xx)
        cnt += 1


def output_undo_commits():
    query_result = db.get_snakefile_undo_commits()
    with open("query_outputs/old_queries/old_undo_commits.txt", "w") as f:
        cnt = 0
        for res in query_result:
            f.write(str(cnt) + "., repo: " + res[0][0]["repo"] + ", _id: " + str(res[0][0]["_id"]) + ":\n")
            cnt += 1
            for line in res[0][1]:
                f.write("-" + line + "\n")
            for line in res[0][2]:
                f.write("+" + line + "\n")
            f.write("   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -\n")
            for line in res[1][1]:
                f.write("-" + line + "\n")
            for line in res[1][2]:
                f.write("+" + line + "\n")
            f.write("-------------------------------------------------------------\n")


def output_one_parameter_commits(path):
    query_result = db.get_one_parameter_commits()
    with open(path, "w") as f:
        cnt = 0
        for res in query_result:
            f.write(str(cnt) + "., repo: " + res[0]["repo"] + ", _id: " + str(res[0]["_id"]) + ":\n")
            cnt += 1
            f.write(res[1] + "\n")
            f.write(res[2] + "\n")
            f.write("-------------------------------------------------------------------------\n")


def output_one_rule_commits():
    query_result = db.get_one_rule_commits()
    with open("query_outputs/old_queries/old_one_rule_commits.txt", "w") as f:
        cnt = 0
        for res in query_result:
            f.write(str(cnt) + "., repo: " + res[0]["repo"] + ", _id: " + str(res[0]["_id"]) + ":\n")
            cnt += 1
            for line in res[1]:
                f.write(line + "\n")
            for line in res[2]:
                f.write(line + "\n")
            #f.write(res[1]+"\n")
            #f.write(res[2] + "\n")
            f.write("-------------------------------------------------------------------------\n")

def output_add_del_rule_commits(path):
    results = db.get_add_del_rule_commits()
    with open(path, "w") as f:
        f.write("addition commits:\n")
        for commit in results[0]:
            for line in commit[1]:
                f.write(line+"\n")
            f.write("  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n")
        f.write("-------------------------------------------------------------------------------------\n")
        f.write("delete commits:\n")
        for commit in results[1]:
            for line in commit[1]:
                f.write(line+"\n")
            f.write("  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n")

def count_include_commits():
    cursor = db.coll.find({})
    total_cnt = 0
    include_cnt = 0
    for commit in cursor:
        for file in commit["commit_content"]["files"]:
            try:
                if "nakefile" in file["filename"]:
                    total_cnt += 1
                    b64_content = file["sha_contents"]["content"]
                    content = str(base64.b64decode(b64_content))
                    if "include" in content:
                        include_cnt += 1
                        # lines = content.split("\\n")
                        # for line in lines:
                        #    if "include" in line:
                        #        print(line)
            except:
                pass
        print("total count: " + str(total_cnt))
        print("include count: " + str(include_cnt))

    print("FINAL RESULTS:")
    print("total count: " + str(total_cnt))
    print("include count: " + str(include_cnt))


def no_snakefile_commits():
    cursor = db.coll.find({})
    no_snakefile_cnt = 0
    for commit in cursor:
        no_snakefile = True
        for file in commit["commit_content"]["files"]:
            if "nakefile" in file["filename"]:
                no_snakefile = False
        if no_snakefile:
            no_snakefile_cnt += 1
            print(commit)
    print("RESULT:")
    print(no_snakefile_cnt)

def check_hunks():
    doc = db.coll.find({"_id": ObjectId("630ca3f68f3047851ae474f5")}).next()
    files = doc["commit_content"]["files"]
    for file in files:
        try:
            hunks = file["hunks"]
            for hunk in hunks:
                lines = hunk["hunk_lines"]
                for line in lines:
                    print(line)
        except Exception as e:
            print("------------------------------------------------------------------")
            if not file["patch"]:
                print("NO PATCH!")
            print(e)
            print(file)
            print("------------------------------------------------------------------")

# commit:
# dict_keys(['_id', 'sha', 'node_id', 'commit', 'url', 'html_url', 'comments_url',
#   'author', 'committer', 'parents', 'commit_content', 'standardised', 'repo',
#   'retreived' [or retrieved!!!]])

# commit_content:
# dict_keys(['sha', 'node_id', 'commit', 'url', 'html_url', 'comments_url',
#   'author', 'committer', 'parents', 'stats', 'files'])

# file
# dict_keys(['sha', 'filename', 'status', 'additions', 'deletions', 'changes',
#   'blob_url', 'raw_url', 'contents_url', 'patch', 'sha_contents'])

# get random record
# commit = db.coll.aggregate([{"$sample": {"size": 1}}]).next()

#with open("complete_metadata.txt", "w") as f:
#    for key, value in db.get_top_level_metadata().items():
#        f.write(key+": "+str(value)+"\n")

#data = db.coll.aggregate([
#    {"$match": {"commit_content.files.0.hunks": {"$ne": "null"}}},
#    {"$sample": {"size": 1}}
#])
#
#for commit in data:
#    # print(commit["commit_content"]["files"][0]["hunks"])
#    print(commit["commit_content"]["files"][0].keys())
#    files = commit["commit_content"]["files"]
#    for file in files:
#        print(file.keys())
#    print("----------------------------------------------------")


#commit = db.coll.aggregate([{"$sample": {"size": 1}}]).next()
#sha_content = commit["commit_content"]["files"][0]["sha_contents"]
#file_content = str(base64.b64decode(sha_content["content"]))

#file_content = file_content.split("\\n")

#for line in file_content:
#    print(line)


# check_hunks()


