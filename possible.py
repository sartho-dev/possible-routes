import asyncio
from urllib.parse import urljoin, urlparse

base_url = "http://localhost:80/"

request_timeout = 2.0      # timeout em segundos para cada requisição
max_concurrency = 50       # número máximo de conexões simultâneas
possible_routes_api = []
results = {}


def load_wordlists():
    """Carrega as wordlists de top-level e subpaths."""
    with open("wordlists/top-level.txt", "r", encoding="utf-8") as f:
        top = [line.strip() for line in f if line.strip()]
    with open("wordlists/subpaths.txt", "r", encoding="utf-8") as f:
        subs = [line.strip() for line in f if line.strip()]
    return top, subs


def concatenate_routes(top_level, subpaths):
    """Gera todas as combinações de URLs a partir das wordlists."""
    for routes in top_level:
        less_url = urljoin(base_url, routes)
        possible_routes_api.append(less_url)
        for sub in subpaths:
            full_url = urljoin(base_url, f"{routes}/{sub}")
            possible_routes_api.append(full_url)


def save_output(groups):
    """Salva os grupos no arquivo saida.txt, filtrando 404 e ordenando."""
    with open("saida.txt", "w", encoding="utf-8") as archive:
        filtered_items = [(k, v) for k, v in groups.items() if k[1] != 404]
        sorted_items = sorted(filtered_items, key=lambda item: len(item[1]), reverse=False)

        for (first_path, status_code), urls in sorted_items:
            line = f"{first_path}/* -> {status_code} ({len(urls)} ocorrências)"
            print(line, file=archive)
            # Mostra até 3 exemplos
            exemplos = ", ".join(urls[:3])
            if len(urls) > 3:
                exemplos += ", ..."
            print(f"    Exemplos: {exemplos}", file=archive)


def extract_from_path(url):
    """Extrai o primeiro segmento da URL (ex: '/status/abc' -> 'status')."""
    parsed = urlparse(url)
    path = parsed.path
    parts = [p for p in path.split("/") if p]
    return parts[0] if parts else "(raiz)"


def parse_url(url):
    """Separa a URL em host, porta e path."""
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or 80
    path = parsed.path or "/"
    return host, port, path


async def fetch_status(url, semaphore):
    """Faz uma requisição HEAD assíncrona e retorna o status code."""
    try:
        async with semaphore:
            host, port, path = parse_url(url)
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=request_timeout
            )

            # Monta a requisição HEAD manualmente
            request = f"HEAD {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode()
            writer.write(request)
            await writer.drain()

            # Lê até encontrar o fim dos headers (\r\n\r\n)
            response = b""
            try:
                while b"\r\n\r\n" not in response:
                    chunk = await asyncio.wait_for(reader.read(4096), timeout=request_timeout)
                    if not chunk:
                        break
                    response += chunk
            except asyncio.TimeoutError:
                pass  # timeout durante leitura, consideramos resposta parcial

            writer.close()
            await writer.wait_closed()

            if not response:
                return None  # sem resposta

            # Extrai status code da primeira linha
            first_line = response.split(b"\r\n", 1)[0]
            try:
                status_code = int(first_line.split(b" ")[1])
                return status_code
            except (IndexError, ValueError):
                return 0  # resposta malformada

    except asyncio.TimeoutError:
        return "timeout"
    except ConnectionRefusedError:
        return "connection_refused"
    except Exception as e:
        return f"error_{type(e).__name__}"


async def worker(url, semaphore):
    """Processa uma URL, agrupando o resultado."""
    status_code = await fetch_status(url, semaphore)

    if status_code is None:
        return

    # Se for string, é um erro
    if isinstance(status_code, str):
        first_path = "__erro__"
        key = (first_path, status_code)
    else:
        first_path = extract_from_path(url)
        key = (first_path, status_code)

    if key not in results:
        results[key] = []
    results[key].append(url)


async def main():
    top_level, subpaths = load_wordlists()
    print(f"Top levels carregados: {len(top_level)}")
    print(f"Subpaths carregados: {len(subpaths)}")

    concatenate_routes(top_level, subpaths)
    total = len(possible_routes_api)
    print(f"URLs geradas: {total}")

    # Semáforo para limitar concorrência
    semaphore = asyncio.Semaphore(max_concurrency)

    # Cria tarefas para todas as URLs
    tasks = [worker(url, semaphore) for url in possible_routes_api]

    # Executa com barra de progresso simples
    done = 0
    for coro in asyncio.as_completed(tasks):
        await coro
        done += 1
        if done % 50 == 0:
            print(f"Progresso: {done}/{total}")

    save_output(results)


if __name__ == "__main__":
    asyncio.run(main())