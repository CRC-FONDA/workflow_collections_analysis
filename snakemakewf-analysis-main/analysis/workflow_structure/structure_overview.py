# from db_operations.workflow_structure.build_worflow import test_for_one_repo, scan_all_trees
# from db_operations.workflow_structure.control_flow import scan_all_contexts
# from db_operations.workflow_structure.collection_analysis import (
#    probe,
#    get_metadata,
#    reasons_for_one_rule_dags,
#    render_dot_graphs,
#    analyse_dot_graphs_from_directory,
#)
from .graph_analysis.parallelism import update_parallelism_data
from db_operations.db_connector import DBConnector
db = DBConnector()

update_parallelism_data()
print("DONE!")



query = db.workflow_structures.find({"graph": {"$exists": True}})
i = 1
for repo in query:
    n = repo["graph"]["n_nodes"]
    m = repo["graph"]["n_parallel_pairs"]
    k = None if n == 1 else m/((n*(n-1))/2)
    lr = repo["graph"]["n_logical_rules"]

    print(str(i)+"/362: "+repo["repo"])
    print(n, m)
    print(
        "n_nodes="+str(n)+"\nn_parallel_pairs="+str(m)+"\nparallelism_pairs_ratio="+str(k)+
        "\nn_logical_rules="+str(lr)+"\nlogical_rules_ratio="+str(lr/n)
    )
    i += 1



print("done!")
