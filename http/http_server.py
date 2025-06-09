# http_server_final.py
import socket
import threading
import os

HOST = '0.0.0.0'
PORT = 8080

def get_mime_type(filepath):
    if filepath.endswith(".html"):
        return "text/html; charset=utf-8"
    if filepath.endswith(".jpeg") or filepath.endswith(".jpg"):
        return "image/jpeg"
    if filepath.endswith(".css"):
        return "text/css"
    # Tipo binário padrão tipo genérico de dado
    return "application/octet-stream"

def create_200_response(filepath):
    try:
        content_type = get_mime_type(filepath)
        
        with open(filepath, 'rb') as f:
            body = f.read()
        
        headers = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        ).encode('utf-8')

        return headers + body
        
    except FileNotFoundError:
        return create_404_response()

def create_404_response():
    body = b"<html><body><h1>404 Arquivo Nao Encontrado</h1></body></html>"
    headers = (
        f"HTTP/1.1 404 Not Found\r\n"
        f"Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    ).encode('utf-8')
    return headers + body

def parse_request(request_bytes):
    try:
        request_str = request_bytes.decode('utf-8')
        first_line = request_str.split('\n')[0]
        method, path, _ = first_line.split()
        return method, path
    except (ValueError, IndexError):
        return None, None

def handle_request(connection, address):
    print(f"[NOVA CONEXAO] {address} conectado.")

    try:
        request_bytes = connection.recv(2048)
        if not request_bytes:
            return

        method, path = parse_request(request_bytes)

        if not method:
            print(f"[ERRO] Requisicao malformada de {address}")
            return
            
        print(f"[{address}] Requisicao: {method} {path}")

        if path == '/':
            path = '/index.html'

        # Mapeia o caminho da URL para um nome de arquivo local
        filename = path.strip('/')
        
        if os.path.isfile(filename):
            response = create_200_response(filename)
        else:
            print(f"[ERRO] Arquivo nao encontrado: {filename}")
            response = create_404_response()

        connection.sendall(response)

    except Exception as e:
        print(f"[ERRO INESPERADO] {e}")
    finally:
        print(f"[CONEXAO FECHADA] {address}")
        connection.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[SERVIDOR HTTP INICIADO] Escutando em http://{HOST if HOST != '0.0.0.0' else '127.0.0.1'}:{PORT}")

        while True:
            connection, address = server_socket.accept()
            # Cria uma nova thread para cada requisição
            thread = threading.Thread(target=handle_request, args=(connection, address))
            thread.start()
            
    except OSError as e:
        print(f"[ERRO FATAL] Nao foi possivel iniciar o servidor: {e}")
    finally:
        server_socket.close()
        print("[SERVIDOR DESLIGADO]")

if __name__ == "__main__":
    start_server()