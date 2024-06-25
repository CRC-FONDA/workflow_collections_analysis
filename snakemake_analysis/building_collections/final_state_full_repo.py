from datetime import datetime
from base64 import b64decode

from .github_api.basics import get_url_content

from ..db_operations.db_connector import DBConnector
db = DBConnector()


def add_repo_to_collection(repo):
    # insert base document to be updated with file contents
    inserted = db.final_state_full_repo.insert_one({
        "repo": repo,
        "scrape_time": datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
    })
    _id = inserted.inserted_id

    # get repo file contents
    git_url = "https://api.github.com/repos/" + repo + "/contents/"

    # extract data from response
    def collect_content(item, path, _id):
        path = path + "/" + item["name"]
        if item["type"] == "dir":
            item_list = get_url_content(item["url"])
            for new_item in item_list:
                collect_content(new_item, path, _id)
        elif item["type"] == "file":
            file_data = get_url_content(item["url"])
            if not file_data:
                print("no contents for "+path)
                return
            base64_content = file_data["content"]
            decoded_content = str(b64decode(base64_content))
            db.final_state_full_repo.find_one_and_update(
                {"_id": _id},
                {"$set": {
                    "files."+path.replace(".", "_"): {
                        "content": decoded_content,
                        "filename": file_data["name"],
                        "size": file_data["size"]
                    }
                }}
            )
            print("file", path)
        else:
            print("unknown type in item collection for: "+path)
    # run recursion start
    base_item_list = get_url_content(git_url)
    if not base_item_list:
        return
    base_path = ""
    for base_item in base_item_list:
        collect_content(base_item, base_path, _id)


