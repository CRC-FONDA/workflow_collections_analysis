from utility.final_state_utility import iterate_workflow_files, get_file_content
from utility.parsers.snakefile_parser import (
    iterate_snakefile_lines_with_context,
    get_indentation,
)


def scan_all_contexts(results_prefix, meta_path):
    from db_operations.db_connector import DBConnector
    db = DBConnector()
    # codes for meta results:
    # case 0: shell
    # case 1: generic rule
    # case 2: input function
    # case 3: generic no rule
    # sub-case 1: 0: config
    #             1: no config
    # sub-case 2: 0: lines > 1
    #             1: lines == 1
    meta_results = [[[0, 0], [0, 0]],   # shell
                    [[0, 0], [0, 0]],   # generic rule
                    [[0, 0], [0, 0]],   # input function
                    [[0, 0], [0, 0]]]   # generic no rule
    for repo in db.final_state.find():
        for wf_file, wf_file_name in iterate_workflow_files(repo):
            content = get_file_content(wf_file)
            if content:
                contexts = get_contexts_from_content(repo["repo"], wf_file_name, content)
                for context in contexts:
                    case, sc1, sc2 = analyse_and_book_context(context, results_prefix)
                    meta_results[case][sc1][sc2] += 1
    write_meta_results(meta_path, meta_results)


def write_meta_results(meta_path, meta_results):
    with open(meta_path, "a") as f:
        total_contexts = 0
        for l1 in meta_results:
            for l2 in l1:
                total_contexts += sum(l2)
        f.write("CONDITIONAL CONTEXTS:\n")
        f.write("total number of contexts: "+str(total_contexts)+"\n")
        for mlist in meta_results:
            f.write(str(mlist)+"\n")



def get_contexts_from_content(repo_name, file_name, content):
    def initial_context(prefix, key_list):
        for i in range(len(key_list)+1):
            if prefix == key_list[:i]:
                return True
        return False

    contexts = []
    current_context = []
    context_lines_list = []
    active_context = False
    for index, line, context_key in iterate_snakefile_lines_with_context(content):
        # print(str(context_key) + "LINE: ("+str(index)+") "+line)
        if active_context:
            # print("INITIAL_CONTEXT = "+str(initial_context(current_context, context_key)))
            if initial_context(current_context, context_key):
                context_lines_list.append((index, line))
            else:
                # print("DEBUG: ADDING NEW CONTEXT!")
                new_context = {
                    "repo_name": repo_name,
                    "file_name": file_name,
                    "context_key": current_context,
                    "lines": context_lines_list,
                    "content": content,
                }
                contexts.append(new_context)
                context_lines_list = []
                active_context = False
        if not active_context:
            if any("if " in key or "else " in key or "elif " in key for key in context_key):
                current_context = context_key
                active_context = True
                context_lines_list = [(index, line)]
    if context_lines_list:
        new_context = {
            "repo_name": repo_name,
            "file_name": file_name,
            "context_key": current_context,
            "lines": context_lines_list,
            "content": content,
        }
        contexts.append(new_context)
    return contexts


def analyse_and_book_context(context, results_prefix):
    def write_context(path, context_to_write):
        with open(path, "a") as f:
            f.write("repo=" + context_to_write["repo_name"] + ", file=" + context_to_write["file_name"] + "\n")
            f.write("context_key: " + str(context_to_write["context_key"]) + "\n")
            for line in context_to_write["lines"]:
                f.write("    " + str(line) + "\n")
            f.write("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  \n\n")

    context_key = context["context_key"]
    rule = False
    shell = False
    config = False
    for key in context_key:
        if "rule" in key:
            rule = True
        if "shell" in key:
            shell = True
        if "if config" in key:
            config = True
        if "if " in key or "elif " in key or "else " in key:
            if shell:
                if config:
                    write_context(results_prefix+"shell_config.txt", context)
                    if len(context["lines"]) > 1:
                        return 0, 0, 0
                    else:
                        return 0, 0, 1
                else:
                    write_context(results_prefix + "shell.txt", context)
                    if len(context["lines"]) > 1:
                        return 0, 1, 0
                    else:
                        return 0, 1, 1
            elif rule:
                if config:
                    write_context(results_prefix+"rule_config.txt", context)
                    if len(context["lines"]) > 1:
                        return 1, 0, 0
                    else:
                        return 1, 0, 1
                else:
                    write_context(results_prefix + "rule.txt", context)
                    if len(context["lines"]) > 1:
                        return 1, 1, 0
                    else:
                        return 1, 1, 1
            else:
                context_index, line = context["lines"][0]
                content = context["content"]
                indentation = get_indentation(line)
                index = context_index
                while index > 0:
                    new_line = content[index]
                    if new_line.strip().startswith("def "):
                        new_context_lines = []
                        for i in range(index, context_index):
                            new_context_lines.append((i, content[i]))
                        context["lines"] = new_context_lines + context["lines"]
                        if config:
                            write_context(results_prefix + "input_function_config.txt", context)
                            return 2, 0, 0
                        else:
                            write_context(results_prefix + "input_function.txt", context)
                            return 2, 1, 0

                    if "rule " in new_line:
                        break
                    index -= 1

                if config:
                    write_context(results_prefix + "no_rule_config.txt", context)
                    if len(context["lines"]) > 1:
                        return 3, 0, 0
                    else:
                        return 3, 0, 1
                else:
                    write_context(results_prefix + "no_rule.txt", context)
                    if len(context["lines"]) > 1:
                        return 3, 1, 0
                    else:
                        return 3, 1, 1

    # codes for meta results:
    # case 0: shell
    # case 1: generic rule
    # case 2: input function
    # case 3: generic no rule
    # sub-case 1: 0: config
    #             1: no config
    # sub-case 2: 0: lines > 1
    #             1: lines == 1







# deprecated function: now different classification cases
def old_analyse_and_book_context(context, results_prefix):
    context_key = context["context_key"]
    rule = False
    for key in context_key:
        if "rule" in key:
            rule = True
        if "if " in key or "elif " in key or "else " in key:
            if rule:
                with open(results_prefix + "in_rule.txt", "a") as f:
                    f.write("repo="+context["repo_name"]+", file="+context["file_name"]+"\n")
                    f.write("context_key: "+str(context["context_key"])+"\n")
                    for line in context["lines"]:
                        f.write("    "+str(line)+"\n")
                    f.write("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  \n\n")
            else:
                with open(results_prefix + "no_rule.txt", "a") as f:
                    f.write("repo="+context["repo_name"]+", file="+context["file_name"]+"\n")
                    f.write("context_key: "+str(context["context_key"])+"\n")
                    for line in context["lines"]:
                        f.write("    " + str(line) + "\n")
                    f.write("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  \n\n")
        if "if config" in key:
            with open(results_prefix + "if_config.txt", "a") as f:
                f.write("repo=" + context["repo_name"] + ", file=" + context["file_name"] + "\n")
                f.write("context_key: " + str(context["context_key"]) + "\n")
                for line in context["lines"]:
                    f.write("    " + str(line) + "\n")
                f.write("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  \n\n")
    return


# deprecated function that assumes a context change at change of context key
# problem: nested contexts cut each other apart
def old_get_context_from_content(repo_name, file_name, content):
    contexts = []
    current_context = None
    context_lines_list = []
    for index, line, context_key in iterate_snakefile_lines_with_context(content):
        if any("if " in key or "else " in key or "elif " in key for key in context_key):
            if context_key != current_context:
                if not context_lines_list:
                    current_context = context_key
                    context_lines_list = [(index, line)]
                else:
                    context = {
                        "repo_name": repo_name,
                        "file_name": file_name,
                        "context_key": current_context,
                        "lines": context_lines_list,
                    }
                    contexts.append(context)
                    current_context = context_key
                    context_lines_list = [(index, line)]
            else:
                context_lines_list.append((index, line))
    if context_lines_list:
        context = {
            "repo_name": repo_name,
            "file_name": file_name,
            "context_key": current_context,
            "lines": context_lines_list,
        }
        contexts.append(context)
    return contexts


