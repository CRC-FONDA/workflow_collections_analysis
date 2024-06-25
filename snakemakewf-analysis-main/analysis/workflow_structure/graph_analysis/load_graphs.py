import os
import pydot
import networkx as nx
from db_operations.db_connector import DBConnector
db = DBConnector()


def read_graphs_from_directory(path="github_scraping/db_operations/workflow_structure/dags/"):
    dags_directory = os.fsencode(path)
    for file in os.listdir(dags_directory):
        filename = os.fsdecode(file)
        if filename.endswith(".gv"):
            repo_string = filename[:filename.find(".gv")]
            graph = nx.DiGraph(nx.nx_pydot.read_dot(path + filename))
            # TODO: should we reverse the edges?
            # graph = graph.reverse()
            yield repo_string, graph


def get_dag_history_graphs():
    collection = db.dag_histories
    documents = collection.find({"$and": [
        {"dag": {"$exists": True}},
        {"dag": {"$ne": None}}
    ]})

    for doc in documents:
        P_list = pydot.graph_from_dot_data(doc["dag"])
        graph = nx.drawing.nx_pydot.from_pydot(P_list[0])
        yield doc["_id"], doc["repo"], graph
