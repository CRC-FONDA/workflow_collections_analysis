from utility.graph_utility import (
    get_graph_from_commit_dag_string,
    get_node_line_from_dag_string,
)

from ..db_connector import DBConnector
db = DBConnector()


def get_highly_parallel_rules():
    aggregate = db.workflow_structures.aggregate([
        {"$match": {
            "$and": [
                {"graph": {"$exists": True}},
                # ...
            ]
        }},
        {"$sort": {
            "graph.n_parallel_pairs": -1
        }},
    ], allowDiskUse=True)

    i = 0
    for doc in aggregate:
        i += 1
        if i < 16:
            continue
        print(doc.keys())
        print(doc["graph"].keys())
        graph = get_graph_from_commit_dag_string(doc)
        if graph:
            degree_sorted_nodes = sorted(graph.in_degree, key=lambda x: x[1], reverse=True)

            rule_lines = [get_node_line_from_dag_string(node[0], doc["dag"]) for node in degree_sorted_nodes]
            rule_names = []
            for rule_line in rule_lines:
                label_start = rule_line.find("\"") + 1
                label_end = rule_line.find("\"", label_start)
                rule_names.append(rule_line[label_start: label_end])

            print("repo:", doc["repo"])
            for i in range(len(rule_lines)):
                print(degree_sorted_nodes[i], rule_names[i], rule_lines[i])

            # try to look up rule body from final_state collection
            break
            final_state_doc = db.final_state.find({"repo": doc["repo"]}).next()
            print(final_state_doc.keys())
            #for file in final_state_doc["workflow_files"]:
            #    print(final_state_doc["files"][file].keys())
            for filename, file in final_state_doc["files"].items():
                # print(filename, file.keys())
                if "content" not in file.keys():
                    continue
                if "rule "+rule_name in file["content"]:
                    print(file["content"])

            break
