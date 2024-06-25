from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder
from bson.objectid import ObjectId
import base64


class NewDBConnector:
    def __init__(self, db_name=None):
        if db_name is None:
            self.db_name = "git_scraping"
        else:
            self.db_name = db_name

        MONGO_HOST = "141.20.38.120"
        MONGO_DB = "github_scraping"

        with open("github_scraping/db_operations/mongodb_user.txt", "r") as f:
            mongodb_username = f.readline().strip()
            mongodb_password = f.readline().strip()
            remote_username = f.readline().strip()
            remote_password = f.readline().strip()

        self.server = SSHTunnelForwarder(
            MONGO_HOST,
            ssh_username=remote_username,
            ssh_password=remote_password,
            remote_bind_address=('127.0.0.1', 27017)
        )

        self.server.start()

        print("DEBUG: server started")

        # access new db
        self.client = MongoClient('127.0.0.1', self.server.local_bind_port)

        self.db = self.client[self.db_name]
        # full commits is on of the two databases for commit histories
        self.full_commits = self.db["data_v1"]
        # brief hunks is another database for commit histories focusing on small changes as I recall
        self.brief_hunks = self.db["data_v3_small"]
        # final_state is the main collection for complete final versions of the workflows
        self.final_state = self.db["data_v5_final_repos"]
        # final state ful repo is an abandoned attempt to collect more data on thise repositories for which we built dags
        self.final_state_full_repo = self.db["final_state_full_repo"]
        # workflow structures is a collection for the dags we were able to built
        self.workflow_structures = self.db["workflow_structures_v1"]
        self.dag_histories = self.db["dag_histories"]
        self.commit_difference_pairs = self.db["commit_difference_pairs"]
        self.rules = self.db["rules"]
        self.full_text_rules = self.db["full_text_rules"]


class DBConnector:
    def __init__(self, connection_string=None, db_name=None):
        if connection_string is None:
            self.connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
        else:
            self.connection_string = connection_string
        if db_name is None:
            self.db_name = "git_scraping"
        else:
            self.db_name = db_name
        self.client = MongoClient(self.connection_string)
        self.db = self.client[self.db_name]
        # full commits is on of the two databases for commit histories
        self.full_commits = self.db["data_v1"]
        # brief hunks is another database for commit histories focusing on small changes as I recall
        self.brief_hunks = self.db["data_v3_small"]
        # final_state is the main collection for complete final versions of the workflows
        self.final_state = self.db["data_v5_final_repos"]
        # final state ful repo is an abandoned attempt to collect more data on thise repositories for which we built dags
        self.final_state_full_repo = self.db["final_state_full_repo"]
        # workflow structures is a collection for the dags we were able to built
        self.workflow_structures = self.db["workflow_structures_v1"]
        self.dag_histories = self.db["dag_histories"]
        self.commit_difference_pairs = self.db["commit_difference_pairs"]
        self.rules = self.db["rules"]
        self.full_text_rules = self.db["full_text_rules"]

    def get_hunk_fulltext(self, hunk, filename):
        commit = self.full_commits.find({"_id": hunk["old_id"]}).next()
        files = commit["commit_content"]["files"]
        content = []
        for file in files:
            if file["filename"] == filename:
                try:
                    raw_content = file["sha_contents"]["content"]
                    content.append(str(base64.b64decode(raw_content)).split("\\n"))
                except KeyError as e:
                    content.append([])
                    print("No content for filename :"+str(e))
                    print("In hunk: "+str(hunk))
        if len(content) != 1:
            raise ValueError("could not find fulltext for "+filename+", "+str(hunk["old_id"]))
        return content[0]

