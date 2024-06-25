from db_operations.db_connector import DBConnector
from collections import defaultdict

db = DBConnector()


def get_one_parameter_commits():
    query = db.full_commits.aggregate([
        {"$match": {"commit_content.files.filename": {"$regex": "Snakefile"}}},
        {"$unwind": "$commit_content.files"},
        {"$match": {"commit_content.files.filename": {"$regex": "Snakefile"}, "commit_content.files.additions": 1,
                    "commit_content.files.deletions": 1}},
        {"$project": {"commit_content.files.filename": 1, "_id": 1, "repo": 1,
                      "commit_content.files.additions": 1, "commit_content.files.deletions": 1,
                      "commit_content.files.changes": 1, "commit_content.files.patch": 1}}
    ])
    results = []
    for commit in query:
        try:
            def check_comment(line):
                return True if line[1:].split()[0] != "#" else False

            def right_hand_string(line):
                pos = line.find('=')
                rhs = line[pos + 1:].strip()
                rhs = rhs.replace(',', '')
                return True if rhs[0] == '"' and rhs[-1] == '"' else False

            def contains_digit(line):
                return any(char.isdigit() for char in line)

            patch = commit["commit_content"]["files"]["patch"]
            patch = patch.split("\n")
            for line in patch:
                if line[0] == "-":
                    del_line = line
                elif line[0] == "+":
                    add_line = line
            if del_line.count('=') != 1 or add_line.count('=') != 1:
                continue
            if right_hand_string(add_line) and right_hand_string(del_line):
                continue
            if not contains_digit(add_line) or not contains_digit(del_line):
                continue
            if check_comment(add_line) and check_comment(del_line):
                results.append((commit, del_line, add_line))
        except KeyError:
            print("no patch error for: ")
            print(commit)
    return results


def get_one_rule_commits(self):
    query = db.full_commits.aggregate([
        {"$match": {"commit_content.files.filename": {"$regex": "Snakefile"}}},
        {"$unwind": "$commit_content.files"},
        {"$match": {"commit_content.files.filename": {"$regex": "Snakefile"}}},
        {"$project": {"commit_content.files.filename": 1, "_id": 1, "repo": 1,
                      "commit_content.files.additions": 1, "commit_content.files.deletions": 1,
                      "commit_content.files.changes": 1, "commit_content.files.patch": 1}}
    ])
    results = []
    for commit in query:
        try:
            patch = commit["commit_content"]["files"]["patch"]
            patch = patch.split("\n")
            del_lines = []
            add_lines = []
            for line in patch:
                if line[0] == "-":
                    del_lines.append(line)
                elif line[0] == "+":
                    add_lines.append(line)
            def check_for_rule(lines):
                if not lines or "rule" not in lines[0]:
                    return False
                if len(lines) == 1:
                    return False
                if lines[0][1:].split()[0] != "rule":
                    return False
                for line in lines[1:]:
                    if "rule" in line:
                        return False
                return True
            if check_for_rule(del_lines) and check_for_rule(add_lines):
                results.append((commit, del_lines, add_lines))
        except KeyError:
            #print("no patch error for: ")
            #print(commit)
            pass
    return results


def get_add_del_rule_commits(self):
    query = db.full_commits.aggregate([
        {"$unwind": "$commit_content.files"},
        {"$match": {"commit_content.files.filename": {"$regex": "Snakefile"}}},
        {"$project": {"commit_content.files.filename": 1, "_id": 1, "repo": 1,
                      "commit_content.files.additions": 1, "commit_content.files.deletions": 1,
                      "commit_content.files.changes": 1, "commit_content.files.patch": 1}}
    ])
    add_results = []
    del_results = []
    for commit in query:
        try:
            patch = commit["commit_content"]["files"]["patch"]
            patch = patch.split("\n")
            del_lines = []
            add_lines = []
            for line in patch:
                if line[0] == "-":
                    del_lines.append(line)
                elif line[0] == "+":
                    add_lines.append(line)
            def check_for_rule(lines):
                if not lines or "rule" not in lines[0]:
                    return False
                if len(lines) == 1:
                    return False
                if lines[0][1:].split()[0] != "rule":
                    return False
                for line in lines[1:]:
                    if "rule" in line:
                        return False
                return True
            if check_for_rule(add_lines) and len(del_lines) == 0:
                add_results.append((commit, add_lines))
            elif check_for_rule(del_lines) and len(add_lines) == 0:
                del_results.append((commit, del_lines))
        except KeyError:
            #print("no patch error for: ")
            #print(commit)
            pass
    return add_results, del_results


def get_snakefile_undo_commits(self):
    query = db.full_commits.aggregate([
        {"$match": {"commit_content.files.filename": {"$regex": "Snakefile"}}},
        {"$unwind": "$commit_content.files"},
        {"$match": {"commit_content.files.filename": {"$regex": "Snakefile"}}},
        {"$project": {"commit_content.files.filename": 1, "_id": 1, "repo": 1,
                      "commit_content.files.additions": 1, "commit_content.files.deletions": 1,
                      "commit_content.files.changes": 1, "commit_content.files.patch": 1}}
    ])
    undo_commits = []
    repo_groups = defaultdict(list)
    for commit in query:
        try:
            patch = commit["commit_content"]["files"]["patch"]
            patch = patch.split("\n")
            del_lines = []
            add_lines = []
            for line in patch:
                if line[0] == "-":
                    del_lines.append(line[1:])
                elif line[0] == "+":
                    add_lines.append(line[1:])
            if add_lines and del_lines:
                repo_groups[commit["repo"]] += [(commit, del_lines, add_lines)]
        except KeyError:
            print("no patch error for: ")
            print(commit["_id"])
    # ineffective algorithm, but good enough here
    for repo, commits in repo_groups.items():
        for commit1 in commits:
            for commit2 in commits:
                if commit1 != commit2 and commit1[1] == commit2[2] and commit1[2] == commit2[1]:
                    if commit1[0]["_id"] < commit2[0]["_id"]:
                        if (commit1, commit2) not in undo_commits:
                            undo_commits.append((commit1, commit2))
                    else:
                        if (commit2, commit1) not in undo_commits:
                            undo_commits.append((commit2, commit1))
    return undo_commits

