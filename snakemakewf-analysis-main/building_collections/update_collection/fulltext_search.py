from utility import update_collection
from db_operations.db_connector import DBConnector
db = DBConnector()


def workflow_fulltext_search():
    subworkflow_files = []
    checkpoint_rules = []
    input_functions = []

    n_documents = str(db.final_state.count_documents({}))
    i = 0

    repos = db.final_state.find()
    for repo in repos:
        i += 1
        print(str(i)+"/"+n_documents+": "+repo["repo"])
        for filename in repo["workflow_files"]:
            try:
                content = repo["files"][filename]["content"].split("\\n")
            except Exception as e:
                print("no content for "+repo["repo"]+"/"+filename+": "+str(e)+"\n")
                continue
            # booleans for parsing:
            input_context = False
            current_rule = None
            func_candidate = None
            for line in content:
                # rule context update
                if line.strip().startswith("rule "):
                    rule_start = line.find("rule ") + 5
                    rule_end = line.find(":", rule_start)
                    current_rule = line[rule_start:rule_end]
                # checkpoints
                if line.strip().startswith("checkpoint "):
                    rule_start = line.find("checkpoint ") + 11
                    rule_end = line.find(":", rule_start)
                    checkpoint_name = line[rule_start:rule_end]
                    checkpoint_rules.append(checkpoint_name)
                    current_rule = checkpoint_name
                # subworkflow usage
                if line.strip().startswith("subworkflow"):
                    subworkflow_files.append(filename)
                # input functions
                if "input:" in line and line.strip()[-1] == ":":
                    input_context = True
                elif "input:" in line and "\"" not in line:
                    p = line.find(":")
                    func_candidate = line[p+1:].strip()
                elif input_context and "\"" not in line:
                    p = line.find("(")
                    func_candidate = line[:p].strip()
                if input_context:
                    input_context = False
                if func_candidate is not None:
                    for func_line in content:
                        if "def " + func_candidate in func_line:
                            input_functions.append((current_rule, func_candidate))
                            func_candidate = None
                            break

        # update database with results for this file
        if subworkflow_files or checkpoint_rules or input_functions:
            db.workflow_structures.find_one_and_update(
                {"repo": repo["repo"]},
                {"$set": {"features": {}}}
            )
        if subworkflow_files:
            field = "features.subworkflow_files"
            value = subworkflow_files
            update_collection(repo["repo"], field, value)
            subworkflow_files = []
        if checkpoint_rules:
            field = "features.checkpoints"
            value = checkpoint_rules
            update_collection(repo["repo"], field, value)
            checkpoint_rules = []
        if input_functions:
            field = "features.input_functions"
            value = input_functions
            update_collection(repo["repo"], field, value)
            input_functions = []
