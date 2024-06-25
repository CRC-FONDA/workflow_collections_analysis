import pydot
import networkx as nx
from .load_graphs import read_graphs_from_directory, get_dag_history_graphs
from utility.graph_utility import (
    get_node_label,
    get_dag_history_node_label,
    update_collection,
    update_dag_history_data,
)
from utility.dag_histories_utility import (
    get_commit_pairs_of_graph_change,
)
from db_operations.db_connector import DBConnector
db = DBConnector()


def determine_parallelism(graph, repo=None, local=True, _id=None, dag_string=None):
    def extract_logical_rule(node_label):
        if "\n" in node_label:
            return node_label[:node_label.find("\n")]
        else:
            return node_label

    # undirected_graph = graph.to_undirected()
    #print("    calculate transitive closure")
    tc = nx.transitive_closure(graph)
    #print("    calculate non edges")
    non_edges = [e for e in nx.non_edges(tc)]
    #print("    calculate parallel pairs")
    parallel_dict = {}
    for edge in non_edges:
        edge_key = tuple(sorted((int(edge[0]), int(edge[1]))))
        if edge_key in parallel_dict:
            parallel_dict[edge_key] = 2
        else:
            parallel_dict[edge_key] = 1
    parallel_pairs = [key for key, value in parallel_dict.items() if value == 2]

    #print("    collect logical rules")
    logical_rules = set()
    for node in graph.nodes:
        if local:
            label = get_node_label(repo, node)
        else:
            label = get_dag_history_node_label(_id, node, dag_string=dag_string)
        logical_rules.add(extract_logical_rule(label))

    #print("    collecting miscellaneous data")
    degree_sequence = sorted(((n, d) for n, d in graph.degree()), key=lambda x: x[1], reverse=True)
    max_degree = degree_sequence[0][1]
    degree_sum = sum([d for n, d in degree_sequence])
    avg_degree = degree_sum / len(degree_sequence)

    return (
        graph.number_of_nodes(),
        len(parallel_pairs),
        len(logical_rules),
        nx.dag_longest_path_length(graph),
        max_degree,
        avg_degree
    )


def update_parallelism_data():
    i = 1
    for repo, graph in read_graphs_from_directory():
        print(str(i)+"/362: "+repo)
        (
            n_nodes,
            n_parallel_pairs,
            n_logical_rules,
            longest_path,
            max_degree,
            avg_degree,
        ) = determine_parallelism(repo, graph)
        update_collection(repo, "graph.n_nodes", n_nodes)
        update_collection(repo, "graph.n_parallel_pairs", n_parallel_pairs)
        update_collection(repo, "graph.n_logical_rules", n_logical_rules)
        update_collection(repo, "graph.longest_path", longest_path)
        update_collection(repo, "graph.max_degree", max_degree)
        update_collection(repo, "graph.avg_degree", avg_degree)
        i += 1


def update_dag_histories_parallelism_data():
    n = db.dag_histories.count_documents({})
    i = 1
    for _id, repo, graph in get_dag_history_graphs():
        print("("+str(i)+"/"+str(n)+") "+repo)
        # skip if document has already been updated with parallelism data
        query = db.dag_histories.find({"$and": [
            {"_id": _id},
            {"graph": {"$exists": True}}
        ]})
        probe = next(query, None)
        if probe:
            print("skipping")
            continue
        (
            n_nodes,
            n_parallel_pairs,
            n_logical_rules,
            longest_path,
            max_degree,
            avg_degree,
        ) = determine_parallelism(graph, repo=repo, local=False, _id=_id)
        update_dag_history_data(_id, "graph.n_nodes", n_nodes)
        update_dag_history_data(_id, "graph.n_parallel_pairs", n_parallel_pairs)
        update_dag_history_data(_id, "graph.n_logical_rules", n_logical_rules)
        update_dag_history_data(_id, "graph.longest_path", longest_path)
        update_dag_history_data(_id, "graph.max_degree", max_degree)
        update_dag_history_data(_id, "graph.avg_degree", avg_degree)
        i += 1


def update_dag_histories_parallelism_data_for_difference_commits():
    log_path = "script_log.txt"
    with open(log_path, "w") as f:
        f.write("\n")
    i = 0
    for pair in get_commit_pairs_of_graph_change():
        i += 1
        if i % 10 == 0:
            with open(log_path, "a") as f:
                f.write("Gone through "+str(i)+" commit pairs.\n")
        for commit in pair:
            # skip if document has already been updated with parallelism data of has no dag
            query = db.dag_histories.find({"$and": [
                {"_id": commit["_id"]},
                {"graph": {"$exists": True}},
                {"dag": {"$ne": None}}
            ]})
            probe = next(query, None)
            if probe:
                with open(log_path, "a") as f:
                    f.write("Skipping repo="+str(commit["repo"])+", commit_number="+str(commit["commit_number"])+"\n")
                continue

            # do dag metadata analysis for this commit
            dag_string = commit["dag"]
            try:
                P_list = pydot.graph_from_dot_data(dag_string)
                if not P_list:
                    dag_string = dag_string.split("\n")
                    dag_string = dag_string[1:]
                    dag_string = "\n".join(dag_string)
                    P_list = pydot.graph_from_dot_data(dag_string)
                if not P_list:
                    with open(log_path, "a") as f:
                        f.write(
                            "Unable to build graph from dag_string for " + commit["repo"] + ", commit_number=" + str(
                                commit["commit_number"])+"\n")
                graph = nx.drawing.nx_pydot.from_pydot(P_list[0])
            except Exception as e:
                with open(log_path, "a") as f:
                    f.write(
                        "Unable to build graph from dag_string for " + commit["repo"] + ", commit_number=" + str(
                            commit["commit_number"])+", "+str(e)+"\n")
                continue

            _id = commit["_id"]
            (
                n_nodes,
                n_parallel_pairs,
                n_logical_rules,
                longest_path,
                max_degree,
                avg_degree,
            ) = determine_parallelism(graph, repo=commit["repo"], local=False, _id=_id, dag_string=commit["dag"])
            update_dag_history_data(_id, "graph.n_nodes", n_nodes)
            update_dag_history_data(_id, "graph.n_parallel_pairs", n_parallel_pairs)
            update_dag_history_data(_id, "graph.n_logical_rules", n_logical_rules)
            update_dag_history_data(_id, "graph.longest_path", longest_path)
            update_dag_history_data(_id, "graph.max_degree", max_degree)
            update_dag_history_data(_id, "graph.avg_degree", avg_degree)




