import asyncio
from urllib.parse import urljoin, urlparse

base_url = "http://localhost:80/"

request_timeout = 2.0      # timeout em segundos para cada requisição
max_concurrency = 50       # número máximo de conexões simultâneas
max_queue_size = 100       # teto da fila de URLs
results = {}


def load_wordlists():
    """Carrega as wordlists de top-level e subpaths."""
    with open("wordlists/top-level.txt", "r", encoding="utf-8") as f:
        top = [line.strip() for line in f if line.strip()]
    with open("wordlists/subpaths.txt", "r", encoding="utf-8") as f:
        subs = [line.strip() for line in f if line.strip()]
    return top, subs


def concatenate_routes(top_level, subpaths):
    """Generator que produz URLs uma a uma."""
    for routes in top_level:
        yield urljoin(base_url, routes)
        for sub in subpaths:
            yield urljoin(base_url, f"{routes}/{sub}")


def save_output(groups):
    """Salva os grupos no arquivo saida.txt, filtrando 404 e ordenando."""
    with open("saida.txt", "w", encoding="utf-8") as archive:
        filtered_items = [(k, v) for k, v in groups.items() if k[1] != 404]
        sorted_items = sorted(filtered_items, key=lambda item: len(item[1]), reverse=False)

        for (first_path, status_code), urls in sorted_items:
            line = f"{first_path}/* -> {status_code} ({len(urls)} ocorrências)"
            print(line, file=archive)
            exemplos = ", ".join(urls[:3])
            if len(urls) > 3:
                exemplos += ", ..."
            print(f"    Exemplos: {exemplos}", file=archive)


def extract_from_path(url):
    """Extrai o primeiro segmento da URL."""
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

            request = f"HEAD {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode()
            writer.write(request)
            await writer.drain()

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


async def producer(queue, top_level, subpaths, num_workers):
    """Produtor: coloca URLs na fila e sentinelas ao final."""
    for url in concatenate_routes(top_level, subpaths):
        await queue.put(url)

    # Coloca None para cada worker sinalizar término
    for _ in range(num_workers):
        await queue.put(None)


async def worker(queue, semaphore, processed_counter):
    """Consumidor: retira URLs da fila e processa."""
    while True:
        url = await queue.get()
        if url is None:
            queue.task_done()
            break

        try:
            status_code = await fetch_status(url, semaphore)
        except Exception:
            status_code = "unexpected_error"

        if status_code is not None:
            if isinstance(status_code, str):
                first_path = "__erro__"
            else:
                first_path = extract_from_path(url)

            key = (first_path, status_code)
            if key not in results:
                results[key] = []
            results[key].append(url)

        processed_counter[0] += 1
        if processed_counter[0] % 50 == 0:
            print(f"Processadas: {processed_counter[0]} URLs")

        queue.task_done()


async def main():
    top_level, subpaths = load_wordlists()
    print(f"Top levels carregados: {len(top_level)}")
    print(f"Subpaths carregados: {len(subpaths)}")

    queue = asyncio.Queue(maxsize=max_queue_size)
    semaphore = asyncio.Semaphore(max_concurrency)

    processed_counter = [0]
    num_workers = max_concurrency

    # Cria workers
    workers = [asyncio.create_task(worker(queue, semaphore, processed_counter))
               for _ in range(num_workers)]

    # Executa produtor
    await producer(queue, top_level, subpaths, num_workers)

    # Aguarda todos os workers terminarem
    await asyncio.gather(*workers)

    print(f"Total de URLs processadas: {processed_counter[0]}")
    save_output(results)


if __name__ == "__main__":
    asyncio.run(main())