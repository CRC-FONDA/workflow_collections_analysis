import re
from ...db_operations.db_connector import DBConnector
db = DBConnector()


def get_keyword_lines_from_rule(rule, keyword):
    def get_indentation(indented_line):
        match = re.search(r"[^ ]", indented_line)
        if match:
            return match.start()
        else:
            return -1

    lines = [line.replace("\t", "    ") for line in rule["lines"]]
    keyword_lines = []
    for i in range(len(lines)):
        if keyword in lines[i]:
            keyword_indentation = get_indentation(lines[i])
            keyword_lines.append(lines[i])
            i += 1
            if i == len(lines):
                break
            new_indentation = get_indentation(lines[i])
            while new_indentation == -1 or new_indentation > keyword_indentation:
                keyword_lines.append(lines[i])
                i += 1
                if i == len(lines):
                    break
                new_indentation = get_indentation(lines[i])
            break
    return keyword_lines


def update_rules_with_input_output_wildcards():
    rules = db.rules.find()
    for rule in rules:
        input_lines = get_keyword_lines_from_rule(rule, "input:")
        input_lines = "".join(input_lines)
        match = re.search(r"\w*\{\w*\}\w*", input_lines)
        if match:
            uses_input_wildcard = True
        else:
            uses_input_wildcard = False

        output_lines = get_keyword_lines_from_rule(rule, "output:")
        output_lines = "".join(output_lines)
        match = re.search(r"\w*\{\w*\}\w*", output_lines)
        if match:
            uses_output_wildcard = True
        else:
            uses_output_wildcard = False

        f2 = {"_id": rule["_id"]}
        newvalues = {"$set": {
            "uses_input_wildcard": uses_input_wildcard,
            "uses_output_wildcard": uses_output_wildcard,
        }}
        db.rules.update_one(f2, newvalues)


def inspect_input_output_wildcards():
    f1 = {"uses_input_wildcard": True}
    f2 = {"uses_output_wildcard": True}
    f3 = {"uses_input_wildcard": True, "uses_output_wildcard": False}
    f4 = {"uses_input_wildcard": False, "uses_output_wildcard": True}
    n0 = db.rules.count_documents({})
    n1 = db.rules.count_documents(f1)
    n2 = db.rules.count_documents(f2)
    n3 = db.rules.count_documents(f3)
    n4 = db.rules.count_documents(f4)

    print(n0, n1, n2, n3, n4)



