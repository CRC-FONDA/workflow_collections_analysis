from db_operations.db_connector import DBConnector
from db_operations.data_v3_small.query_lightweight_db import get_workflow_files, test_for_workflowfile, collect_same_commit_hunks
from hunk_filters import filter_one_rule

connection_string = "mongodb://python:fonda@85.214.95.143/git_scraping"
db_name = "git_scraping"
deep_db = DBConnector(connection_string, db_name, "data_v3_small")
output_prefix = "../query_outputs/"

repo_list = [
    "AAFC-BICoE/snakemake-mothur",
    "AAFC-BICoE/snakemake-partial-genome-pipeline",
    "HelenaLC/muscat-comparison",
    "HenningTimm/bpht_evaluation_workflow",
    "JetBrains-Research/chipseq-smk-pipeline",
    "KoesGroup/Snakemake_ChIPseq_PE",
    "jrderuiter/snakemake-rnaseq",
    "kaiseriskera/FABLE",
    "khalillab/coop-TF-custom-analyses",
    "khalillab/coop-TF-rnaseq",
    "koesterlab/nanopore-qc",
    "leylabmpi/Struo",
    "manaakiwhenua/virtual-landscape-ecosys-services",
    "marykthompson/ribopop_rnaseq",
    "metamaden/recountmethylation_instance",
    "myonaung/sm-SNIPER",
    "nih-cfde/update-content-registry",
]

def get_rule_change_hunks(repo_list):
    hunks = []
    for repo in repo_list:
        try:
            repo_data = deep_db.coll.find({"repo": repo}).next()
        except:
            continue
        workflow_files = get_workflow_files(repo_data)
        for filename, file in repo_data["files"].items():
            if test_for_workflowfile(workflow_files, filename):
                # The file contains data of a workflow file
                for hunk in file["hunks"]:
                    result = filter_one_rule(hunk["hunk_lines"])
                    if result and result[0] == "del" and len(hunk["hunk_lines"]) < 30:
                        hunks.append((result[0], hunk, repo_data))
    return hunks


def get_rule_change_context(hunks):
    results = []
    for change, hunk, repo in hunks:
        same_commit_hunks = collect_same_commit_hunks(repo, hunk)
        if len(same_commit_hunks) < 8:
            results.append((change, repo["repo"], hunk, same_commit_hunks))
    return results

def write_rule_change_context(path, results):
    with open(path, "a") as f:
        for change, repo_name, hunk, same_commit_hunks in results:
            f.write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
            f.write("IN REPO: "+repo_name+", WITH "+change+" FOR HUNK:\n")
            for line in hunk["hunk_lines"]:
                f.write(line+"\n")
            f.write("SAME COMMIT HUNKS:\n")
            for sc_hunk in same_commit_hunks:
                f.write("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n")
                for line in sc_hunk["hunk_lines"]:
                    f.write(line+"\n")


#repo_list_2 = []
#with open(output_prefix + "workflow/tmp_repos.txt", "r") as f:
#    lines = f.readlines()
#    for line in lines:
#        repo_list_2.append(line)

data = get_rule_change_hunks(repo_list)
results = get_rule_change_context(data)
path = output_prefix + "workflow/investigate_rule_change.txt"
write_rule_change_context(path, results)

#print("start")
#with open(output_prefix + "workflow/one_rule_hunks.txt", "r") as f:
#    lines = f.readlines()
#    for line in lines:
#        if line[:6] == "REPO: ":
#            with open(output_prefix + "workflow/tmp_repos.txt", "a") as f2:
#                f2.write(line[6:]+"\n")

print("done!")
