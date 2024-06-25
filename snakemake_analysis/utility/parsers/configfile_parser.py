import re


def get_config_definitions(config_content):

    def get_indentation(indented_line):
        indented_line = indented_line.replace("\t", "    ")
        num_initial_spaces = len(indented_line) - len(indented_line.lstrip())
        return num_initial_spaces

    config_key_value = []
    key_prefix = []
    indentations = [0]
    for line in config_content.split("\\n"):
        if not line.strip() or line.strip().startswith("#"):
            continue
        new_indentation = get_indentation(line)
        if new_indentation == indentations[-1]:
            if re.match("^\s*[A-Za-z0-9_]*:.*", line):
                p = line.find(":")
                new_key = line[:p].strip()
                if key_prefix:
                    key = key_prefix + [new_key]
                else:
                    key = [new_key]
                if line[p + 1:].strip():
                    value = line[p + 1:].strip()
                    config_key_value.append((key, value))
                else:
                    key_prefix.append(new_key)
            else:
                value = line.strip()
                config_key_value.append((key_prefix, value))
        elif new_indentation > indentations[-1]:
            indentations.append(new_indentation)
            if re.match("^\s*[A-Za-z0-9_]*:.*", line):
                p = line.find(":")
                new_key = line[:p].strip()
                if line[p + 1:].strip():
                    key = key_prefix + [new_key]
                    value = line[p + 1:].strip()
                    config_key_value.append((key, value))
                else:
                    key_prefix.append(new_key)
            else:
                value = line.strip()
                config_key_value.append((key_prefix, value))
        elif new_indentation < indentations[-1]:
            i = indentations.index(new_indentation)
            indentations = indentations[:i + 1]
            key_prefix = key_prefix[:i]
            if re.match("^\s*[A-Za-z0-9_]*:.*", line):
                p = line.find(":")
                new_key = line[:p].strip()
                if key_prefix:
                    key = key_prefix + [new_key]
                else:
                    key = [new_key]
                if line[p + 1:].strip():
                    value = line[p + 1:].strip()
                    config_key_value.append((key, value))
                else:
                    key_prefix.append(new_key)
    return config_key_value


def iterate_final_state_config_contents(final_state_repo):
    snakefile_names = [n for n in final_state_repo["workflow_files"] if n.endswith("nakefile")]
    for snakefile_name in snakefile_names:
        configfile_name = ""
        try:
            snakefile_content = final_state_repo["files"][snakefile_name]["content"].split("\\n")
        except KeyError as e:
            print("No file in db for snakefile: " + snakefile_name + ", in repo: " + final_state_repo["repo"])
            continue
        for line in snakefile_content:
            if line.strip().startswith("configfile"):
                configfile_name = line[line.find("\"") + 1: line.rfind("\"")]
                break
        try:
            configfile_content = final_state_repo["files"][configfile_name]["content"][2:-1]
        except KeyError as e:
            if configfile_name:
                print("No file in db for configfile: " + configfile_name + ", in repo: " + final_state_repo["repo"])
            continue
        yield configfile_name, configfile_content, snakefile_name, snakefile_content


def iterate_final_state_config_definitions(final_state_repo):
    for c_name, c_content, s_name, s_content in iterate_final_state_config_contents(final_state_repo):
        yield c_name, get_config_definitions(c_content), s_name
