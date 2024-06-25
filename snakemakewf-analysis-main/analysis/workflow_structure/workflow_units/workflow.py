from utility.final_state_utility import iterate_workflow_files
from utility.parsers.configfile_parser import iterate_final_state_config_definitions
from utility.parsers.snakefile_parser import get_rules_from_file
from analysis.workflow_structure.workflow_units.rule import Rule, files_from_raw_rule
from analysis.workflow_structure.workflow_units.workflow_tree import Tree


class Workflow:
    def __init__(self, source_repo, log_path):
        self.repo = source_repo["repo"]
        self.source_files = set()
        self.rules = dict()
        self.config_values = dict()

        self.build_from_repo_parse(source_repo, log_path)
        self.tree = Tree(self)

    def build_from_repo_parse(self, repo, log_path):
        try:
            for c_name, c_definitions, s_name in iterate_final_state_config_definitions(repo):
                self.config_values[s_name] = c_definitions
                self.source_files = self.source_files.union({c_name, s_name})
        except ValueError as e:
            with open(log_path, "a") as f:
                f.write("during parsing of config definitions: "+str(e))
        for file, file_name in iterate_workflow_files(repo):
            self.source_files.add(file_name)
            raw_rules = get_rules_from_file(file, file_name)
            try:
                for rule_name, data in raw_rules.items():
                    inputs, outputs = files_from_raw_rule(data)
                    self.rules[rule_name] = Rule(repo["repo"], file_name, rule_name, data["top_rule"], inputs, outputs)
            except AttributeError as e:
                with open(log_path, "a") as f:
                    f.write(self.repo+", during parsing of raw rules in workflow creation\n")
                    f.write(str(e))
                    f.write("\n\n")

