def iterate_all_files():
    from ..db_operations.db_connector import DBConnector
    db = DBConnector()
    full_data = db.final_state.find()
    for repo in full_data:
        for file_name, file in repo["files"].items():
            print(repo["repo"], file_name)
            yield repo["repo"], file_name, get_file_content(file, file_name=file_name)


def iterate_workflow_files(repo):
    for file_name in repo["workflow_files"]:
        # print("repo: "+str(repo["repo"])+", filename: "+file_name)
        try:
            file = repo["files"][file_name]
        except KeyError as e:
            file_candidates = [name for name in repo["files"].keys() if name.endswith(file_name)]
            if not file_candidates or len(file_candidates) > 1:
                print("no unique workflow file (" + file_name + ") in repo: " + repo["repo"])
                continue
            else:
                file_name = file_candidates[0]
                file = repo["files"][file_name]
        yield file, file_name


def get_file_content(file, file_name=None):
    try:
        return file["content"].split("\\n")
    except KeyError as e:
        if file_name:
            print("No content for file: " + file_name)
            print(file.keys())
            print(type(file))
        else:
            print("No content for this file.")
        return None
