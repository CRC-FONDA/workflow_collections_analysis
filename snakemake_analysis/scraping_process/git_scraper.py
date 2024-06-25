import urllib.request
import json
from datetime import datetime
from base64 import b64decode
import time


class Scraper:
    def __init__(self, log_path, db):
        self.log_path = log_path
        self.db = db

    def get_repo_files(self, repo, access_count):
        try:
            search_url = "https://api.github.com/search/code?q=repo:" + repo
            req = urllib.request.Request(search_url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            req.add_header('Authorization', 'token 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')
            search_result = urllib.request.urlopen(req)
            search_result = json.load(search_result)
            access_count += 1
        except Exception as e:
            self.__write_log(
                "unable to find repo files: " + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ": " + repo + "; " + str(e) + "\n")
        repo_data = {}
        for file in search_result["items"]:
            file_path = file["path"]
            content_url = file["url"]
            try:
                content_req = urllib.request.Request(content_url)
                content_req.add_header('Accept', 'application/vnd.github.v3+json')
                content_req.add_header('Authorization', 'token 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')
                content_result = urllib.request.urlopen(content_req)
                content_result = json.load(content_result)
                access_count += 1
            except Exception as e:
                self.__write_log("unable to get file info: " + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ": " + repo + "; " + str(e) + "\n")
            base64_content = content_result["content"]
            content = str(b64decode(base64_content))
            repo_data[file_path] = {
                "scrape_time": datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                "base64_content": base64_content,
                "content": content
            }
        return repo_data, access_count

    def store_doc(self, doc):
        self.db.coll.insert_one(doc)

    def scrape_final_repos(self, path_std_repos, path_other_repos):

        def collate_doc(repo_name, count, standardised):
            files, count = self.get_repo_files(repo_name, count)
            new_doc = {
                "repo": repo_name,
                "standardized": standardised,
                "files": files
            }
            return new_doc, count

        def scrape_list(path, standardised):
            access_count = 0
            with open(path, "r") as f:
                repos = f.read().split()
            for repo in repos:
                if access_count > 4000:
                    start = time.time()
                    time.sleep(3700)
                    while time.time() - start < 3700:
                        time.sleep(60)
                    access_count = 0
                try:
                    doc, access_count = collate_doc(repo, access_count, standardised)
                    if not doc:
                        self.__write_log("scraping repo without results: " + datetime.today().strftime(
                            '%Y-%m-%d %H:%M:%S') + ": " + repo + "\n")
                    else:
                        self.__write_log("successfully scraped repo: " + datetime.today().strftime(
                            '%Y-%m-%d %H:%M:%S') + ": " + repo + "\n")
                    # insert new document into database
                    self.store_doc(doc)
                except Exception as e:
                    self.__write_log("unable to scrape repo: "+datetime.today().strftime('%Y-%m-%d %H:%M:%S')+": "+repo+"; "+str(e)+"\n")

        # scraping std repos
        scrape_list(path_std_repos, True)
        # wait to reset GitHub access limit
        start = time.time()
        time.sleep(3700)
        while time.time() - start < 3700:
            time.sleep(60)
        # scraping unstandardised repos
        scrape_list(path_other_repos, False)


    def scrape_repo_list(self, path_repo_list, standardised=False):
        with open(path_repo_list, "r") as f:
            repos = f.read().split()
        # stuff added to space out requests
        cnt = 0
        for repo in repos:
            print("working on: "+datetime.today().strftime('%Y-%m-%d %H:%M:%S')+": "+repo)
            cnt += 1
            if cnt > 35:
                start = time.time()
                time.sleep(5400)
                while time.time() - start < 5400:
                    time.sleep(60)
                cnt = 0
        # end of space out requests addition
            try:
                data = self.__get_repo_history(repo, standardised)
                if not data:
                    self.__write_log("scraping without results: "+datetime.today().strftime('%Y-%m-%d %H:%M:%S')+": "+repo+"\n")
                else:
                    self.__write_log("scraping successful: "+datetime.today().strftime('%Y-%m-%d %H:%M:%S')+": "+repo+"\n")
                yield data
            except:
                self.__write_log("scraping failed: "+datetime.today().strftime('%Y-%m-%d %H:%M:%S')+": "+repo+"\n")

    def __get_snakefile_path(self, repo):
        search_url = "https://api.github.com/search/code?q=rule+repo:" + repo + "+filename:Snakefile"
        req = urllib.request.Request(search_url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('Authorization', 'token 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')
        search_result = urllib.request.urlopen(req)
        search_result = json.load(search_result)
        paths = []
        # if search_result["total_count"] > 0:
        for result in search_result["items"]:
            if result["name"] == "Snakefile":
                paths.append(result["path"])
        # print("number of Snakefiles in repo: "+str(len(paths)))
        return paths

    def __get_repo_history(self, repo, standardised):
        print(repo)
        paths = self.__get_snakefile_path(repo)
        commits = []
        for path in paths:
            commits += self.__get_snakefile_history(repo, standardised, path)
        return commits

    def __get_snakefile_history(self, repo, standardised, file_path):
        print("getting history for "+repo+"/"+file_path)
        url = "https://api.github.com/repos/" + repo + "/commits?path=" + file_path
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('Authorization', 'token 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')
        content = urllib.request.urlopen(req)
        commits = json.load(content)
        for commit in commits:
            url = commit["url"]
            req = urllib.request.Request(url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            req.add_header('Authorization', 'token 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')
            content = urllib.request.urlopen(req)
            commit["commit_content"] = json.load(content)
            for file in commit["commit_content"]["files"]:
                file["sha_contents"] = self.__get_sha_content(file["contents_url"])
            commit["standardised"] = standardised
            commit["repo"] = repo
            commit["retreived"] = str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
        # print(file_path+" (commits): "+str(len(commits)))
        return commits

    def __get_sha_content(self, sha_url):
        req = urllib.request.Request(sha_url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('Authorization', 'token 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')
        content = urllib.request.urlopen(req)
        sha_content = json.load(content)
        return sha_content

    def __write_log(self, text):
        with open(self.log_path, "a") as f:
            f.write(text)




