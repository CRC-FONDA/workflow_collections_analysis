import re


def get_file_content(file):
    try:
        return file["content"].split("\\n")
    except KeyError as e:
        print("no content for current file")
        return None


def get_indentation(indented_line):
    indented_line = indented_line.replace("\t", "    ")
    num_initial_spaces = len(indented_line) - len(indented_line.lstrip())
    return num_initial_spaces


def new_context_key(line):
    p = line.find(":")
    if re.match("^\s*[A-Za-z0-9_]*:.*", line):
        return line[:p].strip(), p
    first_word = line.strip().split()[0]
    if first_word in ["rule", "checkpoint", "if", "else", "elif"]:
        return line[:p].strip(), p
    return None, None


def iterate_snakefile_lines_with_context(snakefile):
    index = 0
    context_key = []
    key_prefix = []
    indentations = [0]
    for line in snakefile:

        # get context key
        if line.strip() and not line.strip().startswith("#"):
            new_indentation = get_indentation(line)
            if new_indentation == indentations[-1]:
                new_key, p = new_context_key(line)
                if new_key:
                    if line[p + 1:].strip():
                        context_key = key_prefix + [new_key]
                    else:
                        key_prefix += [new_key]
                        context_key = key_prefix
                else:
                    context_key = key_prefix
            elif new_indentation > indentations[-1]:
                indentations.append(new_indentation)
                new_key, p = new_context_key(line)
                if new_key:
                    if line[p + 1:].strip():
                        context_key = key_prefix + [new_key]
                    else:
                        key_prefix += [new_key]
                        context_key = key_prefix
                else:
                    context_key = key_prefix
            elif new_indentation < indentations[-1]:
                try:
                    i = indentations.index(new_indentation)
                except ValueError as e:
                    i = 0
                    for j in indentations:
                        if j > new_indentation:
                            break
                        i += 1
                indentations = indentations[:i + 1]
                key_prefix = key_prefix[:i]
                context_key = context_key[:i]
                new_key, p = new_context_key(line)
                if new_key:
                    if line[p + 1:].strip():
                        context_key = key_prefix + [new_key]
                    else:
                        key_prefix += [new_key]
                        context_key = key_prefix
                else:
                    context_key = key_prefix

        yield index, line, context_key
        index += 1


def get_rules_from_file(file_name, file=None, file_content=None):
    if not file_content:
        file_content = get_file_content(file)
    if not file_content:
        print("no file content")
        return None

    rules = dict()

    # parsing variables
    current_rule = ""
    input_active = False
    input_lines = []
    output_active = False
    output_lines = []
    top_rule = True

    for index, line, context_key in iterate_snakefile_lines_with_context(file_content):
        rule_key = [key for key in context_key if "rule " in key]
        if rule_key:
            # within a rule
            new_current_rule = rule_key[0][5:]
            if new_current_rule != current_rule:
                if current_rule:
                    # print("RULE "+ current_rule +" COMPLETE")
                    rules[current_rule] = {
                        "file_name": file_name,
                        "input_lines": input_lines,
                        "output_lines": output_lines,
                        "top_rule": top_rule,
                    }
                    top_rule = False
                current_rule = new_current_rule
                input_active = False
                input_lines = []
                output_active = False
                output_lines = []

            if not input_active and "input" in context_key:
                input_lines = []
                input_active = True
            if input_active:
                if "input" in context_key:
                    # check for input function
                    func_candidate = None
                    input_func = None
                    if "input:" in line and "\"" not in line:
                        p = line.find(":")
                        func_candidate = line[p + 1:].strip()
                    elif "\"" not in line:
                        p = line.find("(")
                        func_candidate = line[:p].strip()
                    if func_candidate:
                        for func_line in file_content:
                            if "def " + func_candidate in func_line:
                                input_func = func_line.strip()
                                break
                    if line.strip():
                        input_lines.append((index, line, input_func))
                else:
                    input_active = False

            if not output_active and "output" in context_key:
                output_lines = []
                output_active = True
            if output_active:
                if "output" in context_key:
                    if line.strip():
                        output_lines.append((index, line))
                else:
                    output_active = False

        else:
            # not in a rule at all
            if current_rule:
                rules[current_rule] = {
                    "file_name": file_name,
                    "input_lines": input_lines,
                    "output_lines": output_lines,
                    "top_rule": top_rule,
                }
                top_rule = False
                current_rule = ""
                input_active = False
                input_lines = []
                output_active = False
                output_lines = []
    if current_rule:
        rules[current_rule] = {
            "file_name": file_name,
            "input_lines": input_lines,
            "output_lines": output_lines,
            "top_rule": top_rule,
        }

    return rules


def get_rules(snakefile):
    def clean_lines(rule_lines):
        return [ln.rstrip() for ln in rule_lines]
    # scan this file for rules
    rules = {}
    for i, line, context_key in iterate_snakefile_lines_with_context(snakefile):
        rule_key = [key for key in context_key if "rule " in key or "checkpoint " in key]
        # print(i, rule_key, context_key, line)
        if rule_key:
            # update rules
            if not rule_key[0] in rules:
                # new rule
                rules[rule_key[0]] = {
                    "line_numbers": [i],
                    "lines": [line],
                    "run": [],
                    "shell": [],
                }
            else:
                # extend existing rule
                rules[rule_key[0]]["line_numbers"].append(i)
                rules[rule_key[0]]["lines"].append(line)
                if "run" in context_key:
                    rules[rule_key[0]]["run"].append(line)
                if "shell" in context_key:
                    rules[rule_key[0]]["shell"].append(line)
    return rules


