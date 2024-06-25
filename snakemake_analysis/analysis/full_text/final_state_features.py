from bson.objectid import ObjectId
from ...db_operations.db_connector import DBConnector

#connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
#db_name = "git_scraping"
#db = DBConnector(connection_string, db_name, "data_v5_final_repos")

output_prefix = "../query_outputs/data_v5_final_repos"
metadata_path = "github_scraping/analysis/full_text/results/metadata.txt"

from ...db_operations.db_connector import DBConnector
db = DBConnector()


def discover_includes_modules_and_wrappers(path="github_scraping/analysis/full_text/results/", update_collection=False):
    log_path = "github_scraping/analysis/full_text/results/logs/final_repos_includes_modules.log"

    def get_includes_and_modules(content):
        content = content.split("\\n")
        found_includes = 0
        includes = []
        found_modules = 0
        modules = []
        found_wrappers = 0
        wrappers = []

        empty_include = False
        found_module = False
        collect_module = False
        for line in content:
            line_list = line.split()
            if empty_include:
                # we expect an included file in this line, because of empty include in previous line
                includes.append(line)
                empty_include = False
                with open(log_path, "a") as f:
                    f.write("Found empty include. Next line: " + line + "\n")
                continue
            if found_module:
                if line_list[0] == "snakefile:":
                    collect_module = True
                    found_module = False
                    continue
                else:
                    found_module = False
                    with open(log_path, "a") as f:
                        f.write("Found non-standard module: " + line + "\n")
            if collect_module:
                modules.append(line)
                collect_module = False
                with open(log_path, "a") as f:
                    f.write("Found module. Collected line: " + line + "\n")
            if not line_list:
                continue
            if line_list[0] == "include:":
                found_includes += 1
                if line_list[1:]:
                    includes.append(line)
                    with open(log_path, "a") as f:
                        f.write("Found include. Collected line: " + line + "\n")
                else:
                    empty_include = True
            if line_list[0] == "module":
                found_modules += 1
                found_module = True
            if line_list[0] == "wrapper:":
                found_wrappers += 1
        content_result = {
            "found_includes": found_includes,
            "includes": includes,
            "found_modules": found_modules,
            "modules": modules,
            "found_wrappers": found_wrappers,
            "wrappers": wrappers,
        }
        return content_result

    m = str(db.final_state.count_documents({}))
    repos = db.final_state.find()
    include_repos = 0
    total_includes = 0
    module_repos = 0
    total_modules = 0
    wrapper_repos = 0
    total_wrappers = 0

    total_repos = 0
    read_repos = 0
    total_files = 0
    read_files = 0

    for repo in repos:
        read_repo = False
        total_repos += 1
        print("("+str(total_repos)+"/"+m+") repos loaded")
        _id = ObjectId(repo["_id"])
        for filename, file in repo["files"].items():
            total_files += 1
            try:
                content = file["content"]
            except Exception as e:
                with open(log_path, "a") as f:
                    f.write("Failed to find content for "+filename+" in repo "+repo["repo"]+"\n")
                continue
            # try to resolve includes and modules
            if not read_repo:
                read_repos += 1
                read_repo = True
            read_files += 1
            try:
                result = get_includes_and_modules(content)
                if result["found_includes"] > 0:
                    include_repos += 1
                total_includes += result["found_includes"]
                if result["found_modules"] > 0:
                    module_repos += 1
                total_modules += result["found_modules"]
                if result["found_wrappers"] > 0:
                    wrapper_repos += 1
                total_wrappers += result["found_wrappers"]
                if update_collection:
                    sub_doc_url = "files." + filename + ".includes"
                    db.coll.update_one(
                        {"_id": _id},
                        {"$set": {sub_doc_url: result["includes"]}}
                    )
                    sub_doc_url = "files." + filename + ".modules"
                    db.coll.update_one(
                        {"_id": _id},
                        {"$set": {sub_doc_url: result["modules"]}}
                    )
                    with open(log_path, "a") as f:
                        f.write("Successfully updated file "+filename+" in repo "+repo["repo"]+"\n")
            except Exception as e:
                with open(log_path, "a") as f:
                    f.write("Failed to update file "+filename+" in repo "+repo["repo"])
                    f.write(" with error: " + str(e) + "\n")

    with open(path + "includes_modules_wrappers.txt", "w") as f:
        f.write("total repos: " + str(total_repos) + "\n")
        f.write(
            "read repos: " + str(read_repos) + ", ratio (read/total repos): " + str(read_repos / total_repos) + "\n")
        f.write("total files: " + str(total_files) + ", ratio (total files/total repos): " + str(
            total_files / total_repos) + "\n")
        f.write("read files: " + str(read_files) + ", ratio (read files/read repos): " + str(read_files / read_repos) +
                ", ratio (read files/total_files): " + str(read_files / total_files) + "\n\n")

        f.write("number of repos with includes: " + str(include_repos) + "\n")
        f.write("number of include insertions: " + str(total_includes) + "\n")
        f.write("number of repos with modules: " + str(module_repos) + "\n")
        f.write("number of module insertions: " + str(total_modules) + "\n")
        f.write("number of repos with wrappers: " + str(wrapper_repos) + "\n")
        f.write("number of wrapper insertions: " + str(total_wrappers) + "\n")


def resolve_includes():
    repos = db.coll.find()
    resolved_includes = 0
    count = 0
    for repo in repos:
        _id = ObjectId(repo["_id"])
        workflow_files = collect_workflow_files(repo)
        sub_doc_url = "workflow_files"
        db.coll.update_one(
            {"_id": _id},
            {"$set": {sub_doc_url: workflow_files}}
        )
        resolved_includes += (len(workflow_files) - 1)
        print(count)
        count += 1
        print(workflow_files)
    print(resolved_includes)
    with open(metadata_path, "a") as f:
        f.write("resolved includes: "+str(resolved_includes)+"\n")


def get_included_files(include_list):
    files = []
    for item in include_list:
        start = item.find("\"")
        end = item.rfind("\"")
        files.append(item[start+1:end])
    return files


def collect_workflow_files(repo):
    workflow_files = set()
    for filename, file in repo["files"].items():
        if "nakefile" in filename:
            workflow_files.update(recursive_workflow_collect(filename, repo))
    return list(workflow_files)


def recursive_workflow_collect(filename, repo):
    included = {filename}
    try:
        # included filename is identical to a file_key in repo files dictionary
        raw_includes = repo["files"][filename]["includes"]
    except KeyError as e:
        # we have to look through the files in the repo to find a match for included filename
        candidates = [name for name in repo["files"].keys() if filename in name]
        if not candidates:
            return included
        elif len(candidates) > 1:
            # TODO: hande this exception better
            # raise ValueError('during workflow collection more than one matching file in '+repo["repo"])
            print("could not identify unique included file for "+repo["repo"]+": "+filename)
            return included
        try:
            raw_includes = repo["files"][candidates[0]]["includes"]
        except Exception as e:
            print(candidates[0]+" has no associated included files: "+str(e))
            return included
    if not raw_includes:
        return included
    else:
        includes = get_included_files(raw_includes)
        for file in includes:
            included.update(recursive_workflow_collect(file, repo))
        return included


def workflow_fulltext_search(path="github_scraping/analysis/full_text/results/", write_examples=False, read_all_files=False):
    total_repos = 0
    read_repos = 0
    total_files = 0
    read_files = 0

    subworkflow_repos = set()
    subworkflow_count = 0
    subworkflow_lines = []
    configfile_repos = set()
    configfile_count = 0
    configfile_lines = []
    inputfunc_repos = set()
    inputfunc_count = 0
    inputfunc_lines = []
    checkpoint_repos = set()
    checkpoint_count = 0
    checkpoint_lines = []
    notebook_repos = set()
    notebook_count = 0
    notebook_calls = 0
    notebook_lines = []
    notebook_examples = []
    out_subworkflows = output_prefix+"/fulltext_search/subworkflows.txt"
    out_configfiles = output_prefix + "/fulltext_search/configfiles.txt"
    out_inputfunc = output_prefix + "/fulltext_search/inputfunc.txt"
    out_checkpoints = output_prefix + "/fulltext_search/checkpoints.txt"

    def write_out(path, repo, filename, line):
        with open(path, "a") as f:
            f.write("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  \n")
            f.write("repo: "+repo+"\n")
            f.write("file: " + filename + "\n")
            f.write("line: "+str(line)+"\n")

    total_docs = str(db.final_state.count_documents({}))
    repos = db.final_state.find()
    doc_count = 0
    for repo in repos:
        notebooks_in_repo = 0
        repo_notebook_lines = []
        doc_count += 1
        print("("+str(doc_count)+"/"+total_docs+") repo docs loaded")
        read_repo = False
        total_repos += 1
        for filename, file in repo["files"].items():
            if not read_all_files:
                if filename not in repo["workflow_files"]:
                    continue
            total_files += 1
            try:
                content = file["content"].split("\\n")
            except Exception as e:
                if write_examples:
                    with open(output_prefix+"/fulltext_search/no_content.txt", "a") as f:
                        f.write("no content for "+repo["repo"]+"/"+filename+": "+str(e)+"\n")
                else:
                    print("no content for "+repo["repo"]+"/"+filename+": "+str(e))
                continue
            if not read_repo:
                read_repos += 1
                read_repo = True
            read_files += 1
            # booleans for parsing:
            input_context = False
            i = 0
            for line in content:
                i += 1
                # subworkflow usage
                if line.strip().startswith("subworkflow"):
                    subworkflow_repos.add(repo["repo"])
                    subworkflow_count += 1
                    subworkflow_lines.append(line)
                    if write_examples:
                        write_out(out_subworkflows, repo["repo"], filename, line)
                # config files
                if line.strip().startswith("configfile"):
                    configfile_repos.add(repo["repo"])
                    configfile_count += 1
                    configfile_lines.append(line)
                    if write_examples:
                        write_out(out_configfiles, repo["repo"],filename,  line)
                # input functions
                func_candidate = None
                if "input:" in line and line.strip()[-1] == ":":
                    input_context = True
                elif "input:" in line and "\"" not in line:
                    p = line.find(":")
                    func_candidate = line[p+1:].strip()
                elif input_context and "\"" not in line:
                    p = line.find("(")
                    func_candidate = line[:p].strip()
                if input_context:
                    input_context = False
                if func_candidate is not None:
                    for func_line in content:
                        if "def "+ func_candidate in func_line:
                            inputfunc_repos.add(repo["repo"])
                            inputfunc_count += 1
                            inputfunc_lines.append((line, func_line))
                            if write_examples:
                                write_out(out_inputfunc, repo["repo"],filename, (line, func_line))
                            break
                # checkpoints
                if line.strip().startswith("checkpoint"):
                    checkpoint_repos.add(repo["repo"])
                    checkpoint_count += 1
                    checkpoint_lines.append(line)
                    if write_examples:
                        write_out(out_checkpoints, repo["repo"], filename, line)
                # notebook
                if line.strip().startswith("notebook"):
                    notebook_repos.add(repo["repo"])
                    notebook_count += 1
                    notebook_lines.append(line)
                    notebooks_in_repo += 1
                    repo_notebook_lines.append((filename, i, line))
                    if line.strip().startswith("notebook:"):
                        notebook_calls += 1
                    if write_examples:
                        write_out(out_checkpoints, repo["repo"], filename, line)
        # collect notebook examples
        if notebooks_in_repo > 0:
            notebook_examples.append((
                repo["repo"],
                notebooks_in_repo,
                repo_notebook_lines
            ))
    # put out meta-results
    if read_all_files:
        out_path = path + "feature_usage_all_files.txt"
    else:
        out_path = path + "feature_usage.txt"
    with open(out_path, "w") as f:
        f.write("total repos: "+str(total_repos)+"\n")
        f.write("read repos: "+str(read_repos)+", ratio (read/total repos): "+str(read_repos/total_repos)+"\n")
        f.write("total files: "+str(total_files)+", ratio (total files/total repos): "+str(total_files/total_repos)+"\n")
        f.write("read files: "+str(read_files)+", ratio (read files/read repos): "+str(read_files/read_repos)+
                ", ratio (read files/total_files): "+str(read_files/total_files)+"\n\n")

        f.write("number of repos with subworkflows: " + str(len(subworkflow_repos)) + "\n")
        f.write("number of subworkflow insertions: " + str(subworkflow_count) + "\n")
        f.write("number of repos with configfiles: " + str(len(configfile_repos)) + "\n")
        f.write("number of configfile insertions: " + str(configfile_count) + "\n")
        f.write("number of repos with inputfunc: " + str(len(inputfunc_repos)) + "\n")
        f.write("number of inputfunc insertions: " + str(inputfunc_count) + "\n")
        f.write("number of repos with checkpoint: " + str(len(checkpoint_repos)) + "\n")
        f.write("number of checkpoint insertions: " + str(checkpoint_count) + "\n")
        f.write("number of repos with notebooks: " + str(len(notebook_repos)) + "\n")
        f.write("number of notebook mentions: " + str(notebook_count) + "\n")
        f.write("number of notebook calls: " + str(notebook_calls) + "\n")

        f.write("\nexamples of notebook repos (repo, notebook-count; filename, line number, notebook-line:\n")
        notebook_examples.sort(key=lambda _x: _x[1], reverse=True)
        for example in notebook_examples:
            f.write(example[0]+", "+str(example[1])+"\n")
            for line in example[2]:
                f.write("    "+str(line)+"\n")


def snakefile_fulltext_search():
    out_snakefile = output_prefix + "/fulltext_search/snakefile.txt"
    config_snakefiles = set()
    num_snakefiles = 0
    num_config = 0

    def write_out(path, repo, filename, line):
        with open(path, "a") as f:
            f.write("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  \n")
            f.write("repo: "+repo+"\n")
            f.write("file: " + filename + "\n")
            f.write("line: "+str(line)+"\n")

    repos = db.coll.find()
    for repo in repos:
        for filename in repo["workflow_files"]:
            if "nakefile" in filename:
                num_snakefiles += 1
                try:
                    content = repo["files"][filename]["content"].split("\\n")
                except Exception as e:
                    with open(output_prefix + "/fulltext_search/no_content.txt", "a") as f:
                        f.write("no content for " + repo["repo"] + "/" + filename + ": " + str(e) + "\n")
                    continue
                for line in content:
                    # config files
                    if line.strip().startswith("configfile"):
                        config_snakefiles.add(repo["repo"]+"/"+filename)
                        num_config += 1
                        write_out(out_snakefile, repo["repo"], filename, line)
    with open(metadata_path, "a") as f:
        f.write("number of snakefiles: " + str(num_snakefiles) + "\n")
        f.write("number of snakefiles with configfiles: " + str(len(config_snakefiles)) + "\n")
        f.write("number of configs in snakefiles: " + str(num_config) + "\n")


def out_of_rule_controlflow():
    repos = db.coll.find()
    files_with_controlflow = 0
    files_with_leftmost_controlflow = 0
    num_workflow_files = 0
    for repo in repos:
        for filename in repo["workflow_files"]:
            num_workflow_files += 1
            try:
                content = repo["files"][filename]["content"].split("\\n")
            except Exception as e:
                with open(output_prefix+"/fulltext_search/no_content.txt", "a") as f:
                    f.write("no content for "+repo["repo"]+"/"+filename+": "+str(e)+"\n")
                continue

            def get_indentation(indented_line):
                tabs = indented_line.count("\t")
                indented_line = indented_line.replace("\t", "")
                spaces = len(indented_line) - len(indented_line.lstrip())
                return spaces, tabs

            # booleans for parsing:
            rule_context = False
            case_check = False
            immediate_rule = False
            drag = 0
            left_drag = 0
            rule_context_indentation = (0, 0)  # (spaces, tabs)

            control_lines = []
            leftmost_control_lines = []
            line_count = 0

            for line in content:
                line_count += 1
                line_count_str = str(line_count) + ": "
                line_count_str = f"{line_count_str:>5}"
                line_indentation = get_indentation(line)

                if not rule_context and line.strip().startswith("rule "):
                    rule_context = True
                    rule_context_indentation = line_indentation
                    continue
                if rule_context and not line.strip():
                    rule_context = False
                    continue
                if rule_context and (line_indentation[0]<rule_context_indentation[0] or line_indentation[1]<rule_context_indentation[1]):
                    rule_context = False

                if not rule_context and line.strip().startswith("if"):
                    case_check = True
                    control_lines.append(line_count_str+line)
                    drag = 3
                    if line_indentation == (0, 0):
                        leftmost_control_lines.append(line_count_str+line)
                        left_drag = 3
                    continue
                elif not rule_context and line.strip().startswith("elif"):
                    case_check = True
                    control_lines.append(line_count_str+line)
                    drag = 3
                    if line_indentation == (0, 0):
                        leftmost_control_lines.append(line_count_str+line)
                        left_drag = 3
                    continue
                elif not rule_context and line.strip().startswith("else"):
                    case_check = True
                    control_lines.append(line_count_str+line)
                    drag = 3
                    if line_indentation == (0, 0):
                        leftmost_control_lines.append(line_count_str+line)
                        left_drag = 3
                    continue
                if drag > 0:
                    control_lines.append(line_count_str + line)
                    drag -= 1
                if left_drag > 0:
                    leftmost_control_lines.append(line_count_str + line)
                    left_drag -= 1
                if case_check and "rule " in line:
                    immediate_rule = True
                case_check = False

            if control_lines:
                files_with_controlflow += 1
                with open(output_prefix+"/controlflow/controlflow.txt", "a") as f:
                    f.write("("+str(files_with_controlflow)+") "+repo["repo"]+", "+filename+"\n")
                    for line in control_lines:
                        f.write(line+"\n")
                    f.write(("-----------------------------------------------------------------------------\n"))

            if control_lines and immediate_rule:
                with open(output_prefix + "/controlflow/rules.txt", "a") as f:
                    f.write("REPO, FILE: " + repo["repo"] + ", " + filename + "\n")
                    for line in control_lines:
                        f.write(line + "\n")
                    f.write(("-----------------------------------------------------------------------------\n"))
                break

            if leftmost_control_lines:
                files_with_leftmost_controlflow += 1
                with open(output_prefix+"/controlflow/leftmost.txt", "a") as f:
                    f.write("REPO, FILE: "+repo["repo"]+", "+filename+"\n")
                    for line in leftmost_control_lines:
                        f.write(line+"\n")
                    f.write(("-----------------------------------------------------------------------------\n"))

    # put out meta-results
    with open(metadata_path, "a") as f:
        f.write("number of workflow files: "+str(num_workflow_files)+"\n")
        f.write("number of files with out of rule controlflow: "+str(files_with_controlflow)+"\n")
        f.write("number of files with leftmost controlflow: " + str(files_with_controlflow) + "\n")


def collect_metadata():
    path = "../../metadata/final_state_metadata.txt"
    data = db.coll.find({})
    for item in data:
        pass
