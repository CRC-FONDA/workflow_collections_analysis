import urllib.request
import json
import time


def handle_github_rate_limit(response):
    headers = response.headers.as_string()
    header = "X-RateLimit-Remaining:"
    if header not in headers:
        return
    begin = headers.find(header) + len(header)
    end = headers.find("\n", begin)
    limit = int(headers[begin:end])
    if limit % 100 == 0:
        print("current github rate limit:", limit)
    if limit < 100:
        time.sleep(60)


def get_url_content(url):
    try:
        with open("github_scraping/building_collections/github_api/token.txt", "r") as f:
            github_token = f.read().strip()
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('Authorization', f'token {github_token}')
        response = urllib.request.urlopen(req)
    except Exception as e:
        print("failed to get content from:  " + url + "\nError: " + str(e))
        return None

    # handle github rate limit
    handle_github_rate_limit(response)

    return json.load(response)
