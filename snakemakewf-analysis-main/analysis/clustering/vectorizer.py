import numpy as np


def clean_lines(lines):
    new_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            continue
        if line.startswith("\'"):
            line = line[2:]
        if line.endswith("\'"):
            line = line[:len(line) - 2]
        if line.endswith("\\"):
            line = line[:len(line) - 1]
        new_lines.append(line)
    return " ".join(new_lines).split()


class ShellCodeBaseVectorizer:
    def __init__(self, vocab_path="github_scraping/analysis/clustering/vocabularies/", cleaned_data=True):
        if cleaned_data:
            vocab_path += "shell_words_cleaned.csv"
        else:
            vocab_path += "shell_words.csv"
        self.vocab_size = 0
        self.word_table = dict()
        with open(vocab_path, "r") as f:
            next(f)
            for line in f.readlines():
                self.vocab_size += 1
                word, pos, count, idf = line.strip().split(", ")
                self.word_table[word] = (int(pos), int(count), float(idf))
        self.blacklist = [
            "\\\\",
            "shell:",
            "\"\"\"",
            "#",
            "\"",
            "\'\'\'",
            "\'",
        ]


class ShellCodeBagOfWordsVectorizer(ShellCodeBaseVectorizer):
    def vectorize(self, lines, clean_data=True):
        v = np.zeros(self.vocab_size)
        if clean_data:
            content = clean_lines(lines)
        else:
            content = " ".join(line.strip() for line in lines).split()
        for word in content:
            n = len(word)
            if n > 1 and word[0] == "\"" and word[1] != "\"":
                word = word[1:]
                n -= 1
            if n > 1 and word[n - 1] == "\"" and word[n - 2] != "\"":
                word = word[1:]
            v[self.word_table[word][0]] += 1
        return v


class ShellCodeTFIDFVectorizer(ShellCodeBaseVectorizer):
    def vectorize(self, lines, blacklist=False, clean_data=True):
        tf = np.zeros(self.vocab_size)
        tf_idf = np.zeros(self.vocab_size)
        n_words = 0
        if clean_data:
            content = clean_lines(lines)
        else:
            content = " ".join(line.strip() for line in lines).split()
        for word in content:
            n = len(word)
            if n > 1 and word[0] == "\"" and word[1] != "\"":
                word = word[1:]
                n -= 1
            if n > 1 and word[n - 1] == "\"" and word[n - 2] != "\"":
                word = word[1:]
            if blacklist:
                if word in self.blacklist:
                    continue
            tf[self.word_table[word][0]] += 1
            n_words += 1
        if n_words > 0:
            tf = tf / n_words
        for pos, count, idf in self.word_table.values():
            tf_idf[pos] = tf[pos] * idf
        return tf_idf




