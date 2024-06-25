def db_update_hunks(self):
    # we need more fine-grained information than changes on a patch level
    # here we add changes on the level of hunks to the mongodb database
    log_path = "../logs/db_hunks_update_file_level.log"

    def get_hunks_from_patch(patch):
        hunks = []
        changes = patch.split("\n")
        started = False
        added = 0
        deleted = 0
        hunk_lines = []
        for line in changes:
            if line[:2] == "@@" and started:
                hunks.append({"added": added, "deleted": deleted, "hunk_lines": hunk_lines})
                added = 0
                deleted = 0
                hunk_lines = []
            elif line[:2] == "@@":
                started = True
                hunk_lines = []
            elif line[0] == "+":
                added += 1
            elif line[0] == "-":
                deleted += 1
            hunk_lines.append(line)
        hunks.append({"added": added, "deleted": deleted, "hunk_lines": hunk_lines})
        return hunks

    # get all documents and update them one by one
    documents = self.coll.find({})
    for doc in documents:
        _id = ObjectId(doc["_id"])
        files = doc["commit_content"]["files"]
        index = 0
        for file in files:
            try:
                hunks = get_hunks_from_patch(file["patch"])
                sub_doc_url = "commit_content.files." + str(index) + ".hunks"
                index += 1
                self.coll.update_one(
                    {"_id": _id},
                    {"$set": {sub_doc_url: hunks}}
                )
                with open(log_path, "a") as f:
                    f.write("Successfully updated document/file with ")
                    f.write("_id: " + str(doc["_id"]) + "\n")
                    f.write("file: " + file["filename"] + "\n")
            except Exception as e:
                with open(log_path, "a") as f:
                    f.write("Error while updating document/file with ")
                    f.write("_id: " + str(doc["_id"]) + "\n")
                    f.write("file: " + file["filename"] + "\n")
                    f.write(str(e) + "\n")


    def db_update_includes(self):
        # annotate files with the files they include
        log_path = "../logs/db_includes_modules_update.log"
        include_module_report = "logs/db_includes_modules_report.log"
        def get_includes_and_modules(content):
            from base64 import b64decode
            content = str(b64decode(content))
            content = content.split("\\n")
            includes = []
            modules = []
            empty_include = False
            found_module = False
            collect_module = False
            for line in content:
                line_list = line.split()
                if empty_include:
                    includes.append(line)
                    empty_include = False
                    with open(include_module_report, "a") as f:
                        f.write("Found empty include. Next line: "+line+"\n")
                    continue
                if found_module:
                    if line_list[0] == "snakefile:":
                        collect_module = True
                        found_module = False
                        continue
                    else:
                        found_module = False
                        with open(include_module_report, "a") as f:
                            f.write("Found non-standard module: "+line+"\n")
                if collect_module:
                    modules.append(line)
                    collect_module = False
                    with open(include_module_report, "a") as f:
                        f.write("Found module. Collected line: "+line+"\n")
                if not line_list:
                    continue
                if line_list[0] == "include:":
                    if line_list[1:]:
                        includes.append(line)
                        with open(include_module_report, "a") as f:
                            f.write("Found include. Collected line: " + line + "\n")
                    else:
                        empty_include = True
                if line_list[0] == "module":
                    found_module = True
            return includes, modules
        # get all documents and update them one by one
        documents = self.coll.find({})
        for doc in documents:
            _id = ObjectId(doc["_id"])
            files = doc["commit_content"]["files"]
            index = 0
            for file in files:
                with open(log_path, "a") as f:
                    f.write("On Object with _id: " + str(doc["_id"]) + "\n")
                try:
                    content = file["sha_contents"]["content"]
                    includes, modules = get_includes_and_modules(content)
                    sub_doc_url = "commit_content.files." + str(index) + ".includes"
                    self.coll.update_one(
                        {"_id": _id},
                        {"$set": {sub_doc_url: includes}}
                    )
                    sub_doc_url = "commit_content.files." + str(index) + ".modules"
                    self.coll.update_one(
                        {"_id": _id},
                        {"$set": {sub_doc_url: modules}}
                    )
                    index += 1
                    with open(log_path, "a") as f:
                        f.write("Successfully updated file " + file["filename"] + "\n")
                except Exception as e:
                    with open(log_path, "a") as f:
                        f.write("Failed to update file: " + file["filename"])
                        f.write(" with error: " + str(e) + "\n")