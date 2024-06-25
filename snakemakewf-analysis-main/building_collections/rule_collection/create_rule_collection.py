from ...utility.parsers.snakefile_parser import iterate_snakefile_lines_with_context, get_rules
from ...db_operations.db_connector import DBConnector
db = DBConnector()


def iterate_all_rules():
    # search metadata
    n_repos = 0
    n_files = 0
    n_missing_files = 0
    n_rules = 0
    rule_data = {}

    # iterate through all rules
    full_data = db.final_state.find()
    for repo in full_data:
        n_repos += 1
        for filename, file in repo["files"].items():
            if filename not in repo["workflow_files"]:
                n_missing_files += 1
                continue
            try:
                content = file["content"].split("\\n")
            except Exception as e:
                # print("no content for " + repo["repo"] + "/" + filename + ": " + str(e))
                n_missing_files += 1
                continue
            # print("looking at " + filename)
            n_files += 1

            # get rules from this file
            rules = get_rules(content)
            for rule_name, rules_lines in rules.items():
                n_rules += 1
                print("Repos:", n_repos, "Files:", n_files, "Rules:", n_rules)
                yield {
                    "repo": repo["repo"],
                    "file": filename,
                    "rule_name": rule_name,
                    "line_numbers": rules_lines["line_numbers"],
                    "lines": rules_lines["lines"],
                    "run_lines": rules_lines["run"],
                    "shell_lines": rules_lines["shell"],
                }
    # lastly yield the meta results
    yield {
        "meta_results": "Done",
        "n_repos": n_repos,
        "n_files": n_files,
        "n_missing_files": n_missing_files,
        "n_rules": n_rules
    }


def clean():
    repos = db.rules.find()
    i = 0
    for repo in repos:
        i += 1
        print(i, repo)
    print("Wow, everything looks so fresh here!")


def insert_rules_into_collection(path="github_scraping/analysis/full_text/results/"):
    #clean()
    #return

    for rule_data in iterate_all_rules():
        if "meta_results" in rule_data:
            # we are done; save meta results
            with open(path + "/logs/rules_collection.txt", "a") as f:
                f.write("meta results of rule search:")
                for m, n in rule_data.items():
                    f.write("    " + m + ": " + str(n) + "\n")
                f.write("\n")
        else:
            # insert new rule into db collection
            db.rules.insert_one(rule_data)
