
def check_comment(line):
    return True if line[1:].split()[0] != "#" else False


def right_hand_string(line):
    pos = line.find('=')
    rhs = line[pos + 1:].strip()
    rhs = rhs.replace(',', '')
    return True if rhs[0] == '"' and rhs[-1] == '"' else False


def contains_digit(line):
    return any(char.isdigit() for char in line)


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


def filter_one_parameter(hunk):
    for line in hunk:
        if line[0] == "-":
            del_line = line
        elif line[0] == "+":
            add_line = line
    #if not del_line or not add_line:
    #    print(hunk)
    #    raise ValueError("can't find add and del lines")
    if del_line.count('=') != 1 or add_line.count('=') != 1:
        return False
    if right_hand_string(add_line) and right_hand_string(del_line):
        return False
    if not contains_digit(add_line) or not contains_digit(del_line):
        return False
    if check_comment(add_line) and check_comment(del_line):
        return True
    return False


def filter_one_rule(hunk):
    del_lines = []
    add_lines = []
    result = []
    for line in hunk:
        if line[0] == "-":
            del_lines.append(line)
        elif line[0] == "+":
            add_lines.append(line)
    del_rule = check_for_rule(del_lines)
    add_rule = check_for_rule(add_lines)
    if del_rule and not add_rule:
        result.append("del")
    if not del_rule and add_rule:
        result.append("add")
    if del_rule and add_rule:
        result.append("change")
    return result


def filter_input(hunk):
    reading_input = False
    done_reading = False
    found_input = False
    for line in hunk:
        if line[0] == "-" and "input:" not in line:
            return False
        if not reading_input and line[0] == "-" and "input:" in line:
            reading_input = True
            found_input = True
        if reading_input and (line[0] != "-"):
            done_reading = True
        if done_reading and line[0] == "-":
            return False
    return found_input
