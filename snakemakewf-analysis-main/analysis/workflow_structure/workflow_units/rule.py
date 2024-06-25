class Rule:
    def __init__(self, source_repo, source_file, name, top_rule, inputs=[], outputs=[]):
        self.source_repo = source_repo
        self.source_file = source_file
        self.name = name
        self.top_rule = top_rule
        self.inputs = inputs
        self.outputs = outputs


def files_from_raw_rule(raw_rule):
    inputs = []
    for _, line, input_func in raw_rule["input_lines"]:
        line = line.strip()
        if line.startswith("#"):
            continue
        if line.startswith("input:"):
            line = line[6:].strip()
        if line:
            if line.startswith("\"") and line.endswith("\""):
                inputs.append((line.replace("\"", "").strip(), input_func))
            else:
                inputs.append((line, input_func))

    outputs = []
    for _, line in raw_rule["output_lines"]:
        line = line.strip()
        if line.startswith("output:"):
            line = line[7:].strip()
        if line:
            if line.startswith("\"") and line.endswith("\""):
                outputs.append(line.replace("\"", "").strip())
            else:
                outputs.append(line)
    return inputs, outputs
