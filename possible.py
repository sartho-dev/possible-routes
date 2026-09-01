import requests
from urllib.parse import urljoin, urlparse
import time
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


def parse_url(url):

    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or 80
    path = parsed.path    

    return host, port, path 

def create_socket(routes):
    host, port, path = parse_url(routes)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(request_timeout)
    try:
        sock.connect((host, port))
        request = f"HEAD {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode()
        sock.sendall(request)

        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(4096)
            if not chunk:          
                break
            response += chunk

       
        first_line = response.split(b"\r\n", 1)[0]
        
        try:
            status_code = int(first_line.split(b" ")[1])
        except (IndexError, ValueError):
            status_code = 0
        return status_code
    finally:
        sock.close()


def requests_send():
    total = len(possible_routes_api)
    for idx, routes in enumerate(possible_routes_api, 1):
        try:
            status_code = create_socket(routes)

            first_path = extract_from_path(routes)
            key = (first_path, status_code)

            if(key not in results):
                results[key] = []

            results[key].append(routes)
            
        except socket.timeout:
            key = ("__erro__", "timeout")
            results.setdefault(key, []).append(routes)
        except ConnectionRefusedError:
            key = ("__erro__", "connection_refused")
            results.setdefault(key, []).append(routes)

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