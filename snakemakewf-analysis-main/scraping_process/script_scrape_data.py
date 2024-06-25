from db_operations.db_connector import DBConnector
from git_scraper import Scraper
from datetime import datetime
import urllib.request
import json

connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
db_name = "git_scraping"
coll_name = "data_v5_final_repos"
other_repos = "repo_lists/other_repos.txt"
std_repos = "repo_lists/std_repos.txt"
log_path = "../logs/scraping_v2.log"


def original_scrape():
    db = DBConnector(connection_string, db_name, coll_name)
    scraper = Scraper(log_path)

    doc_gen = scraper.scrape_repo_list(std_repos, standardised=False)

    for doc_list in doc_gen:
        for doc in doc_list:
            try:
                db.store_doc(doc)
            except:
                with open(log_path, "a") as f:
                    f.write("storing document failed: " + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ": " + doc[
                        "repo"] + "\n")


def final_repos_scrape():
    db = DBConnector(connection_string, db_name, coll_name)
    scraper = Scraper(log_path, db)
    scraper.scrape_final_repos(std_repos, other_repos)


def get_rate_limit():
    url = "https://api.github.com/rate_limit"
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/vnd.github.v3+json')
    req.add_header('Authorization', 'token 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')
    result = urllib.request.urlopen(req)
    result = json.load(result)
    print(result)


final_repos_scrape()
#print("done!")
