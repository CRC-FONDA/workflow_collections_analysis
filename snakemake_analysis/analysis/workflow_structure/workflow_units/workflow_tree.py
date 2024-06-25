class Node:
    def __init__(self, workflow, depth, rule_name, rule, inputs, provides=None):
        self.workflow = workflow
        self.depth = depth
        self.name = rule_name
        self.rule = rule
        self.inputs = inputs
        self.provides = provides
        self.children = []

        n_inputs = 0
        n_input_func = 0
        n_input_wildcards = 0
        n_resolved_inputs = 0
        for _input in self.inputs:
            n_inputs += 1
            if _input[1]:
                n_input_func += 1
            if "{" in _input[0] and "}" in _input[0]:
                n_input_wildcards += 1
            for rule_name, rule in self.workflow.rules.items():
                for output in rule.outputs:
                    if _input[0] in output:
                        n_resolved_inputs += 1
                        n = Node(
                            self.workflow,
                            self.depth + 1,
                            rule_name,
                            rule,
                            rule.inputs
                        )
                        self.children.append(n)

        self.metadata = {
            "n_input": n_inputs,
            "n_input_func": n_input_func,
            "n_input_wildcards": n_input_wildcards,
            "n_resolved_inputs": n_resolved_inputs,
        }


class Tree:
    def __init__(self, workflow):
        self.workflow = workflow
        self.root = None
        for rule_name, rule in workflow.rules.items():
            if "nakefile" in rule.source_file and rule.top_rule:
                self.root = Node(self.workflow, 0, rule_name, rule, rule.inputs)
                break

        n_nodes = 0
        list_n_children = []
        height = 0
        nodes_meta = dict()
        for node in self.traverse():
            n_nodes += 1
            list_n_children.append(len(node.children))
            height = max(height, node.depth)
            nodes_meta[node.name] = node.metadata

        self.metadata = {
            "n_rules": len(self.workflow.rules),
            "n_nodes": n_nodes,
            "list_n_children": list_n_children,
            "height": height,
            "nodes_meta": nodes_meta,
        }

    @staticmethod
    def _traverse(node):
        if node:
            yield node
            for c in node.children:
                yield from Tree._traverse(c)

    def traverse(self):
        yield from Tree._traverse(self.root)

    def print(self):
        def print_node(node, prefix):
            name = prefix+"/"+node.name
            print(node.depth, name)
            print("-  -  -  -  -")
            for c in node.children:
                print_node(c, name)

        print("###############################################################")
        print()
        print("TREE:")
        print("**************")
        print_node(self.root, "")
        print("**************")


