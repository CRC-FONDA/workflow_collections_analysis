from ...utility.parsers.iterate_rules import iterate_all_rules
from ...db_operations.db_connector import DBConnector
from .common_tools import get_operator_domain_map
import matplotlib.pyplot as plt


def get_operators_overview(path_prefix="github_scraping/analysis/operators/full_text_results/", f=None):
    db = DBConnector()
    if not f:
        f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}
    else:
        f1 = f

    n0 = db.full_text_rules.count_documents({})
    n1 = db.full_text_rules.count_documents(f1)
    print(n0, n1)

    operator_domain_map = get_operator_domain_map(path_prefix="github_scraping/analysis/operators/", full_text=True)
    operators_total = dict()
    operators_by_repo = dict()
    operators_by_rule = dict()
    aggregate_count = dict()
    for i in range(9):
        aggregate_count[i] = [set(), set(), 0]

    for rule in db.full_text_rules.find(f1):
        # print(rule["operators"])
        for operator in rule["operators"]:
            if operator.startswith("-") or operator.startswith("{"):
                continue
            if operator in operators_total:
                operators_total[operator] += 1
            else:
                operators_total[operator] = 1
            if operator in operators_by_repo:
                operators_by_repo[operator].add(rule["repo"])
            else:
                operators_by_repo[operator] = {rule["repo"]}
            if operator in operators_by_rule:
                operators_by_rule[operator].add((rule["repo"], rule["file_name"], rule["rule_name"]))
            else:
                operators_by_rule[operator] = {(rule["repo"], rule["file_name"], rule["rule_name"])}
            try:
                domain = operator_domain_map[operator]
            except KeyError:
                continue
            # combine to one other domain
            if domain >= 6:
                domain = 6
            aggregate_count[domain][0].add(rule["repo"])
            aggregate_count[domain][1].add((rule["repo"], rule["file_name"], rule["rule_name"]))
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


def plot_config_operator_matches_data(path_prefix="github_scraping/analysis/operators/full_text_results/"):
    db = DBConnector()
    f1 = {"config_operator_matches": {"$exists": True}}

    repos_with_matches = set()
    operator_domain_map = get_operator_domain_map(path_prefix="github_scraping/analysis/operators/", full_text=True)
    operators_total = {}
    operators_by_repo = {}
    aggregate_count = {}
    for i in range(9):
        aggregate_count[i] = [set(), 0]

    for rule in db.full_text_rules.find(f1):
        actually_matched = False
        for config_file, matches in rule["config_operator_matches"].items():
            #print(type(matches), len(matches))
            for match in matches:
                operator = match[0]
                if operator == "":
                    continue
                if operator.startswith("-") or operator.startswith("{"):
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


def plot_operator_domains_by_workflow(path_prefix="github_scraping/analysis/operators/"):
    db = DBConnector()
    f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}

    operator_domain_map = get_operator_domain_map(path_prefix=path_prefix, full_text=True)

    workflow_data = {}
    operator_rules = db.full_text_rules.find(f1)
    for rule in operator_rules:
        if rule["repo"] in workflow_data:
            workflow_data[rule["repo"]].append((rule["file_name"], rule["rule_name"], rule["operators"]))
        else:
            workflow_data[rule["repo"]] = [(rule["file_name"], rule["rule_name"], rule["operators"])]

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
                if operator.startswith("-") or operator.startswith("{"):
                    continue
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


def prepare_domain_map():
    db = DBConnector()
    old_domain_map = get_operator_domain_map()
    target_domain_map_path_old = "github_scraping/analysis/operators/prepared_data/full_text_operator_categories_old.csv"
    target_domain_map_path = "github_scraping/analysis/operators/prepared_data/full_text_operator_categories.csv"

    def first_count():
        operator_count = {}
        for rule in db.full_text_rules.find({"operators": {"$exists": True, "$not": {"$size": 0}}}):
            operators = [o for o in rule["operators"] if not o.startswith("-")]
            for operator in operators:
                if operator in operator_count:
                    operator_count[operator] += 1
                else:
                    operator_count[operator] = 1

        operators = [(operator, count) for operator, count in operator_count.items()]
        operators.sort(key=lambda x: x[1], reverse=True)

        with open(target_domain_map_path, "w") as f:
            for operator, count in operators:
                try:
                    domain = old_domain_map[operator]
                except KeyError:
                    domain = ""
                f.write(operator + ", " + str(count) + ", " + str(domain) + "\n")

    def complete_domains():
        with open(target_domain_map_path_old, "r") as f:
            next(f)
            lines = f.readlines()
            new_lines = []
            for line in lines:
                line = line.strip()
                print(line)
                k1 = line.rfind(",")
                if len(line) > k1 + 1:
                    domain = str(int(line[k1 + 1:]))
                else:
                    domain = None
                k2 = line[:k1].rfind(",")
                operator = line[:k2]
                count = line[k2+2:k1].strip()
                if not domain:
                    domain = str(8)
                if operator.startswith("{"):
                    domain = str(9)
                print("operator:", operator)
                print("count:", count)
                print("domain:", repr(domain))
                new_lines.append(operator + ", " + count + ", " + domain + "\n")
                print("-------------------------------")
        with open(target_domain_map_path, "w") as f:
            for line in new_lines:
                f.write(line)

    complete_domains()


def plot_operator_count_by_rule(path_prefix="github_scraping/analysis/operators/"):
    db = DBConnector()
    # counts is number of rules in this category
    # bins is the number of operators in rule
    f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}
    rule_data = db.full_text_rules.find(f1)
    count_dict = {}
    for rule in rule_data:
        operators = []
        for operator in rule["operators"]:
            if operator.startswith("-") or operator.startswith("{"):
                continue
            operators.append(operator)
        n_operators = len(operators)
        if n_operators == 0:
            continue
        if n_operators >= 25:
            n_operators = 25
        if n_operators in count_dict:
            count_dict[n_operators] += 1
        else:
            count_dict[n_operators] = 1
    data = [(n_operators, count) for n_operators, count in count_dict.items()]
    data.sort(key=lambda x: x[0])

    for a, b in data:
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
    plt.savefig(path_prefix + "figures/full_text_rule_operator_counts.svg", format="svg", bbox_inches='tight')


def analyse_operators():
    #get_operators_overview()
    #plot_config_operator_matches_data()
    #plot_operator_domains_by_workflow()
    plot_operator_count_by_rule()

    exit()

    total = 0
    shell_lines = 0
    for rule in iterate_all_rules():
        # print(total)
        total += 1
        if len(rule["shell_lines"]) > 0:
            shell_lines += 1

    print("total:", total)
    print("shell_lines", shell_lines)

