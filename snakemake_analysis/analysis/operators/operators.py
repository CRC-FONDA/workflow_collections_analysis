import re
import matplotlib.pyplot as plt
from .common_tools import plot_operator_domains_by_workflow, get_operator_domain_map
from ...db_operations.db_connector import DBConnector
db = DBConnector()


def iterate_shell_rules():
    rules = db.rules.find()
    for rule in rules:
        if rule["shell_lines"]:
            yield rule


def get_config_file(rule):
    repo = db.final_state.find({"repo": rule["repo"]}).next()
    config_files = [f for f in repo["files"].keys() if "config" in f[f.rfind("/"):]]
    return [(f, repo["files"][f]["content"]) for f in config_files if "content" in repo["files"][f]]


def get_operators(shell_lines):
    def clean_line(raw_line):
        for pattern in ["\\\'", "\\\\", '\"', '\'']:
            if pattern in raw_line:
                raw_line = raw_line.replace(pattern, "")
        return raw_line.strip()

    delimiters = "|", ">", ">>", "<", "<<"
    regex_pattern = '|'.join(map(re.escape, delimiters))
    operator_candidates = []
    for line in shell_lines:
        operator_candidates += [clean_line(_line).split(" ")[0] for _line in re.split(regex_pattern, line)]
    operators = [o for o in operator_candidates if len(o) > 0 and o != "shell:" and not o[0] in "#{-"]
    return operators


def update_rule_collection_with_operators():
    # number of total shell rules
    n_shell_rules = str(db.rules.count_documents({"shell_lines": {"$exists": True, "$not": {"$size": 0}}}))
    print("n_shell_rules:", n_shell_rules)
    i = 0
    for rule in iterate_shell_rules():
        i += 1
        print(str(i) + "/" + n_shell_rules)
        operators = get_operators(rule["shell_lines"])
        # update operators
        db.rules.find_one_and_update(
            {"_id": rule["_id"]},
            {"$set": {"operators": operators}}
        )


def clean_operator_entries():
    f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}
    for rule in db.rules.find(f1):
        operators = [operator[1:] if len(operator) > 1 and operator[0] == "(" else operator for operator in rule["operators"]]
        db.rules.find_one_and_update(
            {"_id": rule["_id"]},
            {"$set": {"operators": operators}}
        )


def update_rule_collection_with_config_operator_entries():
    f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}

    n = str(db.rules.count_documents(f1))
    i = 0
    for rule in db.rules.find(f1):
        i += 1
        print(str(i) + "/" + n)
        # construct operator pattern
        operators = rule["operators"]
        if not operators:
            continue
        valid_operators = []
        for operator in operators:
            try:
                re.compile(operator)
                valid_operators.append(operator)
            except re.error:
                print(operator + " is not a valid regex pattern")
                continue
        operator_pattern = "(" + "|".join(valid_operators) + ")"

        rule_matches = {}

        # match operators in config files if possible
        config_files = get_config_file(rule)
        if config_files:
            for file_name, content in config_files:
                processed_matches = []
                matches = re.finditer(operator_pattern, content)
                if matches:
                    match = next(matches, None)
                    while match:
                        processed_matches.append((match.group(), match.span()))
                        # print("processed_matches:", processed_matches)
                        #print(match)
                        #print("span", type(match.span()), match.span())
                        #print("group", match.group())
                        #left = content.rfind("\\n", 0, match.span()[0])
                        #left = 0 if left == -1 else left
                        #right = content.find("\\n", match.span()[1])
                        #right = len(content) if right == -1 else right
                        #matched_line = content[left:right]
                        #print("matches_line:", matched_line)

                        match = next(matches, None)
                if processed_matches:
                    # print(type(file_name), file_name, processed_matches)
                    rule_matches[file_name] = processed_matches
                    # print("rule_matches:", rule_matches)
        if len(rule_matches) > 0:
            print("Found matches:", rule_matches)
            db.rules.find_one_and_update(
                {"_id": rule["_id"]},
                {"$set": {"config_operator_matches": rule_matches}}
            )


def get_operators_overview(path_prefix="github_scraping/analysis/operators/results/", f=None):
    #x = db.rules.find({}).next()
    #print(x.keys())
    #return
    if not f:
        f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}
    else:
        f1 = f

    n0 = db.rules.count_documents({})
    n1 = db.rules.count_documents(f1)
    # print(n0, n1)

    operator_domain_map = get_operator_domain_map(path_prefix="github_scraping/analysis/operators/")
    operators_total = dict()
    operators_by_repo = dict()
    operators_by_rule = dict()
    aggregate_count = dict()
    for i in range(9):
        aggregate_count[i] = [set(), set(), 0]

    for rule in db.rules.find(f1):
        # print(rule["operators"])
        for operator in rule["operators"]:
            if operator in operators_total:
                operators_total[operator] += 1
            else:
                operators_total[operator] = 1
            if operator in operators_by_repo:
                operators_by_repo[operator].add(rule["repo"])
            else:
                operators_by_repo[operator] = {rule["repo"]}
            if operator in operators_by_rule:
                operators_by_rule[operator].add((rule["repo"], rule["file"], rule["rule_name"]))
            else:
                operators_by_rule[operator] = {(rule["repo"], rule["file"], rule["rule_name"])}
            try:
                domain = operator_domain_map[operator]
            except KeyError:
                continue
            # combine to one other domain
            if domain >= 6:
                domain = 6
            aggregate_count[domain][0].add(rule["repo"])
            aggregate_count[domain][1].add((rule["repo"], rule["file"], rule["rule_name"]))
            aggregate_count[domain][2] += 1

    operators_total_list = [(key, value) for key, value in operators_total.items()]
    operators_total_list.sort(key=lambda x: x[1], reverse=True)
    operators_by_repo_list = [(key, len(value)) for key, value in operators_by_repo.items()]
    operators_by_repo_list.sort(key=lambda x: x[1], reverse=True)
    operators_by_rule_list = [(key, len(value)) for key, value in operators_by_rule.items()]
    operators_by_rule_list.sort(key=lambda x: x[1], reverse=True)

    operators_data_list = [(operator, len(repo_set), len(operators_by_rule[operator]), operators_total[operator]) for operator, repo_set in operators_by_repo.items()]
    operators_data_list.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)

    with open(path_prefix + "operator_counts.csv", "w") as f:
        f.write("operator, count by repo, count by rule, total count\n")
        for operator, count_by_repo, count_by_rule, total_count in operators_data_list:
            f.write(operator + ", " + str(count_by_repo) + ", " + str(count_by_rule) + ", " + str(total_count) + "\n")

    # write out domain specific (bioinformatics) operators
    with open(path_prefix + "operator_counts_bioinformatics.csv", "w") as f:
        f.write("operator, count by repo, count by rule, total count\n")
        for operator, count_by_repo, count_by_rule, total_count in operators_data_list:
            try:
                domain = operator_domain_map[operator]
            except KeyError:
                continue
            # print(operator, domain)
            if domain == 0:
                f.write(operator + ", " + str(count_by_repo) + ", " + str(count_by_rule) + ", " + str(total_count) + "\n")

    # write out aggregate counts
    with open(path_prefix + "operator_counts_aggregate.csv", "w") as f:
        f.write("domain, count by repo, count by rule, total count\n")
        domains = ["Bioinformatics", "Control flow", "File processing", "File system", "Code execution",
                   "Data handling", "Misc", "Noise", "under 10"]
        for i in range(9):
            f.write(domains[i] + ", " + str(len(aggregate_count[i][0])) + ", " + str(len(aggregate_count[i][1]))
                    + ", " + str(aggregate_count[i][2]) + "\n")


def get_config_operator_matches_overview(path="github_scraping/analysis/operators/results/"):
    f1 = {"config_operator_matches": {"$exists": True}}
    # n0 = db.rules.count_documents({})
    n1 = str(db.rules.count_documents(f1))
    # print(n0, n1)

    operator_matches = {}
    n_matches = 0
    cleared_matches = set()
    i = 0
    for rule in db.rules.find(f1):
        i += 1
        print(str(i) + "/" + n1)
        matches_in_rule = []
        for config_file, matches in rule["config_operator_matches"].items():
            for match in matches:
                # skip operators of length 0, 1 or 2 as noise in data
                if len(match[0]) < 3:
                    continue
                # collect count for matched operators
                if match[0] in operator_matches:
                    operator_matches[match[0]] += 1
                else:
                    operator_matches[match[0]] = 1
                matches_in_rule.append((config_file, match))

        # get matched config file
        if matches_in_rule:
            config_files = dict(get_config_file(rule))
            for config_file_name, match in matches_in_rule:
                content = config_files[config_file_name]

                # print(match)
                # print("span", type(match.span()), match.span())
                # print("group", match.group())
                left = content.rfind("\\n", 0, match[1][0])
                left = 0 if left == -1 else left
                right = content.find("\\n", match[1][1])
                right = len(content) if right == -1 else right
                matched_line = content[left:right]
                if matched_line.startswith("\\n"):
                    matched_line = matched_line[2:].strip()
                if matched_line.startswith("#"):
                    continue
                print("    operator:", match[0])
                print("    matched_line:", matched_line)
                content = content.split("\\n")

                # filter some matches before writing to file
                if match[0] == "for":
                    continue
                match_key = (rule["repo"], config_file_name, match[0])
                if match_key in cleared_matches:
                    print("We already cleared match: " + str(match_key))
                    continue
                else:
                    cleared_matches.add(match_key)
                n_matches += 1
                with open(path + "operator_config_matches.txt", "a") as f:
                    f.write("match number: " + str(n_matches) + "\n")
                    f.write("repo: " + rule["repo"] + "\n")
                    f.write("config_file: " + config_file_name + "\n")
                    f.write("rule_name: " + rule["rule_name"] + "\n")
                    f.write("operator: " + match[0] + "\n\n")
                    j = 0
                    all_lines = set()
                    match_lines = set()
                    for line in content:
                        if match[0] in line and not line.strip().startswith("#"):
                            match_lines.add(j)
                            for offset in [-2, -1, 0, 1, 2, 3]:
                                if 0 < j + offset < len(content):
                                    all_lines.add(j + offset)
                                    # description = "context" if offset != 0 else "match  "
                                    # f.write("(" + description + ") " + str(j + offset) + ": " + content[j + offset] + "\n")
                        j += 1
                    all_lines = list(all_lines)
                    all_lines.sort()
                    for k in range(len(all_lines)):
                        line_number = all_lines[k]
                        if k > 0 and all_lines[k-1] < line_number - 1:
                            f.write("...\n")
                        description = "match  " if line_number in match_lines else "context"
                        f.write("(" + description + ") " + str(line_number) + ": " + content[line_number] + "\n")

                    f.write("-------------------------------------------------------------------------------\n")

    # write out sorted operator counts
    operator_matches_list = [(key, value) for key, value in operator_matches.items()]
    operator_matches_list.sort(key=lambda x: x[1], reverse=True)
    with open(path + "operator_config_match_counts.csv", "w") as f:
        for op, count in operator_matches_list:
            f.write(op + ", " + str(count) + "\n")


def inspect_operator_collection():
    f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}

    f2 = {"shell_lines": {"$exists": True, "$not": {"$size": 0}}}


    n0 = db.rules.count_documents({})
    n1 = db.rules.count_documents(f1)
    n2 = db.rules.count_documents(f2)

    f3 = {"config_operator_matches": {"$exists": True, "$not": {"$size": 0}}}
    n3 = db.rules.count_documents(f3)

    print("total number of rules:", n0)
    print("shell rules:", n2)
    print("operator rules:", n1)
    print("config match rules:", n3)

    print(db.rules.find(f1).next().keys())


def plot_operator_count_by_rule(path_prefix="github_scraping/analysis/operators/"):

    # counts is number of rules in this category
    # bins is the number of operators in rule
    f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}
    rule_data = db.rules.find(f1)
    count_dict = {}
    for rule in rule_data:
        n_operators = len(rule["operators"])
        if n_operators >= 25:
            n_operators = 25
        if n_operators in count_dict:
            count_dict[n_operators] += 1
        else:
            count_dict[n_operators] = 1
    data = [(n_operators, count) for n_operators, count in count_dict.items()]
    data.sort(key=lambda x: x[0])

    for a,b in data:
        print(a, b)

    # plot data
    counts = [t[1] for t in data]
    bins = [t[0] for t in data]
    # bins = [0] + bins
    plt.rc('font', size=20)
    # cm = 1 / 2.54  # centimeters in inches
    # plt.figure(figsize=(4.0 * cm, 3.0 * cm))
    plt.bar(bins, counts)
    plt.xticks([0, 5, 10, 15, 20, 25], ["0", "5", "10", "15", "20", ">24"])
    plt.title('Number of operators in rules')
    plt.xlabel('number of operators')
    plt.ylabel('number of rules')
    plt.tight_layout()
    plt.savefig(path_prefix + "figures/rule_operator_counts.svg", format="svg", bbox_inches='tight')


def plot_config_operator_matches_data(path_prefix="github_scraping/analysis/operators/results/"):
    f1 = {"config_operator_matches": {"$exists": True}}

    repos_with_matches = set()
    operator_domain_map = get_operator_domain_map(path_prefix="github_scraping/analysis/operators/")
    operators_total = {}
    operators_by_repo = {}
    aggregate_count = {}
    for i in range(9):
        aggregate_count[i] = [set(), 0]

    for rule in db.rules.find(f1):
        actually_matched = False
        for config_file, matches in rule["config_operator_matches"].items():
            #print(type(matches), len(matches))
            for match in matches:
                operator = match[0]
                if operator == "":
                    continue
                actually_matched = True
                if operator in operators_total:
                    operators_total[operator] += 1
                else:
                    operators_total[operator] = 1
                if operator in operators_by_repo:
                    operators_by_repo[operator].add(rule["repo"])
                else:
                    operators_by_repo[operator] = {rule["repo"]}
                try:
                    domain = operator_domain_map[operator]
                except KeyError:
                    print("KeyError for match:", match)
                    #if operator:
                    #    print("KeyError for operator:", operator)
                    continue
                # combine domains to other
                if domain >= 6:
                    domain = 6
                aggregate_count[domain][0].add(rule["repo"])
                aggregate_count[domain][1] += 1
            if actually_matched:
                repos_with_matches.add(rule["repo"])

    # write out results
    print("repos with matches:", len(repos_with_matches))

    operators_data_list = [(operator, len(operators_by_repo[operator]), total_count) for
                           operator, total_count in operators_total.items()]
    operators_data_list.sort(key=lambda x: (x[1], x[2]), reverse=True)

    with open(path_prefix + "operator_match_counts.csv", "w") as f:
        f.write("operator, number of matching repos, number of total matches\n")
        for operator, count_by_repo, total_count in operators_data_list:
            f.write(operator + ", " + str(count_by_repo) + ", " + str(total_count) + "\n")

    with open(path_prefix + "operator_match_counts_bioinformatics.csv", "w") as f:
        f.write("operator, number of matching repos, number of total matches\n")
        for operator, count_by_repo, total_count in operators_data_list:
            try:
                domain = operator_domain_map[operator]
            except KeyError:
                continue
            # print(operator, domain)
            if domain == 0:
                f.write(operator + ", " + str(count_by_repo) + ", " + str(total_count) + "\n")

    with open(path_prefix + "operator_match_counts_aggregate.csv", "w") as f:
        f.write("domain, count by repo, total count\n")
        domains = ["Bioinformatics", "Control flow", "File processing", "File system", "Code execution",
                   "Data handling", "Misc", "Noise", "under 10"]
        for i in range(9):
            f.write(domains[i] + ", " + str(len(aggregate_count[i][0])) + ", " + str(aggregate_count[i][1]) + "\n")


def operator_analysis(path_prefix="github_scraping/analysis/operators/"):
    #plot_operator_domains_by_workflow()
    #plot_operator_count_by_rule()
    #get_operators_overview()
    #f1 = {"operators": {"$exists": True, "$size": 1}}
    #get_operators_overview(path_prefix="github_scraping/analysis/operators/results/1_", f=f1)
    plot_config_operator_matches_data()
    exit()

    with open(path_prefix + "prepared_data/operator_categories.csv", "r") as f:
        content = f.readlines()
    write_content = []
    for line in content:
        n = line.count(",")
        if n > 1:
            write_content.append(line)
        else:
            write_content.append(line[:-1] + ", 8\n")
    with open(path_prefix + "prepared_data/operator_categories_completed.csv", "w") as f:
        for line in write_content:
            f.write(line)


