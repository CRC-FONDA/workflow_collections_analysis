import pandas as pd
from ...utility.parsers.snakefile_parser import iterate_snakefile_lines_with_context, get_rules
from ...db_operations.db_connector import DBConnector
db = DBConnector()


def look_into_rules():
    rules = db.rules.find()
    i = 0
    for rule in rules:
        print(rule.keys())
        if rule["shell_lines"]:
            i += 1
            if i > 5:
                return
            for line in rule["shell_lines"]:
                print(line)
            content = " ".join(line.strip() for line in rule["shell_lines"]).split()
            print("WORDS:", content)
            print("------------------------------------------")


def search_all_repos(path="github_scraping/analysis/full_text/results/"):
    bcftools_lines = []
    bwa_lines = []
    samtool_lines = []
    total_repos = 0
    bcftools_repos = 0
    bwa_repos = 0
    samtool_repos = 0

    full_data = db.final_state.find()
    for repo in full_data:
        total_repos += 1
        print(str(total_repos)+" repo looked at")
        used_bcftools = False
        used_bwa = False
        used_samtool = False
        for filename, file in repo["files"].items():
            if filename not in repo["workflow_files"]:
                continue
            try:
                content = file["content"].split("\\n")
            except Exception as e:
                print("no content for " + repo["repo"] + "/" + filename + ": " + str(e))
                continue
            print("looking at " + filename)
            for i, line, context_key in iterate_snakefile_lines_with_context(content):
                line = line.strip()
                if line.startswith("#") or line.startswith("rule"):
                    continue
                # print(i, context_key, line)
                rule_key = [key for key in context_key if "rule " in key]
                if rule_key:
                    # within a rule
                    if "bcftools" in line:
                        bcftools_lines.append(line)
                        used_bcftools = True
                    if "bwa" in line:
                        bwa_lines.append(line)
                        used_bwa = True
                    if "samtool" in line:
                        samtool_lines.append(line)
                        used_samtool = True
        if used_bcftools:
            bcftools_repos += 1
        if used_bwa:
            bwa_repos += 1
        if used_samtool:
            samtool_repos += 1

    # write out results
    with open(path+"common_tools.txt", "w") as f:
        f.write("total repos: "+str(total_repos)+"\n")
        f.write("repos using bcftools: "+str(bcftools_repos)+"\n")
        f.write("    bcftools occured in rules this many times: "+str(len(bcftools_lines))+"\n")
        f.write("repos using bwa: " + str(bwa_repos) + "\n")
        f.write("    bwa occured in rules this many times: " + str(len(bwa_lines)) + "\n")
        f.write("repos using samtool: " + str(samtool_repos) + "\n")
        f.write("    samtool occured in rules this many times: " + str(len(samtool_lines)) + "\n")

    with open(path+"bcftools_lines.txt", "w") as f:
        for line in bcftools_lines:
            f.write(line+"\n")

    with open(path+"bwa_lines.txt", "w") as f:
        for line in bwa_lines:
            f.write(line+"\n")

    with open(path+"samtool_lines.txt", "w") as f:
        for line in samtool_lines:
            f.write(line+"\n")





def old_search_all_rules():
    print("???")
    # bcftools, bwa, samtool
    bcftools_lines = []
    bwa_lines = []
    samtool_lines = []
    total_repos = 0
    bcftools_repos = 0
    bwa_repos = 0
    samtool_repos = 0
    total_rules = 0
    bcftools_rules = 0
    bwa_rules = 0
    samtool_rules = 0

    print("hi")

    full_data = db.final_state.find()
    for repo in full_data:
        for filename, file in repo["files"].items():
            if filename not in repo["workflow_files"]:
                continue
            try:
                content = file["content"].split("\\n")
            except Exception as e:
                print("no content for "+repo["repo"]+"/"+filename+": "+str(e))
                continue
            print("looking at "+filename)
            for i, line, context_key in iterate_snakefile_lines_with_context(content):
                print(i, context_key, line)
                rule_key = [key for key in context_key if "rule " in key]
                if rule_key:
                    # within a rule
                    new_current_rule = rule_key[0][5:]
                    if new_current_rule != current_rule:
                        if current_rule:
                            # we have completed a rule, collect results
                            pass
                        # starting a new rule
                        rule_executed = False
                        current_rule = new_current_rule
                    else:
                        # not in a rule at all
                        if current_rule:
                            # we have completed a rule, collect results
                            pass

                            current_rule = ""
                            rule_executed = False
                            shell_active = False
                            run_active = False
                            script_active = False
                            wrapper_active = False
                if current_rule:
                    # we have completed a rule, collect results
                    pass

            break

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


def get_operator_domain_map(path_prefix="github_scraping/analysis/operators/", full_text=False):
    od_map = {}
    if full_text:
        data_path = path_prefix + "prepared_data/full_text_operator_categories.csv"
    else:
        data_path = path_prefix + "prepared_data/operator_categories_completed.csv"
    with open(data_path, "r") as f:
        next(f)
        for line in f.readlines():
            k1 = line.rfind(",")
            domain = int(line[k1 + 2:])
            operator = line[:line[:k1].rfind(",")].strip()
            od_map[operator] = domain
    return od_map


def plot_operator_domains_by_workflow(path_prefix="github_scraping/analysis/operators/"):
    f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}

    operator_domain_map = get_operator_domain_map(path_prefix=path_prefix)

    workflow_data = {}
    operator_rules = db.rules.find(f1)
    for rule in operator_rules:
        if rule["repo"] in workflow_data:
            workflow_data[rule["repo"]].append((rule["file"], rule["rule_name"], rule["operators"]))
        else:
            workflow_data[rule["repo"]] = [(rule["file"], rule["rule_name"], rule["operators"])]

    report_data = {}
    total_n_rules = 0
    for repo, rules in workflow_data.items():
        n_rules = 0
        rule_categories = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        for rule in rules:
            operator_categories = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            n_rules += 1
            operators = rule[2]
            for operator in operators:
                try:
                    domain = operator_domain_map[operator]
                except KeyError:
                    continue
                # combine to one other category
                if domain >= 6:
                    domain = 6
                operator_categories[domain] += 1
            for i in range(len(operator_categories)):
                if operator_categories[i] > 0:
                    rule_categories[i] += 1

        report_data[repo] = (n_rules, rule_categories)
        total_n_rules += n_rules

    # put out results:
    print("Data from " + str(len(report_data)) + " workflows and a total number of rules: " + str(total_n_rules))
    print("Average proportion of rules with operators from the following domains by total number of workflow rules:")

    proportion_lists = [[], [], [], [], [], [], [], [], []]
    for n_rules, rule_categories in report_data.values():
        for i in range(len(rule_categories)):
            proportion_lists[i].append(rule_categories[i] / n_rules)

    proportion_averages = [sum(domain_list) / len(domain_list) for domain_list in proportion_lists]

    print("0=domain specific:", proportion_averages[0])
    print("1=control flow:", proportion_averages[1])
    print("2=file content handling:", proportion_averages[2])
    print("3=file handling:", proportion_averages[3])
    print("4=code execution (e.g. conda, python, rscript ..):", proportion_averages[4])
    print("5=data handling (e.g. wget):", proportion_averages[5])
    print("6=misc:", proportion_averages[6])
    print("7=noise:", proportion_averages[7])
    print("8=under 10 count:", proportion_averages[8])


def old_plot_operator_domains_by_workflow(path_prefix="github_scraping/analysis/operators/"):
    f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}

    operator_domain_map = get_operator_domain_map(path_prefix=path_prefix)

    workflow_data = {}
    operator_rules = db.rules.find(f1)
    for rule in operator_rules:
        if rule["repo"] in workflow_data:
            workflow_data[rule["repo"]].append((rule["file"], rule["rule_name"], rule["operators"]))
        else:
            workflow_data[rule["repo"]] = [(rule["file"], rule["rule_name"], rule["operators"])]

    report_data = {}
    total_n_rules = 0
    for repo, rules in workflow_data.items():
        n_rules = 0
        rule_categories = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        for rule in rules:
            n_rules += 1
            operators = rule[2]
            for operator in operators:
                try:
                    domain = operator_domain_map[operator]
                except KeyError:
                    continue
                # combine to one other category
                if domain >= 6:
                    domain = 6
                rule_categories[domain] += 1
        report_data[repo] = (n_rules, rule_categories)
        total_n_rules += n_rules

    # put out results:
    print("Data from " + str(len(report_data)) + " workflows and a total number of rules: " + str(total_n_rules))
    print("Average proportion of rules with operators from the following domains by total number of workflow rules:")

    proportion_lists = [[], [], [], [], [], [], [], [], []]
    for n_rules, rule_categories in report_data.values():
        for i in range(len(rule_categories)):
            proportion_lists[i].append(rule_categories[i] / n_rules)

    proportion_averages = [sum(domain_list) / len(domain_list) for domain_list in proportion_lists]

    print("0=domain specific:", proportion_averages[0])
    print("1=control flow:", proportion_averages[1])
    print("2=file content handling:", proportion_averages[2])
    print("3=file handling:", proportion_averages[3])
    print("4=code execution (e.g. conda, python, rscript ..):", proportion_averages[4])
    print("5=data handling (e.g. wget):", proportion_averages[5])
    print("6=misc:", proportion_averages[6])
    print("7=noise:", proportion_averages[7])
    print("8=under 10 count:", proportion_averages[8])









