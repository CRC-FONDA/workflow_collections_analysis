import pymongo

from building_collections.update_collection import (
    get_dag_histories_from_pair,
)
from db_operations.db_connector import DBConnector
db = DBConnector()


def investigate_n_nodes_diffs():
    analysis_results_path = "github_scraping/db_operations/workflow_structure/results/diff_commits_1.txt"
    query = db.commit_difference_pairs.find({
        "n_nodes": {"$exists": True}
    }).sort("n_nodes_diff", pymongo.DESCENDING)

    i = 0
    for pair in query:
        i += 1

        later, earlier = get_dag_histories_from_pair(pair)
        # for now skip non-consecutive pairs
        if abs(later["commit_number"] - earlier["commit_number"]) != 1:
            with open(analysis_results_path, "a") as f:
                f.write(str(i)+" skipping non-consecutive pair: "+str(pair["_id"])+"\n")
            continue

        # try to retrieve commit lines that caused change
        query = db.full_commits.find({"$and":[
            {"repo": later["repo"]},
            {"sha": later["sha"]},
        ]})
        commit = next(query, None)
        if not commit:
            with open(analysis_results_path, "a") as f:
                f.write(str(i)+" failed to retrieve full commit: "+str(pair["_id"])+"\n")
            continue
        else:
            stats = commit["commit_content"]["stats"]
            if stats["total"] > 50:
                with open(analysis_results_path, "a") as f:
                    f.write(str(i) + " un-interpretable; skipping commit with over 50 line changes: " + str(pair["_id"]) + "\n")
            else:
                with open(analysis_results_path, "a") as f:
                    f.write(str(i) + " looking at commit: " + str(pair["_id"]) + "\n")
                    f.write("repo=" + str(pair["repo"]) + ", "
                            + "n_nodes=" + str(pair["n_nodes"]) + ", "
                            + "n_nodes_diff=" + str(pair["n_nodes_diff"]) + ", "
                            + "n_l_rules_diff=" + str(pair["n_l_rules_diff"]) + ", "
                            + "n_parallel_pairs_diff=" + str(pair["n_parallel_pairs_diff"]) + "\n")
                    f.write(str(stats)+"\n")
                    f.write("---------------------------------------------------------------------\n")
                    files = commit["commit_content"]["files"]
                    for file in files:
                        try:
                            hunks = file["hunks"]
                            for hunk in hunks:
                                f.write("added=" + str(hunk["added"]) + ", deleted=" + str(hunk["deleted"]) + "\n")
                                for line in hunk["hunk_lines"]:
                                    f.write(line + "\n")
                        except:
                            pass
                    f.write("---------------------------------------------------------------------\n")
