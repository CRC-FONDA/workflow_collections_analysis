import re
from utility.parsers.iterate_rules import iterate_all_rules
from ...db_operations.db_connector import DBConnector


def create_collection():
    db = DBConnector()
    i = 0
    for rule in iterate_all_rules():
        i += 1
        print("rule number:", i)
        db.full_text_rules.insert_one(rule)


def update_with_operators():
    def get_operators(shell_lines):
        new_operators = []
        for _, line in shell_lines:
            # clean line
            for pattern in ["\\\'", "\\\\", '\"', '\'', "(", ")"]:
                line = line.replace(pattern, "")
            line = line.strip()
            if not line or line == "shell:":
                continue
            if line.startswith("#"):
                continue

            # split operator candidates
            delimiters = "|", ">", ">>", "<", "<<"
            regex_pattern = '|'.join(map(re.escape, delimiters))
            bash_units = [_.strip() for _ in re.split(regex_pattern, line)]
            for unit in bash_units:
                operator_candidate = unit.split(" ")[0]
                new_operators.append(operator_candidate)
        return new_operators

    db = DBConnector()
    f1 = {"shell_lines": {"$exists": True, "$not": {"$size": 0}}}
    n1 = db.full_text_rules.count_documents(f1)

    print("number of rules with non-emtpy shell lines:", n1)

    i = 0
    for rule in db.full_text_rules.find(f1):
        i += 1
        print(str(i) + "/" + str(n1))
        operators = get_operators(rule["shell_lines"])
        db.full_text_rules.find_one_and_update(
            {"_id": rule["_id"]},
            {"$set": {"operators": operators}}
        )


def update_with_config_operator_matches():
    def get_config_file(config_rule):
        repo = db.final_state.find({"repo": config_rule["repo"]}).next()
        new_config_files = [f for f in repo["files"].keys() if "config" in f[f.rfind("/"):]]
        return [(f, repo["files"][f]["content"]) for f in new_config_files if "content" in repo["files"][f]]

    db = DBConnector()
    f1 = {"operators": {"$exists": True, "$not": {"$size": 0}}}

    n = str(db.full_text_rules.count_documents(f1))
    i = 0
    for rule in db.full_text_rules.find(f1):
        i += 1
        print(str(i) + "/" + n)

        # construct operator pattern
        operators = rule["operators"]
        if not operators:
            continue
        valid_operators = []
        for operator in operators:
            if len(operator) == 1:
                continue
            try:
                re.compile(operator)
                valid_operators.append(operator)
            except re.error:
                print(operator + " is not a valid regex pattern")
                continue
        operator_pattern = "(" + "|".join(valid_operators) + ")"

        # match operators in config files if possible
        rule_matches = {}
        config_files = get_config_file(rule)
        if config_files:
            # print("operator_pattern:", operator_pattern)
            for file_name, content in config_files:
                processed_matches = []
                matches = re.finditer(operator_pattern, content)
                if matches:
                    match = next(matches, None)
                    while match:
                        # print(type(match.group()), match.group())
                        #if len(match.group()) == 1:
                        #    print("operator_pattern:", operator_pattern)
                        #    print(match.group())
                        #    exit()
                        if match.group():
                            processed_matches.append((match.group(), match.span()))
                        match = next(matches, None)
                if processed_matches:
                    rule_matches[file_name] = processed_matches
        if len(rule_matches) > 0:
            print("Found matches:", rule_matches)
            db.full_text_rules.find_one_and_update(
                {"_id": rule["_id"]},
                {"$set": {"config_operator_matches": rule_matches}}
            )
