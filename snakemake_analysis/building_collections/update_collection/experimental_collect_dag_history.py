import subprocess
import os

from db_operations.db_connector import DBConnector
db = DBConnector()


def get_repo_directories(repo):
    repo_suf = repo[repo.find("/"):]
    repo_string_replaced = repo.replace("/", "_")
    repo_dir = "github_scraping/dag_histories/" + repo_string_replaced
    return repo_dir, repo_suf


def clone_repo(repo):
    # clone the repo first
    repo_dir, repo_suf = get_repo_directories(repo)

    print("current working directory:")
    subprocess.run(["pwd"])

    subprocess.run(["mkdir", repo_dir])
    try:
        result = subprocess.run(
            ["git", "clone", "https://github.com/" + repo],
            cwd=repo_dir + "/",
            text=True,
            timeout=600,
            # input = input_string.encode(),
        )
        if result.returncode == 0:
            cloned = True
        else:
            print("for " + repo + " an error occurred during cloning: ")
            cloned = False
    except Exception as e:
        print("for " + repo + " an error occurred during cloning: " + str(e))
        cloned = False
    return cloned


def get_commits_from_git_log(repo):
    repo_dir, repo_suf = get_repo_directories(repo)
    try:
        result = subprocess.run(
            ["git", "log"],
            capture_output=True,
            text=True,
            cwd=repo_dir + repo_suf,
            timeout=1200,
            # stdout=subprocess.PIPE,
        )
        if result.returncode == 0:
            git_log = result.stdout
        else:
            print("for " + repo + " an error occurred during git log collection")
            return None
    except Exception as e:
        print("for " + repo + " an error occurred during git log collection: "+str(e))
        return None
    commits = []
    lines = git_log.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].startswith("commit "):
            sha = lines[i].split(" ")[1].strip()
            message = lines[i + 4].strip()
            date = " ".join(lines[i+2].split(" ")[1:])
            author = " ".join(lines[i+1].split(" ")[1:])
            commits.append((sha, message, date, author))
            i += 6
            continue
        i += 1
    return commits


def set_repo_to_commit(repo, sha):
    repo_dir, repo_suf = get_repo_directories(repo)
    subprocess.run(
        ["git", "checkout", sha],
        capture_output=True,
        text=True,
        cwd=repo_dir + repo_suf,
        timeout=1200,
        # stdout=subprocess.PIPE,
    )


def store_results(repo, commit_number, commit, dag_string, dryrun_string):
    doc = {
        "repo": repo,
        "commit_number": commit_number,
        "sha": commit[0],
        "commit_message": commit[1],
        "date": commit[2],
        "author": commit[3],
        "dag": dag_string,
        "dryrun": dryrun_string,
    }
    try:
        db.dag_histories.insert_one(doc)
    except Exception as e:
        print("error while storing for " + repo + ", " + commit[0])


def build_dag_and_dryrun(repo, sha):
    dag_string = None
    dryrun_string = None
    repo_dir, repo_suf = get_repo_directories(repo)
    try:
        result = subprocess.run(
            ["snakemake", "--dag"],
            capture_output=True,
            text=True,
            cwd=repo_dir + repo_suf,
            timeout=1200,
            # stdout=subprocess.PIPE,
        )

        if result.returncode == 0:
            dag_string = result.stdout
        else:
            print("error for " + repo + " while dag building")
    except Exception as e:
        print("error for "+repo+" while dag building: "+str(e))

    # create dag png
    try:
        subprocess.run(["snakemake --dag | dot -Tpdf > ../dag_"+sha+".pdf"], cwd=repo_dir + repo_suf, shell=True)
    except Exception as e:
        print("error for " + repo + " while dag png building: " + str(e))

    # execute dryrun
    try:
        result = subprocess.run(
            ["snakemake", "-n", "-r"],
            capture_output=True,
            text=True,
            cwd=repo_dir + repo_suf,
            # stdout=subprocess.PIPE,
        )
        if result.returncode == 0:
            dryrun_string = result.stdout
        else:
            print("error for " + repo + " while dag dryrun")
    except Exception as e:
        print("error for " + repo + " while dag dryrun: " + str(e))

    # return results
    return dag_string, dryrun_string


def run_update(candidates):
    # example candidate : blab/norovirus
    # candidates = candidates[:1]
    for repo in candidates:
        # skip if repo is already in database
        query = db.dag_histories.find({"repo": repo})
        probe = next(query, None)
        if probe:
            continue

        print("----------------------------------------------------")
        print("looking at dag history of "+repo)

        cloned = clone_repo(repo)

        if cloned:
            commits = []
            commits = get_commits_from_git_log(repo)
            i = 0
            m = str(len(commits))
            for commit in commits:

                i += 1
                print("("+str(i)+"/"+m+") looking at commit: "+commit[0])
                set_repo_to_commit(repo, commit[0])

                # build dag for current state of repo
                dag_string, dryrun_string = build_dag_and_dryrun(repo, commit[0])
                store_results(repo, i, commit, dag_string, dryrun_string)

        # clean up repo
        repo_dir, repo_suf = get_repo_directories(repo)
        if os.path.exists(repo_dir + repo_suf):
            subprocess.run(["yes | rm -r " + repo_dir + repo_suf], shell=True)


def fill_data_gaps():
    # repos:
    # already clones:
    # (1) 'Ax-Sch/AlphScore'
    pass

