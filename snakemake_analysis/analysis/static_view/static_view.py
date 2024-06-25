import networkx as nx
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np

from ...utility.graph_utility import (
    get_graph_from_commit_dag_string,
    get_node_label_map_from_dag_string,
)

from ...utility.print_dags import (
    print_dag_from_dag_string,
)

from ...utility.parsers.snakefile_parser import get_rules_from_file

from ...db_operations.db_connector import DBConnector
db = DBConnector()


def write_workflow_structure_metadata(path="github_scraping/analysis/static_view/results/metadata.txt"):
    n_repos = len(db.workflow_structures.distinct("repo"))
    n_repos_with_dag = db.workflow_structures.count_documents({"dag": {"$ne": None}})
    # n_repos_with_graph = db.workflow_structures.count_documents({"graph": {"$exists": True}})

    lists = {
        'n_nodes': [],
        'n_logical_rules': [],
        'n_parallel_pairs': [],
        'longest_path': [],
        'max_degree': [],
        'avg_degree': [],
    }
    lists_data = dict()

    for doc in db.workflow_structures.find({"graph": {"$exists": True}}):
        for datum in lists.keys():
            lists[datum].append(doc["graph"][datum])

    for datum in lists.keys():
        lists[datum].sort()
        datum_list = lists[datum]
        lists_data[datum] = {
            "p25": datum_list[int(len(datum_list) / 4)],
            "p50": datum_list[int(len(datum_list) / 2)],
            "p75": datum_list[int(len(datum_list) * 3 / 4)],
            "avg": sum(datum_list) / len(datum_list)
        }

    with open(path, "w") as f:
        f.write("number of repos in collection: "+str(n_repos)+"\n")
        f.write("number of repos with dag: "+str(n_repos_with_dag)+"\n")
        # f.write("number of repos with dag analysis data: " + str(n_repos_with_graph) + "\n")

        f.write("\nDistributions of dag characteristics:\n")
        f.write("(n_parallel_pairs is number of node-pairs in the dag that have no path in either direction, thus they can be run in parallel)\n")
        for datum in lists_data.keys():
            f.write(datum+": ")
            data = lists_data[datum]
            for t in data.keys():
                f.write(t+"="+str(data[t])+", ")
            f.write("\n")


def write_workflow_structure_parallelism(path="github_scraping/analysis/static_view/results/"):
    n_analysed_graphs = 0

    overall_data = {
        "avg_degree": [],
        "median_degree": [],
        "max_degree": [],
        "avg_logical_degree": [],
        "median_logical_degree": [],
        "max_logical_degree": [],
        "avg_from_one_logical": [],
        "median_from_one_logical": [],
        "max_from_one_logical": [],
        "avg_from_one_wildcard": [],
        "median_from_one_wildcard": [],
        "max_from_one_wildcard": [],
        "logical-physical_ratio": [],
        "avg_logical_over_physical_degrees": [],
        "min_logical_over_physical_degrees": [],
        "example_repos": [],
        "example_rules": [],
    }

    f1 = {"dag": {"$ne": None}}
    f2 = {"$and": [
        {"dag": {"$ne": None}},
        {"graph.n_nodes": {"$gt": 2}},
    ]}
    m = str(db.workflow_structures.count_documents(f1))
    i = 0
    for doc in db.workflow_structures.find(f1):
        #if i > 9:
        #    break
        i += 1
        print("("+str(i)+"/"+m+") analysing "+doc["repo"])
        graph = get_graph_from_commit_dag_string(doc)
        if not graph:
            continue
        n_analysed_graphs += 1

        dag_path = "github_scraping/analysis/static_view/results/dags/"
        print_dag_from_dag_string(doc["dag"], dag_path, doc["repo"].replace("/", "_"))
        label_map = get_node_label_map_from_dag_string(doc["dag"])

        # reverse graph for neighbour analysis
        graph = graph.reverse()
        dag_data = {
            "degree": [],
            "logical_degree": [],
            "from_one_logical": [],
            "from_one_wildcard": [],
            "logical_over_physical_degrees": [],
        }
        for x in graph:
            # print("node:", x, "label:", label_map[x])
            requested_nodes = 0
            requested_logical_rules = set()
            requested_wildcard_instances = 0
            # requested_wildcard_rules = set()
            logical_rule_requests = dict()
            wildcard_rule_requests = dict()
            for y in graph.neighbors(x):
                requested_nodes += 1
                label = label_map[y]
                wildcard = label.find("\\n")
                if wildcard != -1:
                    requested_wildcard_instances += 1
                    label = label[:wildcard]
                    # requested_wildcard_rules.add(label)
                    if label not in wildcard_rule_requests.keys():
                        wildcard_rule_requests[label] = 1
                    else:
                        wildcard_rule_requests[label] += 1
                requested_logical_rules.add(label)
                if label not in logical_rule_requests.keys():
                    logical_rule_requests[label] = 1
                else:
                    logical_rule_requests[label] += 1

            # collect example rules with high degree
            degree = requested_nodes
            if len(overall_data["example_rules"]) < 10:
                overall_data["example_rules"].append((
                    doc["repo"],
                    degree,
                    label_map[x],
                ))
                overall_data["example_rules"].sort(key=lambda _x: _x[1])
            else:
                if degree > overall_data["example_rules"][0][1]:
                    overall_data["example_rules"][0] = (
                        doc["repo"],
                        degree,
                        label_map[x],
                    )
                    overall_data["example_rules"].sort(key=lambda _x: _x[1])
            # add data for this node into dag statistics
            dag_data["degree"].append(requested_nodes)
            dag_data["logical_degree"].append(len(requested_logical_rules))
            dag_data["from_one_logical"].append(max(logical_rule_requests.values()) if logical_rule_requests else 0)
            dag_data["from_one_wildcard"].append(max(wildcard_rule_requests.values()) if wildcard_rule_requests else  0)
            if requested_nodes > 0:
                dag_data["logical_over_physical_degrees"].append(len(requested_logical_rules) / requested_nodes)

        # collect data for this dag into overall statistics
        for data_key in dag_data.keys():
            if data_key == "logical_over_physical_degrees":
                continue
            overall_data["avg_" + data_key].append(sum(dag_data[data_key]) / len(dag_data[data_key]))
            dag_data[data_key].sort(reverse=True)
            overall_data["max_" + data_key].append(dag_data[data_key][0])
            overall_data["median_" + data_key].append(dag_data[data_key][int(len(dag_data[data_key])/2)])
        overall_data["logical-physical_ratio"].append(doc["graph"]["n_logical_rules"] / doc["graph"]["n_nodes"])
        if len(dag_data["logical_over_physical_degrees"]) > 0:
            overall_data["avg_logical_over_physical_degrees"].append(sum(dag_data["logical_over_physical_degrees"]) / len(dag_data["logical_over_physical_degrees"]))
            overall_data["min_logical_over_physical_degrees"].append(min(dag_data["logical_over_physical_degrees"]))

        # collect workflow examples according to parallelism score
        p_score = overall_data["max_degree"][-1] / graph.number_of_nodes()
        if len(overall_data["example_repos"]) < 10:
            overall_data["example_repos"].append((
                doc["repo"],
                p_score,
                overall_data["max_degree"][-1],
                graph.number_of_nodes(),
            ))
            overall_data["example_repos"].sort(key=lambda _x: _x[1])
        else:
            if p_score > overall_data["example_repos"][0][1]:
                overall_data["example_repos"][0] = (
                    doc["repo"],
                    p_score,
                    overall_data["max_degree"][-1],
                    graph.number_of_nodes(),
                )
                overall_data["example_repos"].sort(key=lambda _x: _x[1])

    # create figures for data
    plt.tight_layout()

    def get_bar_data(bar_data_list):
        count_dict = Counter(bar_data_list)
        max_value = max(count_dict.keys())
        for value in range(max_value):
            if value not in count_dict.keys():
                count_dict[value] = 0
        base_data = [(path_length, count) for path_length, count in count_dict.items()]
        base_data.sort(key=lambda _x: _x[0])
        data_bins = [d[0] for d in base_data]
        data_counts = [d[1] for d in base_data]
        return data_bins, data_counts

    #plt.rc('font', size=16)
    fig, axs = plt.subplots(2, 2)
    fig.tight_layout(h_pad=5)
    bins = [d/2 for d in range(20)] + [max(overall_data["avg_degree"])]
    h, e = np.histogram(overall_data["avg_degree"], bins=bins)
    axs[0, 0].bar(range(len(bins)-1), h)
    axs[0, 0].set_xticks(range(len(bins) - 1))
    axs[0, 0].set_xticklabels(bins[:-1])
    # axs[0, 0].set_xticklabels(["1", "", "", "", "3", "", "", "", "5", "", "", "", "7", "", "", "", "9", "", "", ""], fontsize=20)
    axs[0, 0].xaxis.set_major_locator(plt.MaxNLocator(8))
    axs[0, 0].set_title('Avg physical job degree')
    axs[0, 0].set(ylabel='number of workflows')
    counts, bins, patches = axs[0, 1].hist(overall_data["avg_logical_degree"], density=False, bins=20)
    # axs[0, 1].set_xticks(bins)
    axs[0, 1].set_title('Avg logical rule degree')
    bins, counts = get_bar_data(overall_data["max_degree"])
    right_sum = sum(counts[41:])
    bins = bins[:41] + [41]
    counts = counts[:41] + [right_sum]
    axs[1, 0].bar(bins, counts)
    axs[1, 0].set_title('Max physical job degree')
    axs[1, 0].set(xlabel='degree', ylabel='number of workflows')
    bins, counts = get_bar_data(overall_data["max_logical_degree"])
    axs[1, 1].bar(bins, counts)
    axs[1, 1].set_title('Max logical rule degree')
    axs[1, 1].set(xlabel='degree')
    #fig.supxlabel('degree')
    #fig.supylabel('number of workflows')

    #for ax in axs.flat:
    #    ax.set(xlabel='degree', ylabel='number of workflows')

    plt.savefig(path + "figures/job_degrees.svg", format="svg", bbox_inches='tight')

    # separate plot for logical to physical ratios
    plt.clf()
    plt.rc('font', size=20)
    fig.tight_layout(h_pad=3)
    data = overall_data["logical-physical_ratio"]
    plt.hist(data, density=False, bins=20, log=True)
    plt.title('Logical rule/physical job ratio')
    plt.xlabel('ratio')
    plt.ylabel('count')
    plt.savefig(path + "figures/log_logical_physical_ratio.svg", format="svg", bbox_inches='tight')

    # separate plot for histograms for logical over physical degrees
    plt.clf()
    plt.rc('font', size=20)
    fig, axs = plt.subplots(1, 2)
    fig.tight_layout(pad=2)
    axs[0].hist(overall_data["avg_logical_over_physical_degrees"], density=False, bins=10)
    axs[0].set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    axs[0].set_xticklabels(["0.0", "", "", "", "", "0.5", "", "", "", "", "1.0"], fontsize=20)
    axs[0].set_title('Average ratio')
    axs[0].set(ylabel='number of workflows')
    # bins, counts = get_bar_data(overall_data["max_logical_over_physical_degrees"])
    axs[1].hist(overall_data["min_logical_over_physical_degrees"], density=False, bins=10)
    axs[1].set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    axs[1].set_xticklabels(["0.0", "", "", "", "", "0.5", "", "", "", "", "1.0"], fontsize=20)
    axs[1].set_title('Minimal ratio')
    # axs[1].set(xlabel='ratio of logical rules to physical jobs')
    fig.supxlabel('ratio of logical rules to physical jobs')
    plt.savefig(path + "figures/logical_over_physical_degrees.svg", format="svg", bbox_inches='tight')

    # write out parallelism results
    description = "Description of the data presented here:\n\n" \
                  "For each repository we look at the constructed dag:\n" \
                  "  For each such dag we look at each of its nodes:\n" \
                  "    For each node we look at its neighbours and calculate:\n" \
                  "      its degree (number of jobs it \"spawns\")\n" \
                  "      its logical_degree (number of logical rules its spawns)\n" \
                  "      its from_one_logical (maximum number of requested jobs stemming from one logical rule)\n" \
                  "      its from_one_wildcard (same as from_one_logical except these must be distinct instances for one wildcard)\n" \
                  "  Then we calculate the average, median and max over all the nodes for each repo.\n" \
                  "Finally reported here are the statistics over these measures over the collection of repositories/dags\n\n"

    with open(path + "parallelism.txt", "w") as f:
        f.write(description)
        f.write("number of analysed graphs: "+str(n_analysed_graphs)+"/"+m+"\n\n")
        f.write("length of avg_degree: " + str(len(overall_data["avg_degree"])) + "\n")
        f.write("length of max_degree: " + str(len(overall_data["max_degree"])) + "\n")
        f.write("length of avg_logical_degree: " + str(len(overall_data["avg_logical_degree"])) + "\n")
        f.write("length of max_logical_degree: " + str(len(overall_data["max_logical_degree"])) + "\n\n")
        lists_data = dict()
        for datum in overall_data.keys():
            if datum == "example_repos" or datum == "example_rules":
                continue
            data_list = overall_data[datum]
            data_list.sort()
            lists_data[datum] = {
                "p25": data_list[int(len(data_list) / 4)],
                "p50": data_list[int(len(data_list) / 2)],
                "p75": data_list[int(len(data_list) * 3 / 4)],
                "avg": sum(data_list) / len(data_list),
                "min": data_list[0],
                "max": data_list[len(data_list)-1],
            }

        f.write("\nDistributions of dag characteristics:\n")
        j = 0
        for datum in lists_data.keys():
            if j % 3 == 0:
                f.write("\n")
            j += 1
            f.write(datum + ": ")
            data = lists_data[datum]
            for t in data.keys():
                f.write(t + "=" + str(data[t]) + ", ")
            f.write("\n")

        f.write("\n\nExample workflows:\n")
        for example in overall_data["example_repos"]:
            f.write(str(example)+"\n")

        f.write("\n\nExample rules:\n")
        for example in overall_data["example_rules"]:
            f.write(str(example) + "\n")


def write_workflow_structure_loops(path="github_scraping/analysis/static_view/results/loops.txt"):
    n_analysed_graphs = 0

    overall_data = {
        "n_paths": [],
        "n_loop_paths": [],
        "max_n_logical_in_one_path": [],
        "avg_logical_by_length": [],
        "median_logical_by_length": [],
        "min_logical_by_length": [],
        "loop_repos": [],
    }

    f1 = {"dag": {"$ne": None}}
    f2 = {"$and": [
        {"dag": {"$ne": None}},
        {"graph.n_nodes": {"$gt": 2}},
    ]}
    m = str(db.workflow_structures.count_documents(f1))

    i = 0
    j = 0
    for doc in db.workflow_structures.find(f1):
        i += 1
        #if i > 10:
        #    break

        print("(" + str(i) + "/" + m + ") analysing " + doc["repo"])
        graph = get_graph_from_commit_dag_string(doc)
        if not graph:
            continue
        n_analysed_graphs += 1

        label_map = get_node_label_map_from_dag_string(doc["dag"])

        # reverse graph for neighbour analysis
        graph = graph.reverse()

        dag_data = {
            "n_paths": 0,
            "n_loop_paths": 0,
            "max_n_logical_in_one_path": 1,
            "logical_by_length": [],
            "loop_paths": [],
            "looped_rules": set(),
            "unique_label_id": 0,
            "longest_loop_path": [],
            "shortest_loop_path": [],
        }

        # depth first traversal of dag starting from root
        # as paths we consider only maximal paths that end at a leaf
        def traverse(node, path_prefix, dag_data_dict):
            if node in label_map.keys():
                label = label_map[node]
            else:
                # fix for when label_map fails, we assume uniqueness of label
                # we need unique labels to not create incorrect loops with default labels
                label = "unique_label_"+str(dag_data_dict["unique_label_id"])+"_"+str(node)
                dag_data_dict["unique_label_id"] += 1
            wildcard = label.find("\\n")
            if wildcard != -1:
                label = label[:wildcard]
            path_prefix.append(label)
            children = [child for child in graph.neighbors(node)]
            if children:
                for child in children:
                    traverse(child, path_prefix, dag_data_dict)
            else:
                # we are at a leaf and have collected a max path that we now analyse
                dag_data_dict["n_paths"] += 1
                logical_by_length = len(set(path_prefix)) / len(path_prefix)
                if logical_by_length < 1:
                    dag_data_dict["n_loop_paths"] += 1
                    rule_counts = set([(rule, path_prefix.count(rule)) for rule in path_prefix])
                    rule_name, mnl = max([rule_count for rule_count in rule_counts], key=lambda x: x[1])
                    dag_data_dict["max_n_logical_in_one_path"] = max(dag_data_dict["max_n_logical_in_one_path"], mnl)
                    dag_data_dict["looped_rules"].add(rule_name)
                    path_length = len(path_prefix)
                    if dag_data_dict["longest_loop_path"]:
                        if path_length > len(dag_data_dict["longest_loop_path"]):
                            dag_data_dict["longest_loop_path"] = path_prefix.copy()
                            #raise ValueError("new longest loop path: "+str(path_prefix))
                    else:
                        dag_data_dict["longest_loop_path"] = path_prefix.copy()
                        #raise ValueError("new longest path: " + str(path_prefix))
                    if dag_data_dict["shortest_loop_path"]:
                        if path_length < len(dag_data_dict["shortest_loop_path"]):
                            dag_data_dict["shortest_loop_path"] = path_prefix.copy()
                            #raise ValueError("new shortest loop path: " + str(path_prefix))
                    else:
                        dag_data_dict["shortest_loop_path"] = path_prefix.copy()
                dag_data_dict["logical_by_length"].append(logical_by_length)
                #print("path:", path_prefix)
                #print("rules:", rule_counts)
            # remove thyself again from prefix
            path_prefix.pop()

        root = next(nx.topological_sort(graph))
        prefix = []
        traverse(root, prefix, dag_data)

        overall_data["n_paths"].append(dag_data["n_paths"])
        overall_data["n_loop_paths"].append(dag_data["n_loop_paths"])
        overall_data["max_n_logical_in_one_path"].append(dag_data["max_n_logical_in_one_path"])
        dag_data["logical_by_length"].sort()
        overall_data["min_logical_by_length"].append(dag_data["logical_by_length"][0])
        overall_data["median_logical_by_length"].append(dag_data["logical_by_length"][int(len(dag_data["logical_by_length"]) / 2)])
        overall_data["avg_logical_by_length"].append(sum(dag_data["logical_by_length"]) / len(dag_data["logical_by_length"]))

        if dag_data["n_loop_paths"] > 0:
            overall_data["loop_repos"].append((
                doc["repo"],
                dag_data["looped_rules"],
                overall_data["n_loop_paths"][j],
                overall_data["max_n_logical_in_one_path"][j],
                dag_data["longest_loop_path"],
                dag_data["shortest_loop_path"]))
        # j serves as index for this repo in the overall data lists
        j += 1

    with open(path, "w") as f:
        f.write("number of analysed graphs: " + str(n_analysed_graphs) + "/" + m + "\n\n")

        f.write("max_n_logical_in_one_path (max number of times a logical rule was repeated per repo): \n")
        loop_counts = set(overall_data["max_n_logical_in_one_path"])
        for c in loop_counts:
            f.write("repeat_count = "+str(c)+": occurred "+str(overall_data["max_n_logical_in_one_path"].count(c))+" times\n")
        f.write("\n\n")

        lists_data = dict()
        for datum in ["n_paths", "n_loop_paths", "avg_logical_by_length", "median_logical_by_length", "min_logical_by_length"]:
            data_list = overall_data[datum]
            data_list.sort()
            # print("data_list", datum, len(data_list))
            lists_data[datum] = {
                "p25": data_list[int(len(data_list) / 4)],
                "p50": data_list[int(len(data_list) / 2)],
                "p75": data_list[int(len(data_list) * 3 / 4)],
                "avg": sum(data_list) / len(data_list),
                "min": data_list[0],
                "max": data_list[len(data_list) - 1]
            }

        f.write("Distributions of dag characteristics:\n")
        for datum in lists_data.keys():
            f.write(datum + ": ")
            data = lists_data[datum]
            for t in data.keys():
                f.write(t + "=" + str(data[t]) + ", ")
            f.write("\n")

        f.write("\nrepos with loops:\nrepo name, repeated rule name, number of paths with rule repetition, "
                "max rule repetition in one path\n"
                "longest loop path,\nshortest loop path\n")
        for repo in overall_data["loop_repos"]:
            f.write(str(repo[0])+", "+str(repo[1])+", "+str(repo[2])+", "+str(repo[3])+", "+"\n")
            f.write("        "+str(repo[4])+",\n")
            f.write("        "+str(repo[5])+",\n")


def write_workflow_structure_branching(path="github_scraping/analysis/static_view/results/branching.txt"):
    overall_data = {
        "n_logical_dag_rules": [],
        "n_workflow_rules": [],
        "ratio_logical_rules_by_workflow_rules": [],
    }

    f1 = {"dag": {"$ne": None}}
    f2 = {"$and": [
        {"dag": {"$ne": None}},
        {"graph.n_nodes": {"$gt": 2}},
    ]}
    m = str(db.workflow_structures.count_documents(f1))

    n_dag_repos = 0
    n_graph_repos = 0
    n_workflow_repos = 0
    n_getting_rules_from_workflow_failed = 0
    for doc in db.workflow_structures.find(f1):
        n_dag_repos += 1
        print("(" + str(n_dag_repos) + "/" + m + ") analysing " + doc["repo"])
        # build and analyse graph from dag string
        graph = get_graph_from_commit_dag_string(doc)
        if not graph:
            continue
        n_graph_repos += 1
        label_map = get_node_label_map_from_dag_string(doc["dag"])
        unique_label_id = 0
        logical_rules = set()
        for node in graph:
            if node in label_map.keys():
                label = label_map[node]
            else:
                # fix for when label_map fails, we assume uniqueness of label
                # we need unique labels to not create incorrect loops with default labels
                label = "unique_label_"+str(unique_label_id)+"_"+str(node)
                unique_label_id += 1
            wildcard = label.find("\\n")
            if wildcard != -1:
                label = label[:wildcard]
            logical_rules.add(label)
        n_logical_rules = len(logical_rules)

        # get workflow files and extract rules from final_state collection
        workflow = next(db.final_state.find({"repo": doc["repo"]}), None)
        if not workflow:
            continue
        n_workflow_repos += 1
        print(workflow.keys())

        n_workflow_rules = 0
        for filename in workflow["workflow_files"]:
            try:
                content = workflow["files"][filename]["content"].split("\\n")
                rules = get_rules_from_file(filename, file_content=content)
            except Exception as e:
                print("unable to read content for "+workflow["repo"]+", "+filename)
                continue
            n_workflow_rules += len(rules)
        # as an additional alternative also get rules from all files in repo


        overall_data["n_logical_dag_rules"].append(n_logical_rules)
        overall_data["n_workflow_rules"].append(n_workflow_rules)
        if n_workflow_rules == 0:
            n_getting_rules_from_workflow_failed += 1
            n_workflow_rules = 1
        overall_data["ratio_logical_rules_by_workflow_rules"].append(n_logical_rules / n_workflow_rules)

    with open(path, "w") as f:
        f.write("number of repos with dag_string = "+str(n_dag_repos)+
                "\nnumber of repos with successful graph construction = "+str(n_dag_repos)+
                "\nnumber of repos where we retrieved workflow files = "+str(n_workflow_repos))
        f.write("\n  out of those getting workflow rules still failed "+str(n_getting_rules_from_workflow_failed)+ " times.")

        lists_data = dict()
        for datum in overall_data.keys():
            data_list = overall_data[datum]
            data_list.sort()
            lists_data[datum] = {
                "p25": data_list[int(len(data_list) / 4)],
                "p50": data_list[int(len(data_list) / 2)],
                "p75": data_list[int(len(data_list) * 3 / 4)],
                "avg": sum(data_list) / len(data_list),
                "min": data_list[0],
                "max": data_list[len(data_list) - 1],
            }

        f.write("\n\nDistributions of dag characteristics:\n")
        for datum in lists_data.keys():
            f.write(datum + ": ")
            data = lists_data[datum]
            for t in data.keys():
                f.write(t + "=" + str(data[t]) + ", ")
            f.write("\n")


def write_histograms_from_collection(path="github_scraping/analysis/static_view/results/"):
    longest_paths = []
    physical_rules = []
    logical_rules = []
    logical_physical_rule_ratios = []
    for doc in db.workflow_structures.find({"graph": {"$exists": True}}):
        data = doc["graph"]
        longest_paths.append(data["longest_path"])
        physical_rules.append(data["n_nodes"])
        logical_rules.append(data["n_logical_rules"])
        logical_physical_rule_ratios.append(data["n_logical_rules"] / data["n_nodes"])

    count_dict = Counter(longest_paths)
    max_length = max(count_dict.keys())
    for path_length in range(max_length):
        if path_length not in count_dict.keys():
            count_dict[path_length] = 0
    data = [(path_length, count) for path_length, count in count_dict.items()]
    data.sort(key=lambda x: x[0])

    print("number of repos with data:", len(longest_paths))
    print(data)

    counts = [t[1] for t in data]
    bins = [t[0] for t in data]
    # bins = [0] + bins
    plt.rc('font', size=20)
    # cm = 1 / 2.54  # centimeters in inches
    # plt.figure(figsize=(4.0 * cm, 3.0 * cm))
    plt.bar(bins, counts)
    plt.xticks([0, 5, 10, 15, 20, 25])
    plt.title('Longest paths in DAGs')
    plt.xlabel('length of longest path')
    plt.ylabel('number of workflows')
    plt.tight_layout()
    plt.savefig(path + "figures/longest_paths.svg", format="svg", bbox_inches='tight')

    # rule histograms
    plt.clf()

    def get_bar_data(bar_data_list):
        count_dict = Counter(bar_data_list)
        max_value = max(count_dict.keys())
        for value in range(max_value):
            if value not in count_dict.keys():
                count_dict[value] = 0
        base_data = [(path_length, count) for path_length, count in count_dict.items()]
        base_data.sort(key=lambda _x: _x[0])
        data_bins = [d[0] for d in base_data]
        data_counts = [d[1] for d in base_data]
        return data_bins, data_counts

    fig, axs = plt.subplots(1, 2)
    fig.tight_layout(h_pad=3)
    # number of physical rules
    bins, counts = get_bar_data(physical_rules)
    right_sum = sum(counts[51:])
    bins = bins[:51] + [51]
    counts = counts[:51] + [right_sum]
    axs[0].bar(bins, counts)
    # axs[0, 0].set_xticks(range(len(bins) - 1))
    # axs[0, 0].set_xticklabels(bins[:-1])
    # axs[0, 0].xaxis.set_major_locator(plt.MaxNLocator(8))
    axs[0].set_xticks([0, 10, 20, 30, 40, 50])
    axs[0].set_xticklabels(["0", "", "20", "", "40", ""], fontsize=20)
    axs[0].set_title('Physical jobs')
    axs[0].set(xlabel='number of jobs', ylabel='number of workflows')
    # number of logical rules
    bins, counts = get_bar_data(logical_rules)
    right_sum = sum(counts[51:])
    bins = bins[:51] + [51]
    counts = counts[:51] + [right_sum]
    axs[1].bar(bins, counts)
    axs[1].set_xticks([0, 10, 20, 30, 40, 50])
    axs[1].set_xticklabels(["0", "", "20", "", "40", ""], fontsize=20)
    axs[1].set_title('Logical rules')
    axs[1].set(xlabel='number of rules')
    # ratio of logical to physical rules
    #axs[2].hist(logical_physical_rule_ratios, density=False, bins=10)
    #axs[2].set_title('Logical/physical rules')
    #axs[2].set(xlabel='ratio', ylabel='number of repos')

    # plt.savefig(path + "figures/rule_counts.svg", format="svg", bbox_inches='tight')
    plt.savefig(path + "figures/rule_counts.svg", format="svg", bbox_inches='tight')


def write_workflow_structure_sequences(path="github_scraping/analysis/static_view/results/sequences.txt"):
    n_analysed_graphs = 0

    overall_data = {
        "n_nodes": [],
        "n_logical_rules": [],
        "n_paths": [],
        "avg_path_length": [],
        "median_path_length": [],
        "max_path_length": [],
    }

    f1 = {"dag": {"$ne": None}}
    f2 = {"$and": [
        {"dag": {"$ne": None}},
        {"graph.n_nodes": {"$gt": 2}},
    ]}
    m = str(db.workflow_structures.count_documents(f1))

    i = 0
    j = 0
    for doc in db.workflow_structures.find(f1):
        i += 1
        #if i > 10:
        #    break

        print("(" + str(i) + "/" + m + ") analysing " + doc["repo"])
        graph = get_graph_from_commit_dag_string(doc)
        if not graph:
            continue
        n_analysed_graphs += 1

        label_map = get_node_label_map_from_dag_string(doc["dag"])

        # reverse graph for neighbour analysis
        graph = graph.reverse()

        dag_data = {
            "n_paths": 0,
            "n_loop_paths": 0,
            "max_n_logical_in_one_path": 1,
            "logical_by_length": [],
            "loop_paths": [],
            "looped_rules": set(),
            "unique_label_id": 0,
        }

        # depth first traversal of dag starting from root
        # as paths we consider only maximal paths that end at a leaf
        def traverse(node, path_prefix, dag_data_dict):
            if node in label_map.keys():
                label = label_map[node]
            else:
                # fix for when label_map fails, we assume uniqueness of label
                # we need unique labels to not create incorrect loops with default labels
                label = "unique_label_"+str(dag_data_dict["unique_label_id"])+"_"+str(node)
                dag_data_dict["unique_label_id"] += 1
            wildcard = label.find("\\n")
            if wildcard != -1:
                label = label[:wildcard]
            path_prefix.append(label)
            children = [child for child in graph.neighbors(node)]
            if children:
                for child in children:
                    traverse(child, path_prefix, dag_data_dict)
            else:
                # we are at a leaf and have collected a max path that we now analyse
                dag_data_dict["n_paths"] += 1
                logical_by_length = len(set(path_prefix)) / len(path_prefix)
                if logical_by_length < 1:
                    dag_data_dict["n_loop_paths"] += 1
                    rule_counts = set([(rule, path_prefix.count(rule)) for rule in path_prefix])
                    rule_name, mnl = max([rule_count for rule_count in rule_counts])
                    dag_data_dict["max_n_logical_in_one_path"] = max(dag_data_dict["max_n_logical_in_one_path"], mnl)
                    dag_data_dict["looped_rules"].add(rule_name)
                dag_data_dict["logical_by_length"].append(logical_by_length)
                #print("path:", path_prefix)
                #print("rules:", rule_counts)
            # remove thyself again from prefix
            path_prefix.pop()

        root = next(nx.topological_sort(graph))
        prefix = []
        traverse(root, prefix, dag_data)

        overall_data["n_paths"].append(dag_data["n_paths"])
        overall_data["n_loop_paths"].append(dag_data["n_loop_paths"])
        overall_data["max_n_logical_in_one_path"].append(dag_data["max_n_logical_in_one_path"])
        dag_data["logical_by_length"].sort()
        overall_data["min_logical_by_length"].append(dag_data["logical_by_length"][0])
        overall_data["median_logical_by_length"].append(dag_data["logical_by_length"][int(len(dag_data["logical_by_length"]) / 2)])
        overall_data["avg_logical_by_length"].append(sum(dag_data["logical_by_length"]) / len(dag_data["logical_by_length"]))

        if dag_data["n_loop_paths"] > 0:
            overall_data["loop_repos"].append((doc["repo"],dag_data["looped_rules"], overall_data["n_loop_paths"][j]))
        # j serves as index for this repo in the overall data lists
        j += 1

    with open(path, "w") as f:
        f.write("number of analysed graphs: " + str(n_analysed_graphs) + +"/"+m+"\n\n")

        f.write("max_n_logical_in_one_path (max number of times a logical rule was repeated per repo): \n")
        loop_counts = set(overall_data["max_n_logical_in_one_path"])
        for c in loop_counts:
            f.write("repeat_count = "+str(c)+": occurred "+str(overall_data["max_n_logical_in_one_path"].count(c))+" times\n")
        f.write("\n\n")

        lists_data = dict()
        for datum in ["n_paths", "n_loop_paths", "avg_logical_by_length", "median_logical_by_length", "min_logical_by_length"]:
            data_list = overall_data[datum]
            data_list.sort()
            # print("data_list", datum, len(data_list))
            lists_data[datum] = {
                "p25": data_list[int(len(data_list) / 4)],
                "p50": data_list[int(len(data_list) / 2)],
                "p75": data_list[int(len(data_list) * 3 / 4)],
                "avg": sum(data_list) / len(data_list),
                "min": data_list[0],
                "max": data_list[len(data_list) - 1]
            }

        f.write("Distributions of dag characteristics:\n")
        for datum in lists_data.keys():
            f.write(datum + ": ")
            data = lists_data[datum]
            for t in data.keys():
                f.write(t + "=" + str(data[t]) + ", ")
            f.write("\n")

        f.write("\nrepos with loops:\nrepo name, repeated rule name, number of paths with rule repetition\n")
        for repo in overall_data["loop_repos"]:
            f.write(str(repo)+"\n")
