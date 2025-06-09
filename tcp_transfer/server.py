import socket
import threading
import os
import hashlib
import protocolo

HOST = '0.0.0.0'
PORT = 5001
clients = []
clients_lock = threading.Lock()

def calcular_hash_sha256(caminho_arquivo):
    sha256 = hashlib.sha256()
    with open(caminho_arquivo, 'rb') as f:
        for bloco in iter(lambda: f.read(4096), b''):
            sha256.update(bloco)
    return sha256.hexdigest()

def enviar_para_todos(mensagem):
    msg_formatada = protocolo.create_msg_chat_broadcast(mensagem)
    with clients_lock:
        for cliente in list(clients):
            try:
                cliente.sendall(msg_formatada)
            except socket.error:
                clients.remove(cliente)

def lidar_com_cliente(conn, addr):
    print(f"[+] Conectado por {addr}")
    with clients_lock:
        clients.append(conn)
    
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            comando = data.decode(protocolo.CODIFICACAO).strip()

            if comando == "SAIR":
                break

            elif comando.startswith("ARQUIVO "):
                nome_arquivo = comando.split(" ", 1)[1]
                print(f"[REQUISIÇÃO] Cliente {addr} solicitou '{nome_arquivo}'")
                
                if os.path.isfile(nome_arquivo):
                    # Lógica de Aplicação: Obter dados do arquivo
                    tamanho = os.path.getsize(nome_arquivo)
                    hash_arquivo = calcular_hash_sha256(nome_arquivo)

                    # Lógica de Protocolo: Monta e envia a resposta
                    cabecalho = protocolo.create_cabecalho_arquivo(nome_arquivo, tamanho, hash_arquivo)
                    conn.sendall(cabecalho)
                    
                    with open(nome_arquivo, 'rb') as f:
                        while (chunk := f.read(4096)):
                            conn.sendall(chunk)
                else:
                    # Lógica de Protocolo: Monta e envia um erro
                    erro = protocolo.create_erro_arquivo_nao_encontrado()
                    conn.sendall(erro)

            elif comando.startswith("CHAT "):
                msg = comando.split(" ", 1)[1]
                print(f"[CHAT de {addr}]: {msg}")
                enviar_para_todos(f"[{addr[0]}:{addr[1]}] {msg}")

            else:
                conn.sendall(protocolo.create_comando_invalido())
    except ConnectionResetError:
        print(f"[-] Conexão com {addr} foi resetada.")
    finally:
        print(f"[-] Cliente {addr} desconectado.")
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()

def console_servidor():
    # lẽ mensagens do console e envia para todos os clientes conectados
    while True:
        msg = input()
        if msg:
            enviar_para_todos(f"[Servidor]: {msg}")

def iniciar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[SERVIDOR INICIADO] Escutando em {HOST}:{PORT}")
        
        threading.Thread(target=console_servidor, daemon=True).start()

        while True:
            conn, addr = s.accept()
            threading.Thread(target=lidar_com_cliente, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    iniciar_servidor()