from db_operations.db_connector import DBConnector
from hunk_filters import filter_one_parameter, filter_one_rule, filter_input
from collections import defaultdict
import base64

connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
db_name = "git_scraping"
deep_db = DBConnector(connection_string, db_name, "data_v3_small")
output_prefix = "../query_outputs/"
metadata_prefix = "../metadata/"


def get_workflow_files(repo):
    workflow_files = []
    for filename, file in repo["files"].items():
        if "nakefile" in filename:
            workflow_files += recursive_workflow_collect(filename, repo)
    return list(set(workflow_files))


def recursive_workflow_collect(filename, repo):
    try:
        raw_includes = repo["files"][filename]["includes"]
    except KeyError as e:
        candidates = [name for name in repo["files"].keys() if filename in name]
        if not candidates:
            return [filename]
        elif len(candidates) > 1:
            # TODO: hande this exception better
            # raise ValueError('during workflow collection more than one matching file in '+repo["repo"])
            return [filename]
        raw_includes = repo["files"][candidates[0]]["includes"]
    included = [filename]
    if not raw_includes:
        return included
    else:
        includes = get_included_files(raw_includes)
        for file in includes:
            included += recursive_workflow_collect(file, repo)
        return list(set(included))


def get_included_files(include_list):
    files = []
    for item in include_list:
        start = item.find("\"")
        end = item.rfind("\"")
        files.append(item[start+1:end])
    return files


def test_for_workflowfile(test_workflow_files, test_filename):
    for test_file in test_workflow_files:
        if test_filename in test_file:
            return True
    return False


def collect_same_commit_hunks(repo, test_hunk):
    workflow_files = get_workflow_files(repo)
    same_commit_hunks = []
    for filename, file in repo["files"].items():
        if test_for_workflowfile(workflow_files, filename):
            for hunk in file["hunks"]:
                if hunk["old_id"] == test_hunk["old_id"]:
                    same_commit_hunks.append(hunk)
    return same_commit_hunks


def get_one_parameter_hunks():
    repos = deep_db.coll.find({})
    data = defaultdict(list)
    num_one_parameter_hunks = 0
    for repo in repos:
        workflow_files = get_workflow_files(repo)
        for filename, file in repo["files"].items():
            if test_for_workflowfile(workflow_files, filename):
                # The file contains data of a workflow file
                for hunk in file["hunks"]:
                    if hunk["added"] == 1 and hunk["deleted"] == 1:
                        if filter_one_parameter(hunk["hunk_lines"]):
                            num_one_parameter_hunks += 1
                            data[repo["repo"]].append((num_one_parameter_hunks, hunk["hunk_lines"]))
    return data, num_one_parameter_hunks


def write_simple_hunks(path, data, num_hunks):
    with open(path, "w") as f:
        f.write("IN TOTAL "+str(num_hunks)+" HUNKS WERE FOUND.\n")
        f.write("\n")
        for repo, hunks in data.items():
            f.write("REPO: "+str(repo)+"\n")
            for num, hunk in hunks:
                f.write("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n")
                f.write("(HUNK NUM: "+str(num)+")\n")
                for line in hunk:
                    if line[0] == "-" or line[0] == "+":
                        f.write(line+"\n")
            f.write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")


def get_one_rule_hunks():
    repos = deep_db.coll.find({})
    data = defaultdict(list)
    num_one_rule_hunks = 0
    for repo in repos:
        workflow_files = get_workflow_files(repo)
        for filename, file in repo["files"].items():
            if test_for_workflowfile(workflow_files, filename):
                # The file contains data of a workflow file
                for hunk in file["hunks"]:
                    result = filter_one_rule(hunk["hunk_lines"])
                    if result:
                        num_one_rule_hunks += 1
                        data[repo["repo"]].append((num_one_rule_hunks, result[0], hunk["hunk_lines"]))
    return data, num_one_rule_hunks


def write_one_rule_hunks(data, num_hunks):
    path = output_prefix + "workflow/one_rule_hunks.txt"
    add_cnt = 0
    del_cnt = 0
    change_cnt = 0
    with open(path, "w") as f:
        f.write("IN TOTAL "+str(num_hunks)+" ONE RULE HUNKS WERE FOUND.\n")
        f.write("\n")
        for repo, hunks in data.items():
            f.write("REPO: "+str(repo)+"\n")
            for num, result, hunk in hunks:
                # if not result == "del":
                #    continue
                f.write("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n")
                f.write("(HUNK NUM: "+str(num)+" - "+result+") \n")
                for line in hunk:
                    f.write(line+"\n")
                if result == "add":
                    add_cnt += 1
                elif result == "del":
                    del_cnt += 1
                elif result == "change":
                    change_cnt += 1
            f.write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        f.write("added: "+str(add_cnt)+", deleted: "+str(del_cnt)+", changed: "+str(change_cnt)+"\n")


def get_input_hunks():
    # repo crazyhottommy/pyflow_seurat_parameter is a prime example
    repos = deep_db.coll.find({})
    data = defaultdict(list)
    num_input_hunks = 0
    for repo in repos:
        workflow_files = get_workflow_files(repo)
        for filename, file in repo["files"].items():
            if test_for_workflowfile(workflow_files, filename):
                # The file contains data of a workflow file
                for hunk in file["hunks"]:
                    if hunk["added"] != 1 or hunk["deleted"] != 1:
                        continue
                    if filter_input(hunk["hunk_lines"]):
                        num_input_hunks += 1
                        data[repo["repo"]].append((num_input_hunks, hunk["hunk_lines"]))
    return data, num_input_hunks


def test_same_commit_collection(repo_name):
    repo = deep_db.coll.find({"repo": repo_name}).next()
    workflow_files = get_workflow_files(repo)
    hunks = []
    for filename, file in repo["files"].items():
        if test_for_workflowfile(workflow_files, filename):
            for hunk in file["hunks"]:
                hunks.append(hunk)

    for hunk in hunks:
        print(hunk)
    print("----------------------------------------------------------------------")
    commit_hunks = collect_same_commit_hunks(repo, hunks[6])
    for hunk in commit_hunks:
        print(hunk)
    print("done!")


def get_one_line_hunks():
    found_target = 0
    missed_taget = 0
    repos = deep_db.coll.find()
    data = defaultdict(list)
    num_one_parameter_hunks = 0
    count = 0
    for repo in repos:
        # print(repo["repo"])
        #if count < 27:
            # TODO: SKIP for testing
        #    count += 1
        #    continue
        workflow_files = get_workflow_files(repo)
        for filename, file in repo["files"].items():
            if test_for_workflowfile(workflow_files, filename):
                # The file contains data of a workflow file
                for hunk in file["hunks"]:
                    if hunk["added"] == 1 and hunk["deleted"] == 1:
                        # check for context of changed line in file
                        # retrieve full text for this hunk
                        full_doc = deep_db.db["data_v1"].find({
                            "_id": hunk["old_id"]
                        }).next()
                        files = full_doc["commit_content"]["files"]
                        target_file = [f for f in files if f["filename"] == filename]
                        if not target_file or len(target_file) > 1:
                            raise ValueError("hunk is not associated with unique file!")
                        else:
                            target_file = target_file[0]
                        # target_hunk = [h for h in target_file["hunks"] if h["hunk_lines"] == hunk["hunk_lines"]]
                        # if not target_hunk or len(target_hunk) > 1:
                        #     raise ValueError("hunk is not associated with unique hunk!")
                        # else:
                        #     target_hunk = target_hunk[0]
                        content = target_file["sha_contents"]["content"]
                        content = str(base64.b64decode(content)).split("\\n")
                        header = hunk["hunk_lines"][0]
                        # del_lines = [l[1:] for l in hunk["hunk_lines"] if l[0] == "-"]
                        add_lines = [l[1:] for l in hunk["hunk_lines"] if l[0] == "+"]
                        i = header.find("+")
                        j = header[i:].find(",")
                        k = header[i+j:].find("@")
                        context = int(header[i+j+1:i+j+k])

                        try:
                            add_line_index = int(header[i+1:i+j])+(context-5)
                        except:
                            missed_taget += 1
                            continue

                        old_hunks = target_file["hunks"]
                        # print(target_file)

                        def debug_out():
                            print("TARGET HUNK:")
                            for line in hunk["hunk_lines"]:
                                print(line)
                            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                            print("COMMIT HUNKS ON FILE:")
                            for h in old_hunks:
                                for line in h["hunk_lines"]:
                                    print(line)
                                print("    #    #    #    #    #    #    #    #    #")
                            print("############################################################")
                            print("############################################################")
                            print("############################################################")
                            print("PREDICTED CHANGE LOCATION AROUND INDEX: " + str(add_line_index))
                            print(content[add_line_index - 4])
                            print(content[add_line_index - 3])
                            print(content[add_line_index - 2])
                            print(content[add_line_index - 1])
                            print("TARGET (context=" + str(context) + "): " + content[add_line_index])
                            print(content[add_line_index + 1])
                            print(content[add_line_index + 2])
                            print(content[add_line_index + 3])
                            print(content[add_line_index + 4])
                            print("---------------------------------------------------------------")
                            print("---------------------------------------------------------------")
                            print("---------------------------------------------------------------")
                            for line in content:
                                print(line)

                        try:
                            p_t = content[add_line_index]
                            a_l = add_lines[0]
                            if p_t == a_l:
                                found_target += 1
                            else:
                                missed_taget += 1
                            #print(repo["repo"])
                            #print("predicted target and added line:")
                            #print(p_t)
                            #print(a_l)
                            #for line in hunk["hunk_lines"]:
                            #    print(line)
                            #print("  -  -  -  -  -  -  -  -  -  -  -  -")

                        except:
                            missed_taget += 1
    print("found_targets: "+str(found_target))
    print("missed_targets: "+str(missed_taget))
    return data, num_one_parameter_hunks


def one_line_hunks_simple_contextualisation():
    def determine_context(context):
        for context_line in context:
            if context_line.startswith("input:"):
                return 0
            elif context_line.startswith("output:"):
                return 1
            elif context_line.startswith("run:"):
                return 2
            elif context_line.startswith("shell:"):
                return 3
            elif context_line.startswith("params:"):
                return 4
            elif context_line.startswith("wrapper:"):
                return 5
            elif context_line.startswith("rule "):
                return 6
        return 7

    repos = deep_db.coll.find()
    num_one_line_hunks = 0
    context_counts = [0, 0, 0, 0, 0, 0, 0, 0]  # order: input, output, run, shell, params, wrapper, rule_head, unclear
    context_hunks = [[], [], [], [], [], [], [], []]  # order: input, output, run, shell, params, wrapper, rule_head, unclear
    for repo in repos:
        workflow_files = get_workflow_files(repo)
        for filename, file in repo["files"].items():
            if test_for_workflowfile(workflow_files, filename):
                # The file contains data of a workflow file
                for hunk in file["hunks"]:
                    if hunk["added"] == 1 and hunk["deleted"] == 1:
                        # extract prior context from hunk context
                        lines = hunk["hunk_lines"]
                        prior_context = []
                        for line in lines:
                            if line[0] != "-" and line[0] != "+":
                                prior_context.append(line.strip())
                            else:
                                change_line = line[1:].strip().replace("#", "")
                                prior_context.append(change_line)
                                break
                        prior_context.reverse()
                        # determine context
                        context_choice = determine_context(prior_context)
                        num_one_line_hunks += 1
                        context_counts[context_choice] += 1
                        context_hunks[context_choice].append(hunk)
    with open(metadata_prefix+"deep_metadata.txt", "a") as f:
        # order: input, output, run, shell, params, wrapper, rule_head, unclear
        f.write("number of one line hunks: "+str(num_one_line_hunks)+"\n")
        f.write("number of input one line hunks: "+str(context_counts[0])+"\n")
        f.write("number of output one linke hunks: "+str(context_counts[1])+"\n")
        f.write("number of run one linke hunks: " + str(context_counts[2]) + "\n")
        f.write("number of shell one linke hunks: " + str(context_counts[3]) + "\n")
        f.write("number of params one linke hunks: " + str(context_counts[4]) + "\n")
        f.write("number of wrapper one linke hunks: " + str(context_counts[5]) + "\n")
        f.write("number of rule_head one linke hunks: " + str(context_counts[6]) + "\n")
        f.write("number of unclear one linke hunks: " + str(context_counts[7]) + "\n")

    def write_out(context, i):
        with open(output_prefix + "simple_contexts/"+context+".txt", "w") as f:
            for hunk in context_hunks[i]:
                for line in hunk["hunk_lines"]:
                    f.write(line + "\n")
                f.write("  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n")

    write_out("input", 0)
    write_out("output", 1)
    write_out("run", 2)
    write_out("shell", 3)
    write_out("params", 4)
    write_out("wrapper", 5)
    write_out("rule_head", 6)
    write_out("unclear", 7)


def config_change_hunks():
    commit_ids = set()
    hunk_count = 0
    config_commit_ids = set()
    config_hunks = 0

    repos = deep_db.coll.find()
    for repo in repos:
        workflow_files = get_workflow_files(repo)
        for filename, file in repo["files"].items():
            if test_for_workflowfile(workflow_files, filename):
                # The file contains data of a workflow file
                for hunk in file["hunks"]:
                    hunk_count += 1
                    commit_ids.add(hunk["old_id"])
                    for line in hunk["hunk_lines"]:
                        if line[0] == "-" and line[1:].startswith("configfile:"):
                            config_commit_ids.add(hunk["old_id"])
                            config_hunks += 1
                            with open(output_prefix+"lightweight_db/config_hunks.txt", "a") as f:
                                f.write("REPO, FILE: "+repo["repo"]+", "+filename+"\n")
                                for li in hunk["hunk_lines"]:
                                    f.write(li+"\n")
                                f.write("-----------------------------------------------------\n")
    with open(metadata_prefix+"lightweight_db.txt", "a") as f:
        f.write("number of commits: "+str(len(commit_ids))+"\n")
        f.write("number of commits with config change: "+str(len(config_commit_ids))+"\n")
        f.write("number of hunks: "+str(hunk_count)+"\n")
        f.write("number of hunks with config change: "+str(config_hunks)+"\n")


config_change_hunks()
print("done!")
