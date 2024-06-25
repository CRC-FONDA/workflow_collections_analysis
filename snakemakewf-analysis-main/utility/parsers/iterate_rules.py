from ...db_operations.db_connector import DBConnector
from ...utility.parsers.snakefile_parser import iterate_snakefile_lines_with_context
from ...utility.final_state_utility import iterate_workflow_files, get_file_content

db = DBConnector()


def iterate_all_rules():
    full_data = db.final_state.find()
    for repo in full_data:
        for file, file_name in iterate_workflow_files(repo):
            file_content = get_file_content(file)
            if not file_content:
                continue
            # parsing variables
            current_rule = ""
            rule_executed = False
            shell_active = False
            shell_lines = []
            run_active = False
            run_lines = []
            script_active = False
            script_lines = []
            wrapper_active = False
            wrapper_lines = []

            for i, line, context_key in iterate_snakefile_lines_with_context(file_content):
                # print("("+str(i)+") "+str(context_key)+": "+line)
                rule_key = [key for key in context_key if "rule " in key]  # has to be "rule " because of "ruleorder" keyword
                if rule_key:
                    # within a rule
                    new_current_rule = rule_key[0][5:]
                    if new_current_rule != current_rule:
                        if current_rule:
                            # print("RULE "+ current_rule +" COMPLETE")
                            results = {
                                "repo": repo["repo"],
                                "file_name": file_name,
                                "rule_name": current_rule,
                                "rule_executed": rule_executed,
                                "shell_lines": shell_lines,
                                "run_lines": run_lines,
                                "script_lines": script_lines,
                                "wrapper_lines": wrapper_lines
                            }
                            yield results
                        # starting a new rule
                        rule_executed = False
                        current_rule = new_current_rule

                    if not shell_active and "shell" in context_key:
                        shell_lines = []
                        shell_active = True
                        rule_executed = True
                    if shell_active:
                        if "shell" in context_key:
                            if line.strip():
                                shell_lines.append((i, line))
                        else:
                            shell_active = False
                    if not run_active and "run" in context_key:
                        run_lines = []
                        run_active = True
                        rule_executed = True
                    if run_active:
                        if "run" in context_key:
                            if line.strip():
                                run_lines.append((i, line))
                        else:
                            run_active = False
                    if not script_active and "script" in context_key:
                        script_lines = []
                        script_active = True
                        rule_executed = True
                    if script_active:
                        if "script" in context_key:
                            if line.strip():
                                script_lines.append((i, line))
                        else:
                            script_active = False
                    if not wrapper_active and "wrapper" in context_key:
                        wrapper_lines = []
                        wrapper_active = True
                        rule_executed = True
                    if wrapper_active:
                        if "wrapper" in context_key:
                            if line.strip():
                                wrapper_lines.append((i, line))
                        else:
                            wrapper_active = False

                else:
                    # not in a rule at all
                    if current_rule:
                        # print("RULE " + current_rule + " COMPLETE")
                        results = {
                            "repo": repo["repo"],
                            "file_name": file_name,
                            "rule_name": current_rule,
                            "rule_executed": rule_executed,
                            "shell_lines": shell_lines,
                            "run_lines": run_lines,
                            "script_lines": script_lines,
                            "wrapper_lines": wrapper_lines
                        }
                        yield results
                        current_rule = ""
                        rule_executed = False
                        shell_active = False
                        run_active = False
                        script_active = False
                        wrapper_active = False
            if current_rule:
                # print("RULE " + current_rule + " COMPLETE")
                results = {
                    "repo": repo["repo"],
                    "file_name": file_name,
                    "rule_name": current_rule,
                    "rule_executed": rule_executed,
                    "shell_lines": shell_lines,
                    "run_lines": run_lines,
                    "script_lines": script_lines,
                    "wrapper_lines": wrapper_lines
                }
                yield results


def write_rule_iteration(path, results):
    with open (path, "a") as f:
        f.write("repo: "+results["repo"]+", file: "+results["file_name"]+"\n")
        f.write("rule: "+results["rule_name"] + ", executed: " + str(results["rule_executed"])+"\n")
        f.write("SHELL LINES:\n")
        for l in results["shell_lines"]:
            f.write(str(l)+"\n")
        f.write("RUN LINES:\n")
        for l in results["run_lines"]:
            f.write(str(l)+"\n")
        f.write("SCRIPT LINES:\n")
        for l in results["script_lines"]:
            f.write(str(l) + "\n")
        f.write("WRAPPER LINES:\n")
        for l in results["wrapper_lines"]:
            f.write(str(l) + "\n")
        f.write("-----------------------------------------------------------\n")


def collect_meta_results(result):
    num_shell_lines = len(result["shell_lines"])
    num_run_lines = len(result["run_lines"])
    num_script_lines = len(result["script_lines"])
    num_wrapper_lines = len(result["wrapper_lines"])
    meta_result = [
        1,  # number of rules
        [num_shell_lines],
        [num_run_lines],
        [num_script_lines],
        [num_wrapper_lines],
        1 if (num_shell_lines+num_run_lines+num_script_lines+num_wrapper_lines > 0) else 0,  # rule executed
        1 if len([x for x in [num_shell_lines, num_run_lines, num_script_lines, num_wrapper_lines] if x > 0]) > 1 else 0  # multiple executions rule
    ]
    return meta_result
