from db_operations.db_connector import DBConnector
from utility.parsers.snakefile_parser import iterate_snakefile_lines_with_context
from utility.parsers.configfile_parser import get_config_definitions, iterate_final_state_config_contents
import re

db = DBConnector()


def get_configfile_hunks():
    full_data = db.brief_hunks.find()

    for repo in full_data:
        for filename, file in repo["files"].items():
            if "config" in filename:
                for hunk in file["hunks"]:
                    content = db.get_hunk_fulltext(hunk, filename)
                    yield hunk, content


def write_configfile_with_definitions(path, configfile, definitions):
    with open(path, "w") as f:
        for line in configfile.split("\\n"):
            f.write(line+"\n")
        f.write("\nDEFINITIONS:\n\n")
        for x in definitions:
            f.write(str(x)+"\n")
        f.write("#############################################################################\n\n")


def write_usage_overview():
    with open("report.txt", "w") as f:
        pass
    for results in iterate_snakefile_config_use():
        with open("report.txt", "a") as f:
            f.write("REPO: " + str(results["repo"]) + "\n")
            f.write("FILENAME: " + str(results["filename"]) + "\n")
            f.write("LINE: " + str(results["line"]) + "\n")
            f.write("CONFIG_KEY: " + str(results["config_key"]) + "\n")
            f.write("VALUE CANDIDATES: " + str(results["values"]) + "\n")
            f.write("CONTEXT_KEY: " + str(results["context_key"]) + "\n")
            f.write("SURROUNDINGS:\n")
            for l in results["surroundings"]:
                f.write("\t"+l+"\n")
            f.write("----------------------------------------------------------\n")


def iterate_snakefile_config_use():
    full_data = db.final_state.find()
    for repo in full_data:
        for configfile_name, configfile_content, snakefile_name, snakefile_content in iterate_final_state_config_contents(repo):
            config_definitions = get_config_definitions(configfile_content)
            write_configfile_with_definitions("c.txt", configfile_content, config_definitions)

            for i, line, context_key in iterate_snakefile_lines_with_context(snakefile_content):
                surroundings = snakefile_content[max(0, i-3):min(i+4, len(snakefile_content)-1)]

                for p in re.finditer("config\\[", line):
                    config_key = []
                    m = p.span()[1]
                    n = line.find("][", m)
                    while n != -1:
                        key = line[m+1:n].replace("\"", "").replace('\'', '').replace('\\', '')
                        config_key.append(key)
                        m = n+1
                        n = line.find("][", m)
                    n = line.find("]", m)
                    key = line[m+1:n].replace("\"", "").replace('\'', '').replace('\\', '')
                    config_key.append(key)

                    values = []
                    for def_key, value in config_definitions:
                        if config_key == def_key:
                            values.append(value)
                    out = {
                        "repo": repo["repo"],
                        "filename": snakefile_name,
                        "line": line,
                        "line_index": i,
                        "config_key": config_key,
                        "values": values,
                        "context_key": context_key,
                        "surroundings": surroundings,
                        "snakefile_content": snakefile_content
                    }
                    yield out

