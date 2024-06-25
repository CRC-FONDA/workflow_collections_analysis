import pymongo
from sshtunnel import SSHTunnelForwarder
from ..db_operations.db_connector import DBConnector


def copy_collection(collection_name):
    print("START OF COPYING COLLECTION:", collection_name)
    MONGO_HOST = "141.20.38.120"
    MONGO_DB = "github_scraping"

    with open("github_scraping/db_operations/mongodb_user.txt", "r") as f:
        mongodb_username = f.readline().strip()
        mongodb_password = f.readline().strip()
        remote_username = f.readline().strip()
        remote_password = f.readline().strip()

    server = SSHTunnelForwarder(
        MONGO_HOST,
        ssh_username=remote_username,
        ssh_password=remote_password,
        remote_bind_address=('127.0.0.1', 27017)
    )

    server.start()

    print("DEBUG: server started")

    # access new db
    client = pymongo.MongoClient('127.0.0.1', server.local_bind_port)  # server.local_bind_port is assigned local port
    new_db = client[MONGO_DB]

    # access old db
    old_db = DBConnector()
    old_db = old_db.db

    n_documents = old_db[collection_name].count_documents({})
    print(collection_name, "- number of documents:", n_documents)
    n = 0
    for document in old_db[collection_name].find():
        n += 1
        new_db[collection_name].insert_one(document)
        if n % 100 == 0:
            print(f"{n}/{n_documents} copied")

    server.stop()

    print("DEBUG: server stopped")

    return


def migrate_mongodb():
    COPY_COLLECTIONS = [
        "data_v1",
        "data_v3_small",
        "data_v5_final_repos",
        "workflow_structures_v1",
        "dag_histories",
        "commit_difference_pairs",
        "rules",
        "full_text_rules",

    ]

    for collection_name in COPY_COLLECTIONS:
        copy_collection(collection_name)


def create_ssh_tunnel():
    print("Do the migration.")

    import paramiko
    import socket
    import sys
    import subprocess
    from sshtunnel import SSHTunnelForwarder
    from pymongo import MongoClient

    with open("github_scraping/db_operations/mongodb_user.txt", "r") as f:
        mongodb_username = f.readline().strip()
        mongodb_password = f.readline().strip()
        remote_username = f.readline().strip()
        remote_password = f.readline().strip()

        # first tunnel connection to gruenau7
        gruenau7_ip = '141.20.21.41'
        mongodb_ip = '141.20.38.120'
        #local_port = 49205

        #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #sock.bind(('', local_port))  # set source address
        #sock.connect(('', 22))  # connect to the destination address

        gruenau7 = paramiko.SSHClient()
        gruenau7.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        gruenau7.connect(gruenau7_ip, username=remote_username, password=remote_password)
        gruenau7_transport = gruenau7.get_transport()
        dest_addr = (mongodb_ip, 22)
        local_addr = (gruenau7_ip, 22)
        gruenau7_channel = gruenau7_transport.open_channel("direct-tcpip", dest_addr, local_addr)

        mongodb = paramiko.SSHClient()
        mongodb.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        mongodb.connect(mongodb_ip, username=remote_username, password=remote_password, sock=gruenau7_channel)

        mongodb_transport = mongodb.get_transport()
        dest_addr = ('0.0.0.0', 8000)
        local_addr = ('127.0.0.1', 32034)
        mongodb_channel = mongodb_transport.open_channel("direct-tcpip", dest_addr, local_addr)

        exit()

        new_channel = mongodb_transport.open_session()
        print(new_channel.getpeername())
        print(new_channel.get_id())
        print(new_channel.get_transport())
        print(new_channel.get_name())
        print(new_channel.__getattribute__("port"))
        exit()

        #stdin, stdout, stderr = mongodb.exec_command("mongod --version")
        #print(stdout.read())  # edited#
        #exit()

        connection = MongoClient('127.0.0.1', local_port)
        db = connection["github_scraping"]
        data = db.list_collection_names()
        print(data)

        mongodb.close()
        gruenau7.close()

        # define ssh tunnel
        #server = SSHTunnelForwarder(
        #    "141.20.38.120",
        #    ssh_username=remote_username,
        #    ssh_pkey=remote_password,
        #    remote_bind_address=('141.20.21.41', 22)
        #)

        # start ssh tunnel
        #server.start()
        #server.local_bind_address

        #connection = MongoClient('127.0.0.1', server.local_bind_port)
        #db = connection["guthub_scraping"]
        #data = db.list_collection_names()
        #print(data)


