import numpy as np
from sklearn.cluster import KMeans

from .data_preparation.create_vocabulary import create_shell_vocabulary
from .vectorizer import ShellCodeBagOfWordsVectorizer, ShellCodeTFIDFVectorizer
from ...db_operations.db_connector import DBConnector
db = DBConnector()


def fit_kmeans_clustering(level=None, f0=None):
    # vectorizer = ShellCodeBagOfWordsVectorizer()
    vectorizer = ShellCodeTFIDFVectorizer()
    if level is not None:
        f1 = f0
    else:
        f1 = {"shell_lines": {"$exists": True, "$not": {"$size": 0}}}
    rules = db.rules.find(f1)

    raw_data = []
    for rule in rules:
        v = vectorizer.vectorize(rule["shell_lines"], blacklist=True, clean_data=True)
        raw_data.append(v)

    data = np.array(raw_data)
    print("Clustering data shape:", data.shape)
    # print(data)

    return KMeans(n_clusters=5, n_init="auto").fit(data)


def write_kmeans_clustering_to_db():
    kmeans = fit_kmeans_clustering()
    print("Clustering completed")

    vectorizer = ShellCodeTFIDFVectorizer(cleaned_data=True)
    f1 = {"shell_lines": {"$exists": True, "$not": {"$size": 0}}}
    rules = db.rules.find(f1)
    for rule in rules:
        #for line in rule["shell_lines"]:
        #    print(line)
        v = vectorizer.vectorize(rule["shell_lines"], blacklist=True, clean_data=True)
        prediction = kmeans.predict([v])[0].item()
        # print(type(prediction), prediction)

        f1 = {"_id": rule["_id"]}
        newvalues = {"$set": {'hierarchical_kmeans': {"level_1": prediction}}}
        db.rules.update_one(f1, newvalues)


def write_deeper_level_kmeans_clustering_to_db(level):
    f1 = {
            "shell_lines": {"$exists": True, "$not": {"$size": 0}},
            "$or": [
                {"hierarchical_kmeans.level_3": 1},
                {"hierarchical_kmeans.level_3": 2},
                {"hierarchical_kmeans.level_3": 4},
            ],
        }
    kmeans = fit_kmeans_clustering(level=level, f0=f1)
    print("Clustering completed")

    vectorizer = ShellCodeTFIDFVectorizer(cleaned_data=True)
    rules = db.rules.find(f1)
    for rule in rules:
        #for line in rule["shell_lines"]:
        #    print(line)
        v = vectorizer.vectorize(rule["shell_lines"], blacklist=True, clean_data=True)
        prediction = kmeans.predict([v])[0].item()
        # print(type(prediction), prediction)

        f2 = {"_id": rule["_id"]}
        newvalues = {"$set": {'hierarchical_kmeans.level_4': prediction}}
        db.rules.update_one(f2, newvalues)


def print_cluster_sizes(clustering_name, level=None):
    if level is None:
        f1 = {clustering_name: {"$exists": True}}
    else:
        f1 = {clustering_name + "." + level: {"$exists": True}}
    rules = db.rules.find(f1)
    clusters = [[], [], [], [], []]
    for rule in rules:
        clusters[rule[clustering_name][level]].append(rule)
    print("Cluster: ", clustering_name, ",", "Level:", str(level))
    for i in range(5):
        print(" ", i, len(clusters[i]))


def show_cluster_examples(clustering_name, level=None, cluster_id=0):
    if level is None:
        f1 = {clustering_name: {"$exists": True}}
    else:
        f1 = {clustering_name + "." + level: {"$exists": True}}
    rules = db.rules.find(f1)
    clusters = [[], [], [], [], []]
    for rule in rules:
        clusters[rule[clustering_name][level]].append(rule)

    for rule in clusters[cluster_id]:
        for line in rule["shell_lines"]:
            print(line)
        input("...")


def kmeans_clustering():
    # create_shell_vocabulary()
    # write_kmeans_clustering_to_db()
    # write_deeper_level_kmeans_clustering_to_db(level=4)
    print_cluster_sizes("hierarchical_kmeans", level="level_4")
    show_cluster_examples("hierarchical_kmeans", level="level_4", cluster_id=0)

    # f1 = {clustering: {"$exists": True}}
    #rules = db.rules.find({})
    #for rule in rules:
    #    print(rule.keys())
    #    input("...")





