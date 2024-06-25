from ...analysis.workflow_structure.graph_analysis import read_graphs_from_directory
from ...utility.graph_utility import get_node_label, extract_logical_rule
from ...db_operations.db_connector import DBConnector
db = DBConnector()


def get_operators_for_graph(repo_string, graph):
    #test = [x for x in db.rules.find({"repo": repo_string})]
    #print("number of rules for repo " + repo_string + ": " + str(len(test)))
    #return

    operator_map = {}

    for node in graph.nodes:
        label = get_node_label(repo_string, node)
        rule_name = extract_logical_rule(label)
        f = {
            "repo": repo_string.replace("_", "/"),
            "rule_name": "rule " + rule_name,
            "operators": {"$exists": True, "$not": {"$size": 0}},
        }
        rule = [x for x in db.rules.find(f)]
        if len(rule) > 1:
            #TODO: raise ValueError("More than one rule matched: repo=" + repo_string.replace("_", "/") + ", rule=" + "rule " + rule_name)
            pass
        if rule:
            operator_map[node] = rule[0]["operators"]
            print(node, rule_name, operator_map[node])

    return operator_map


def get_operator_paths(reversed_graph, operator_map):
    def build_paths(node):
        successors = reversed_graph.successors(node)
        operators = operator_map[node] if node in operator_map else None

        successor_paths = []
        for s in successors:
            successor_paths += build_paths(s)

        if successor_paths:
            return [path + [(node, operators)] for path in successor_paths]
        else:
            return [[(node, operators)]]

    print("GET OPERATOR PATHS")
    return build_paths(str(0))


def get_all_operator_paths(paths):
    operator_paths = []
    for path in paths:
        # print("PATH:", path)
        current_segments = []
        for node, operators in path:
            if operators:
                # print("APPEND:", operators)
                if current_segments:
                    new_segments = []
                    for operator in operators:
                        for segment in current_segments:
                            new_segment = segment + [operator]
                            operator_paths.append(new_segment)
                            new_segments.append(new_segment)
                    current_segments = new_segments
                else:
                    current_segments = [[operator] for operator in operators]
            else:
                current_segments = []
    return [tuple(path) for path in operator_paths]


def get_longest_operator_paths(paths):
    operator_paths = []
    for path in paths:
        current_segments = []
        for node, operators in path:
            if operators:
                if current_segments:
                    new_segments = []
                    for operator in operators:
                        for segment in current_segments:
                            new_segments.append(segment + [operator])
                    current_segments = new_segments
                else:
                    current_segments = [[operator] for operator in operators]
            else:
                if current_segments:
                    operator_paths += current_segments
                    current_segments = []
    return [tuple(path) for path in operator_paths]


def get_all_operator_pairs(paths):
    operator_pairs = []
    for path in paths:
        preceding_operators = []
        for node, operators in path:
            if operators:
                if preceding_operators:
                    for operator in operators:
                        for preceding_operator in preceding_operators:
                            operator_pairs.append((preceding_operator, operator))
                preceding_operators = operators
            else:
                preceding_operators = []
    return operator_pairs


def iterate_graphs_with_operators(out_path="github_scraping/analysis/operators/results/"):
    n_repos_with_operator_paths = 0
    number_of_unique_paths = 0

    operator_path_counts_by_repo = {}
    operator_pair_counts_by_repo = {}
    operator_path_counts_total = {}
    operator_pair_counts_total = {}
    i = 0
    for repo_string, graph in read_graphs_from_directory():
        i += 1
        print(str(i) + "/362: " + repo_string)
        operator_map = get_operators_for_graph(repo_string, graph)
        print("number of nodes with operators: " + str(len(operator_map)))
        if len(operator_map) > 0:
            n_repos_with_operator_paths += 1
            reversed_graph = graph.reverse(copy=True)
            # print("EDGES")
            # print(reversed_graph.edges)
            paths = get_operator_paths(reversed_graph, operator_map)
            longest_operator_paths = get_longest_operator_paths(paths)
            operator_pairs = get_all_operator_pairs(paths)

            for path in longest_operator_paths:
                if path in operator_path_counts_total:
                    operator_path_counts_total[path] += 1
                else:
                    operator_path_counts_total[path] = 1
            for pair in operator_pairs:
                if pair in operator_pair_counts_total:
                    operator_pair_counts_total[pair] += 1
                else:
                    operator_pair_counts_total[pair] = 1

            longest_operator_paths = set(longest_operator_paths)
            operator_pairs = set(operator_pairs)

            number_of_unique_paths += len(longest_operator_paths)

            for path in longest_operator_paths:
                if path in operator_path_counts_by_repo:
                    operator_path_counts_by_repo[path] += 1
                else:
                    operator_path_counts_by_repo[path] = 1
            for pair in operator_pairs:
                if pair in operator_pair_counts_by_repo:
                    operator_pair_counts_by_repo[pair] += 1
                else:
                    operator_pair_counts_by_repo[pair] = 1

    with open(out_path + "operator_path_counts_total.txt", "w") as f:
        operator_path_counts_list = [(path_key, count) for path_key, count in operator_path_counts_total.items()]
        operator_path_counts_list.sort(key=lambda x: x[1], reverse=True)
        for path_key, count in operator_path_counts_list:
            f.write("number of occurences: " + str(count) + ", path segment: " + str(path_key) + "\n")

    with open(out_path + "operator_path_counts_by_repo.txt", "w") as f:
        operator_path_counts_list = [(path_key, count) for path_key, count in operator_path_counts_by_repo.items()]
        operator_path_counts_list.sort(key=lambda x: x[1], reverse=True)
        for path_key, count in operator_path_counts_list:
            f.write("number of occurences: " + str(count) + ", path segment: " + str(path_key) + "\n")

    with open(out_path + "operator_pair_counts_total.txt", "w") as f:
        operator_pair_counts_list = [(pair, count) for pair, count in operator_pair_counts_total.items()]
        operator_pair_counts_list.sort(key=lambda x: x[1], reverse=True)
        for pair, count in operator_pair_counts_list:
            f.write("number of occurences: " + str(count) + ", path segment: " + str(pair) + "\n")

    with open(out_path + "operator_pair_counts_by_repo.txt", "w") as f:
        operator_pair_counts_list = [(pair, count) for pair, count in operator_pair_counts_by_repo.items()]
        operator_pair_counts_list.sort(key=lambda x: x[1], reverse=True)
        for pair, count in operator_pair_counts_list:
            f.write("number of occurences: " + str(count) + ", path segment: " + str(pair) + "\n")

    print("number of repos with operator paths:", n_repos_with_operator_paths)
    print("number of unique paths:", number_of_unique_paths)







