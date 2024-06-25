import urllib.request


def get_raw_repos_to_txt(path):
    url_workflow_catalog_data = "https://raw.githubusercontent.com/snakemake/snakemake-workflow-catalog/main/data.js"
    req = urllib.request.Request(url_workflow_catalog_data)
    content = urllib.request.urlopen(req)
    content = str(content.read())
    content = content.split("\\n")
    with open(path, "w") as f:
        for line in content:
            f.write(line+"\n")


def get_repos_to_txt(path_raw, std_path, other_path):
    with open(path_raw, "r") as f:
        content = f.read()
    content = content.split()
    other_repos = set()
    std_repos = set()
    std_cnt = 0
    repo_cnt = 0
    repo = ""
    for i in range(len(content)):
        if "full_name" in content[i]:
            if std_cnt != repo_cnt:
                other_repos.add(repo)
                std_cnt = 0
                repo_cnt = 0
            repo = content[i+1]
            repo = repo[:-1]
            repo = repo.replace('"', '')
            repo_cnt += 1
        if "standardized" in content[i]:
            std_cnt += 1
            if content[i+1] == "true,":
                std_repos.add(repo)
            else:
                other_repos.add(repo)
    with open(std_path, "w") as f:
        for repo in std_repos:
            f.write(repo + "\n")
    with open(other_path, "w") as f:
        for repo in other_repos:
            f.write(repo + "\n")


def get_repos_from_txt(path):
    with open(path, "r") as f:
        content = f.read()
        return content.split()
