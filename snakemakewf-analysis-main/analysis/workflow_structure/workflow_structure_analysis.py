import subprocess
import graphviz
import os
import pydot
import networkx as nx
from db_operations.db_connector import DBConnector
db = DBConnector()


def get_metadata():
    coll = db.workflow_structures
    metadata = {
        "total_docs": coll.count_documents({}),
        "cloned_docs": coll.count_documents({"cloned": True}),
        "dag_docs": coll.count_documents({"dag": {"$ne": None}}),
        "dryrun_docs": coll.count_documents({"dryrun": {"$ne": None}}),
    }
    return metadata


def write_dag_pdfs():
    dag_path = "dags/"
    coll = db.workflow_structures
    query = coll.find({"dag": {"$ne": None}})
    for repo in query:
        repo_replace = repo["repo"].replace("/", "_")
        try:
            dag_txt_path = repo_replace+"_dag.txt"
            with open(dag_path+dag_txt_path, "w") as f:
                f.write(repo["dag"])
            subprocess.run(["cat " + dag_txt_path + " | dot -Tpdf > ../"+dag_path+repo_replace+"_dag.pdf"], cwd=dag_path, shell=True)
        except Exception as e:
            print("dag creation failed for "+repo["repo"])
            print(str(e))


def reasons_for_one_rule_dags():
    coll = db.workflow_structures

    total = coll.count_documents({})
    print("total documents: "+str(total))

    print("un-cloned documents: "+str(coll.count_documents({"cloned": False})))

    none_dag = coll.count_documents({"dag": None})
    print("none-dag documents: "+str(none_dag))
    print("dag documents: "+str(total-none_dag))

    query = coll.find({
        "dag": {"$ne": None},
        #"dag": {"$ne": {"$regex": 'digraph'}}
        # "dag": {"$regex": 'digraph'}
        # "dag": {"$regex": '^.*label.*'}
        })
    for repo in query:
        dag_txt = repo["dag"]
        if not "->" in dag_txt:
            print(repo["repo"] + ": " + repo["scrape_time"])
            print("----------------------------------------------------------------")
            print(repo["dag"])
            print("----------------------------------------------------------------")
            print(repo["dryrun"])
            print("################################################################")


def render_dot_graphs():
    dag_path = "dags/"
    coll = db.workflow_structures
    query = coll.find({
        "dag": {"$ne": None},
    })
    for repo in query:
        repo_string = repo["repo"].replace("/", "_")
        dag_string = repo["dag"]
        dag_string = dag_string[dag_string.find("digraph"):]

        graph = graphviz.Source(dag_string)
        graph.render(outfile=dag_path+repo_string+".png", format="png")


def analyse_dot_graphs_from_directory(path="dags/"):
    dags_directory = os.fsencode(path)
    results_path = "results/dag_analysis.txt"

    total_n = 0
    n_nodes_list = []
    avg_degree_list = []
    max_degree_list = []
    longest_path_list = []

    for file in os.listdir(dags_directory):
        filename = os.fsdecode(file)
        if filename.endswith(".gv"):
            print(str(total_n+1)+"/362")
            repo_string = filename[:filename.find(".gv")]
            print(str(total_n)+": repo: "+repo_string)
            graph = nx.MultiDiGraph(nx.nx_pydot.read_dot(path+filename))
            graph = graph.reverse()
            print("edges: "+str(list(graph.edges)))
            print("is directed = "+str(graph.is_directed()))
            print("is tree = "+str(nx.is_tree(graph)))
            print("longest path: "+str(nx.dag_longest_path(graph)))
            n_nodes_list.append(graph.number_of_nodes())
            longest_path_list.append((len(nx.dag_longest_path(graph))))
            # print("number of nodes: "+str(graph.number_of_nodes()))
            degree_sequence = sorted(((n, d) for n, d in graph.degree()), key=lambda x: x[1], reverse=True)
            # print("degree_sequence: "+str(degree_sequence))
            max_degree_list.append(degree_sequence[0][1])
            degree_sum = sum([d for n, d in degree_sequence])
            avg_degree = degree_sum / len(degree_sequence)
            avg_degree_list.append(avg_degree)
            total_n += 1
            continue
        else:
            continue

    n_nodes_list.sort()
    n_nodes_p25 = n_nodes_list[int(len(n_nodes_list) / 4)]
    n_nodes_p50 = n_nodes_list[int(len(n_nodes_list) / 2)]
    n_nodes_p75 = n_nodes_list[int(len(n_nodes_list) * 3 / 4)]
    n_nodes_avg = sum(n_nodes_list) / len(n_nodes_list)
    avg_degree_list.sort()
    avg_degree_p25 = avg_degree_list[int(len(avg_degree_list) / 4)]
    avg_degree_p50 = avg_degree_list[int(len(avg_degree_list) / 2)]
    avg_degree_p75 = avg_degree_list[int(len(avg_degree_list) * 3 / 4)]
    avg_degree_avg = sum(avg_degree_list) / len(avg_degree_list)
    max_degree_list.sort()
    max_degree_p25 = max_degree_list[int(len(max_degree_list) / 4)]
    max_degree_p50 = max_degree_list[int(len(max_degree_list) / 2)]
    max_degree_p75 = max_degree_list[int(len(max_degree_list) * 3 / 4)]
    max_degree_avg = sum(max_degree_list) / len(max_degree_list)
    longest_path_list.sort()
    longest_path_p25 = longest_path_list[int(len(longest_path_list) / 4)]
    longest_path_p50 = longest_path_list[int(len(longest_path_list) / 2)]
    longest_path_p75 = longest_path_list[int(len(longest_path_list) * 3 / 4)]
    longest_path_avg = sum(longest_path_list) / len(longest_path_list)

    with open(results_path, "w") as f:
        f.write("number of graphs = "+str(total_n)+"\n\n")
        f.write("n_nodes_avg = "+str(n_nodes_avg)+"\n")
        f.write("n_nodes_p25 = "+str(n_nodes_p25)+", n_nodes_p50 = "+str(
            n_nodes_p50)+", n_nodes_p75 = "+str(n_nodes_p75)+"\n")
        f.write(str(n_nodes_list))
        f.write("\n\n")
        f.write("avg_degree_avg = "+str(avg_degree_avg)+"\n")
        f.write("avg_degree_p25 = "+str(avg_degree_p25)+", avg_degree_p50 = "+str(
            avg_degree_p50)+", avg_degree_p75 = "+str(avg_degree_p75)+"\n")
        f.write(str(avg_degree_list))
        f.write("\n\n")
        f.write("max_degree_avg = " + str(max_degree_avg) + "\n")
        f.write("max_degree_p25 = " + str(max_degree_p25) + ", max_degree_p50 = " + str(
            max_degree_p50) + ", max_degree_p75 = " + str(max_degree_p75) + "\n")
        f.write(str(max_degree_list))
        f.write("\n\n")
        f.write("longest_path_avg = " + str(longest_path_avg) + "\n")
        f.write("longest_path_p25 = " + str(longest_path_p25) + ", longest_path_p50 = " + str(
            longest_path_p50) + ", longest_path_p75 = " + str(longest_path_p75) + "\n")
        f.write(str(longest_path_list))
        f.write("\n\n")


def probe():
    coll = db.workflow_structures

    total = coll.count_documents({})
    print("total documents: " + str(total))
    print("un-cloned documents: " + str(coll.count_documents({"cloned": False})))
    none_dag = coll.count_documents({"dag": None})
    print("none-dag documents: " + str(none_dag))
    print("dag documents: " + str(total - none_dag)+", ratio: "+str((total - none_dag) / total))

    one_node = 0
    query = coll.find({
        "dag": {"$ne": None},
    })
    for repo in query:
        dag_txt = repo["dag"]
        if "->" not in dag_txt:
            one_node += 1
    print("one node dags: "+str(one_node)+", ratio: "+str(one_node / (total - none_dag))+", ratio of total documents: "+str(one_node / total))

    query = coll.find({"dag": None, "cloned": True})
    i = 0
    for repo in query:
        #print(repo.keys())
        #print(str(i)+": "+repo["repo"]+", "+repo["scrape_time"]+", "+str(repo["cloned"]))
        i += 1

