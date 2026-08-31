linha = "HTTP/1.1 200 OK\r\n"
partes = linha.split("\r\n", 1)[0]
print(partes) 