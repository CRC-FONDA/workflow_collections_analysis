import urllib.request
import json
from base64 import b64decode
from ..github_api.basics import get_url_content


def concatenate_suffixes(keys):
    if type(keys) is dict:
        keys = [concatenate_suffixes(k) for k in keys.keys()]
    elif isinstance(keys, str):
        return keys
    suffix = ""
    for k in keys:
        suffix += ("." + k)
    return suffix


def update_no_content_files():
    from ...db_operations.db_connector import DBConnector
    db = DBConnector()

    full_data = db.final_state.find()
    repos = 0
    files = 0
    no_content = 0
    new_contents = 0
    for repo in full_data:
        repos += 1
        print("REPOS:", repos)
        print("NEW CONTENTS:", new_contents)
        for file_name, file in repo["files"].items():
            files += 1
            if "content" not in file:
                no_content += 1
                #print("NO CONTENT!")
                #print(repo["repo"], file_name)
                suffix = concatenate_suffixes(file)
                #print("number of keys:", len(keys))

                file_url = "https://api.github.com/repos/" + repo["repo"] + "/contents/" + file_name + suffix
                #print(file_url)

                file_data = get_url_content(file_url)
                if not file_data:
                    print("no contents for " + file_url)
                    continue
                #print("FILE_DATA:", file_data.keys())
                base64_content = file_data["content"]
                decoded_content = str(b64decode(base64_content))
                try:
                    db.final_state.find_one_and_update(
                        {"repo": repo["repo"]},
                        {"$set": {
                            "files." + file_name.replace(".", "_"): {
                                "content": decoded_content,
                                "fixed_no_content": True,
                                "filename": file_data["name"],
                                "size": file_data["size"]
                            }
                        }}
                    )
                except Exception as e:
                    print("Failed tp update database document: " + str(e))

                new_contents += 1

    print("files:", files)
    print("no_content:", no_content)
