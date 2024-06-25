import networkx as nx
import pydot
import matplotlib.pyplot as plt
from ..db_operations.db_connector import DBConnector
db = DBConnector()


def extract_logical_rule(node_label):
    if "\n" in node_label:
        return node_label[:node_label.find("\n")]
    else:
        return node_label


def get_node_label(repo_string, node, dag_directory="github_scraping/db_operations/workflow_structure/dags/"):
    with open(dag_directory+repo_string+".gv", "r") as f:
        content = f.read()
    node_label = content.find(str(node)+"[label = ")
    label_start = content.find("\"", node_label)+1
    label_end = content.find("\"", label_start)
    return content[label_start: label_end]


def get_dag_history_node_label(_id, node, dag_string=None):
    if not dag_string:
        query = db.dag_histories.find({"_id": _id})
        dag_string = query.next()["dag"]
    node_label = dag_string.find(str(node) + "[label = ")
    label_start = dag_string.find("\"", node_label) + 1
    label_end = dag_string.find("\"", label_start)
    return dag_string[label_start: label_end]


def get_node_line_from_dag_string(node_id, dag_string):
    node_line = dag_string.find(node_id + "[label = ")
    node_line_end = dag_string.find("\n", node_line)
    return dag_string[node_line: node_line_end]


def get_node_label_map_from_dag_string(dag_string):
    label_map = dict()
    for line in dag_string.split("\n"):
        node_label = line.find("[label = ")
        if node_label >= 0:
            node = line[:node_label].strip()
            label_start = line.find("\"", node_label) + 1
            label_end = line.find("\"", label_start)
            label = line[label_start: label_end]
            label_map[node] = label
    return label_map


def get_n_nodes_from_dag_string(dag_string):
    lines = dag_string.split("\n")
    for i in range(len(lines)):
        if "->" in lines[i]:
            line = lines[i-1]
            p = line.find("[label = ")
            n = int(line[:p].strip())
            return n
    return None


def update_collection(repo, field, value):
    if "/" not in repo:
        p = repo.find("_")
        repo = repo[:p] + "/" + repo[p+1:]
    status = db.workflow_structures.find_one_and_update(
        {"repo": repo},
        {"$set": {field: value}}
    )
    if status is None:
        print("Unable to update "+repo+" with field="+str(field)+", value="+str(value))


def update_dag_history_data(_id, field, value):
    status = db.dag_histories.find_one_and_update(
        {"_id": _id},
        {"$set": {field: value}}
    )
    if status is None:
        print("Unable to update " + str(_id) + " with field=" + str(field) + ", value=" + str(value))


def save_graph_image(graph, path):
    fig, ax = plt.subplots()
    nx.draw(graph)  # default spring_layout
    plt.savefig(path)


def get_graph_from_commit_dag_string(commit):
    dag_string = commit["dag"]
    try:
        P_list = pydot.graph_from_dot_data(dag_string)
        if not P_list:
            dag_string = dag_string.split("\n")
            dag_string = dag_string[1:]
            dag_string = "\n".join(dag_string)
            P_list = pydot.graph_from_dot_data(dag_string)
        if not P_list:
            print("Unable to build graph from dag_string for " + commit["repo"] + "\n")
        else:
            print("successfully built P_list for graph construction")
        graph = nx.drawing.nx_pydot.from_pydot(P_list[0])
        return graph
    except Exception as e:
        print("Unable to build graph from dag_string for " + commit["repo"] + ": " + str(e) + "\n")
        return None
