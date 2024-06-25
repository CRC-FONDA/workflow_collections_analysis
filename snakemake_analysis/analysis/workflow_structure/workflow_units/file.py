class File:
    def __init__(self, source_repo, source_file, source_lines, name, producers=[], consumers=[]):
        self.source_repo = source_repo
        self.source_file = source_file
        self.source_lines = source_lines
        self.name = name
        self.producers = producers
        self.consumers = consumers


