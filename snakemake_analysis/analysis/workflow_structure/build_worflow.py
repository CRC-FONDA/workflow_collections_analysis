from analysis.workflow_structure.workflow_units.workflow import Workflow
import math


def scan_all_trees(results_path, log_path, meta_path):
    from db_operations.db_connector import DBConnector
    db = DBConnector()
    i = 0
    meta_results = dict()
    for repo in db.final_state.find():
        try:
            # build the workflow
            wf = Workflow(repo, log_path)
            # collect meta results
            meta_rules = dict()
            for rule_name, rule in wf.rules.items():
                meta_rules[rule_name] = {
                    "n_inputs": len(rule.inputs),
                    "n_input_funcs": len([i for i in rule.inputs if i[1]]),
                    "n_outputs": len(rule.outputs),
                }
            meta_repo = {
                "rules": meta_rules,
                "tree": wf.tree.metadata,
            }
            meta_results[repo["repo"]] = meta_repo

            # write out repo tree results
            if wf.tree.metadata["n_nodes"] >= 1:
                with open(results_path, "a") as f:
                    f.write("(" + str(i) + ") repo: " + repo["repo"] + "\n")
                    f.write("tree metadata: ")
                    f.write(str(wf.tree.metadata) + "\n")
                    f.write("nodes metadata:\n")
                    for node in wf.tree.traverse():
                        f.write(str(node.metadata) + "\n")
                    f.write("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n")
        except RecursionError as e:
            with open(log_path, "a") as f:
                f.write("repo: " + repo["repo"] + "\n")
                f.write(str(e))
                f.write("\n\n")
        i += 1
    extract_meta_results(meta_results, meta_path)


def extract_meta_results(metadata, meta_path):
    n_repos = 0
    n_total_rules = 0
    n_rules_list = []
    n_inputs_per_rule_list = []
    n_input_funcs_per_rule_list = []
    n_outputs_per_rule_list = []
    avg_n_inputs_per_rule_per_repo_list = []
    avg_n_input_funcs_per_rule_per_repo_list = []
    avg_n_outputs_per_rule_per_repo_list = []
    n_rules_without_input_per_repo_list = []

    amount_of_nodes_from_rules_by_repo_list = []
    tree_height_per_repo_list = []
    total_amount_of_nodes_from_rules_by_repo = 0

    for repo_name, repo_meta in metadata.items():
        n_repos += 1
        n_rules = len(repo_meta["rules"])
        n_total_rules += n_rules
        n_rules_list.append(n_rules)
        n_inputs = 0
        n_input_funcs = 0
        n_outputs = 0
        n_rules_without_input = 0
        for rule_name, rule_meta in repo_meta["rules"].items():
            new_inputs = rule_meta["n_inputs"]
            new_input_funcs = rule_meta["n_input_funcs"]
            new_outputs = rule_meta["n_outputs"]
            n_inputs_per_rule_list.append(new_inputs)
            n_input_funcs_per_rule_list.append(new_input_funcs)
            n_outputs_per_rule_list.append(new_outputs)
            n_inputs += new_inputs
            n_input_funcs += new_input_funcs
            n_outputs += new_outputs
            if new_inputs == 0:
                n_rules_without_input += 1
        if n_rules != 0:
            avg_n_inputs_per_rule_per_repo_list.append(n_inputs / n_rules)
            avg_n_input_funcs_per_rule_per_repo_list.append(n_input_funcs / n_rules)
            avg_n_outputs_per_rule_per_repo_list.append(n_outputs / n_rules)
        else:
            avg_n_inputs_per_rule_per_repo_list.append(0)
            avg_n_input_funcs_per_rule_per_repo_list.append(0)
            avg_n_outputs_per_rule_per_repo_list.append(0)
        n_rules_without_input_per_repo_list.append(n_rules_without_input)

        if n_rules != 0:
            amount_of_nodes_from_rules_by_repo = (repo_meta["tree"]["n_nodes"] / n_rules, repo_meta["tree"]["n_nodes"], n_rules)
        else:
            amount_of_nodes_from_rules_by_repo = (0, repo_meta["tree"]["n_nodes"], n_rules)
        amount_of_nodes_from_rules_by_repo_list.append(amount_of_nodes_from_rules_by_repo)
        total_amount_of_nodes_from_rules_by_repo += amount_of_nodes_from_rules_by_repo[0]
        tree_height_per_repo_list.append(repo_meta["tree"]["height"])
    average_amount_of_nodes_from_rules_by_repo = total_amount_of_nodes_from_rules_by_repo / n_repos

    with open(meta_path, "a") as f:
        f.write("META RESULTS\n\n\n")
        f.write("number of repos: "+str(n_repos)+"\n")
        f.write("total number of rules: "+str(n_total_rules)+"\n")
        f.write("\n")
        f.write("rules per repo: "+str(util_sort(n_rules_list))+"\n")
        p25, p50, p75 = get_percentiles(n_rules_list)
        f.write("percentiles: p25="+str(p25)+", p50="+str(p50)+", p75="+str(p75))
        f.write("; average="+str(sum(n_rules_list) / len(n_rules_list))+"\n")
        f.write("\n")
        f.write("number of inputs per rule: "+str(util_sort(n_inputs_per_rule_list))+"\n")
        p25, p50, p75 = get_percentiles(n_inputs_per_rule_list)
        f.write("percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75))
        f.write("; average=" + str(sum(n_inputs_per_rule_list) / len(n_inputs_per_rule_list)) + "\n")
        f.write("\n")
        f.write("number of input functions per rule: " + str(util_sort(n_input_funcs_per_rule_list))+"\n")
        p25, p50, p75 = get_percentiles(n_input_funcs_per_rule_list)
        f.write("percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75))
        f.write("; average=" + str(sum(n_input_funcs_per_rule_list) / len(n_input_funcs_per_rule_list)) + "\n")
        f.write("\n")
        f.write("number of outputs per rule: " + str(util_sort(n_outputs_per_rule_list))+"\n")
        p25, p50, p75 = get_percentiles(n_outputs_per_rule_list)
        f.write("percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75))
        f.write("; average=" + str(sum(n_outputs_per_rule_list) / len(n_outputs_per_rule_list)) + "\n")
        f.write("\n")

        f.write("average number of inputs per rule per repo: " + str(util_sort(avg_n_inputs_per_rule_per_repo_list))+"\n")
        p25, p50, p75 = get_percentiles(avg_n_inputs_per_rule_per_repo_list)
        f.write("percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75))
        f.write("; average=" + str(
            sum(avg_n_inputs_per_rule_per_repo_list) / len(avg_n_inputs_per_rule_per_repo_list)) + "\n")
        f.write("\n")
        f.write("average number of input functions per rule per repo: " + str(util_sort(avg_n_input_funcs_per_rule_per_repo_list))+"\n")
        p25, p50, p75 = get_percentiles(avg_n_input_funcs_per_rule_per_repo_list)
        f.write("percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75))
        f.write("; average=" + str(
            sum(avg_n_input_funcs_per_rule_per_repo_list) / len(avg_n_input_funcs_per_rule_per_repo_list)) + "\n")
        f.write("\n")
        f.write("average number of outputs per rule per repo: " + str(util_sort(avg_n_outputs_per_rule_per_repo_list))+"\n")
        p25, p50, p75 = get_percentiles(avg_n_outputs_per_rule_per_repo_list)
        f.write("percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75))
        f.write("; average=" + str(
            sum(avg_n_outputs_per_rule_per_repo_list) / len(avg_n_outputs_per_rule_per_repo_list)) + "\n")
        f.write("\n")
        f.write("number of rules without inputs per repo: " + str(util_sort(n_rules_without_input_per_repo_list))+"\n")
        p25, p50, p75 = get_percentiles(n_rules_without_input_per_repo_list)
        f.write("percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75))
        f.write("; average=" + str(
            sum(n_rules_without_input_per_repo_list) / len(n_rules_without_input_per_repo_list)) + "\n")
        f.write("\n")

        f.write("\n\nTREE META RESULTS:\n\n")
        f.write("number of tree nodes divided by number of rules per repo: " + str(util_sort(amount_of_nodes_from_rules_by_repo_list))+"\n")
        p25, p50, p75 = get_percentiles(amount_of_nodes_from_rules_by_repo_list)
        f.write("percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75))
        f.write("; average=" + str(
            sum([e[0] for e in amount_of_nodes_from_rules_by_repo_list]) / len(amount_of_nodes_from_rules_by_repo_list)) + "\n")
        f.write("average over repos: "+str(average_amount_of_nodes_from_rules_by_repo)+"\n")
        f.write("\n")
        f.write("tree height by repo: " + str(util_sort(tree_height_per_repo_list))+"\n")
        p25, p50, p75 = get_percentiles(tree_height_per_repo_list)
        f.write("percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75))
        f.write("; average=" + str(
            sum(tree_height_per_repo_list) / len(tree_height_per_repo_list)) + "\n")


def util_sort(to_sort_list):
    try:
        to_sort_list.sort(key=lambda x: x[0], reverse=True)
    except TypeError as e:
        to_sort_list.sort(reverse=True)
    return to_sort_list


def get_percentiles(results_list):
    length = len(results_list)
    try:
        results_list.sort(key=lambda x: x[0])
    except TypeError as e:
        results_list.sort()
    p25 = results_list[math.floor(length / 4)]
    p50 = results_list[math.floor(length / 2)]
    p75 = results_list[math.floor((length / 4) * 3)]
    return p25, p50, p75


def test_for_one_repo():
    from db_operations.db_connector import DBConnector
    db = DBConnector()
    i = 0
    for repo in db.final_state.find():
        if i == 204:
            wf = Workflow(repo)
            break
        i += 1


    print("RESULTS:")
    print("repo: " + wf.repo)
    print("source files: " + str(wf.source_files))
    print("config values: " + str(wf.config_values))
    print("-----------------------------------")
    print("RULES:")
    for rule_name, rule in wf.rules.items():
        print("Rule: "+rule_name+", top_rule="+str(rule.top_rule))
        print("INPUTS:")
        for i in rule.inputs:
            print(i)
        print("OUTPUTS:")
        for o in rule.outputs:
            print(o)
        print("-  -  -  -  -  -  -  -  -  -")

    print(wf.tree.print())






