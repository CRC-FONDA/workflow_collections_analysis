from collections import Counter
from ...db_operations.db_connector import DBConnector
db = DBConnector()


def scan_config_files(path="github_scraping/analysis/full_text/results/"):
    total_repos = 0
    total_config = 0
    config_with_cotent = 0
    repos_with_config = 0
    config_suffix = []
    config_lengths = []

    total_docs = str(db.final_state.count_documents({}))
    repos = db.final_state.find()
    for repo in repos:
        total_repos += 1
        repo_has_config = False
        print("("+str(total_repos)+"/"+total_docs+") repos looked at")

        for filename, file in repo["files"].items():
            p1 = filename.rfind("/")
            filename = filename[p1:]
            if "config" not in filename:
                continue
            total_config += 1
            repo_has_config = True
            p2 = filename.find(".")
            config_suffix.append(filename[p2:])
            try:
                content = file["content"].split("\\n")
            except Exception as e:
                print("no content for "+repo["repo"]+": "+filename+": "+str(e))
                continue
            config_with_cotent += 1
            config_lengths.append(len(content))
        if repo_has_config:
            repos_with_config += 1

    # write out results
    with open(path + "config_files.txt", "w") as f:
        f.write("total repos: "+str(total_repos)+"\n")
        f.write("repos with config: " + str(repos_with_config) + "\n")
        f.write("total_config_files: "+str(total_config)+"\n")
        f.write("config files with content: "+str(config_with_cotent)+"\n")
        f.write("avg config file length: "+str(sum(config_lengths) / len(config_lengths))+"\n")
        config_lengths.sort()
        m = len(config_lengths)
        f.write("config file lengths: p25="+str(config_lengths[int(m/4)])+
                ", p50="+str(config_lengths[int(m/2)])+
                ", p75="+str(config_lengths[int(3*m/4)])+"\n\n")
        f.write("config suffixes:\n")
        suffix_counts = [(k, v) for k, v in Counter(config_suffix).items()]
        suffix_counts.sort(key=lambda _x: _x[1], reverse=True)
        for c in suffix_counts:
            f.write("    "+str(c[0])+", "+str(c[1])+"\n")


