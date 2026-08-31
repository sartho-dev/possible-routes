import requests
from urllib.parse import urljoin, urlparse
import time
import http.client
import socket


base_url = "http://localhost:80/"

request_timeout = 0.1
request_delay = 0.01
general_results = []
possible_routes_api = []
results = {}


def load_wordlists():
    with open("top-level.txt", "r", encoding="utf-8") as f:
        top = [line.strip() for line in f if line.strip()]
    with open("subpaths.txt", "r", encoding="utf-8") as f:
        subs = [line.strip() for line in f if line.strip()]

    return top, subs

def concatenate_routes(top_level, subpaths):
    for routes in top_level:
        less_url = urljoin(base_url, routes)
        possible_routes_api.append(less_url)
        for sub in subpaths:
            full_url = urljoin(base_url, f"{routes}/{sub}")
            possible_routes_api.append(full_url)


def save_output(groups):
    with open("saida.txt", "w", encoding="utf-8") as archive:
        filtered_items = [(k, v) for k, v in groups.items() if k[1] != 404]

        sorted_items = sorted(filtered_items, key=lambda item: len(item[1]), reverse=False)

        for (first_path, status_code), urls in sorted_items: 
            line = f"{first_path}/* -> {status_code} ({len(urls)} ocorrências)"
            print(line,file=archive)


def extract_from_path(url):

    parsed = urlparse(url)
    path = parsed.path
    first_path = path.split("/")[1] 

    return first_path 
     
def requests_send():
    total = len(possible_routes_api)
    for idx, routes in enumerate(possible_routes_api, 1):
        try:
            possible_request = requests.head(routes, timeout=request_timeout)

            status_code = possible_request.status_code

            first_path = extract_from_path(routes)

            key = (first_path, status_code)

            if(key not in results):
                results[key] = []

            results[key].append(routes)
            
        except requests.exceptions.RequestException as erro:
            print(f"ERRO: {erro}")

        if idx % 50 == 0:
            print(f"Progresso: {idx}/{total}")

        time.sleep(request_delay)

def main():
      top_level, subpaths = load_wordlists()
      print(f"Top levels carregados: {len(top_level)}")
      print(f"Subpaths carregados: {len(subpaths)}")
      concatenate_routes(top_level, subpaths)
      requests_send()
      save_output(results)


if __name__ == "__main__":
    main()