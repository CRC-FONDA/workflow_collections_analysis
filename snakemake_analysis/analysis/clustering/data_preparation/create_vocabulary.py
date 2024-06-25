import math
from ..vectorizer import clean_lines
from ....db_operations.db_connector import DBConnector
db = DBConnector()


def create_shell_vocabulary(path="github_scraping/analysis/clustering/vocabularies/", clean_data=True):
    f1 = {"shell_lines": {"$exists": True, "$not": {"$size": 0}}}
    rules = db.rules.find(f1)

    vocabulary = {}
    document_count = {}

    i = 0
    for rule in rules:
        words_present = set()
        i += 1
        if i % 100 == 0:
            print("counted %d shell rules" % i)
        if clean_data:
            content = clean_lines(rule["shell_lines"])
        else:
            content = " ".join(line.strip() for line in rule["shell_lines"]).split()
        for word in content:
            n = len(word)
            if n > 1 and word[0] == "\"" and word[1] != "\"":
                word = word[1:]
                n -= 1
            if n > 1 and word[n-1] == "\"" and word[n-2] != "\"":
                word = word[1:]
            if word in vocabulary:
                vocabulary[word] += 1
            else:
                vocabulary[word] = 1
            words_present.add(word)

        for word in words_present:
            if word in document_count:
                document_count[word] += 1
            else:
                document_count[word] = 1

    print("unique words:", len(vocabulary))
    if clean_data:
        output_path = path + "shell_words_cleaned.csv"
    else:
        output_path = path + "shell_words.csv"
    with open(output_path, "w") as f:
        f.write("word, position, count, idf (N=" + str(i) + ")\n")
        j = 0
        for w, c in sorted(vocabulary.items(), key=lambda item: item[1], reverse=True):
            idf = math.log(i / document_count[w])
            f.write(w + ", " + str(j) + ", " + str(c) + ", " + str(idf) + "\n")
            j += 1

