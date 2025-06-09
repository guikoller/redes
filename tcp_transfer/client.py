import socket
import hashlib
import threading
import os
import protocolo

def calcular_hash_bytes(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

def receber_do_servidor(sock):
    # Thread para receber e processar dados do servidor
    # Gerencia a comunicação assíncrona do cliente
    buffer = b''
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("\n[INFO] Conexão com o servidor foi fechada.")
                break
            
            buffer += data

            while True:
                if buffer.startswith(b'CHAT:'):
                    try:
                        mensagem_completa, buffer = buffer.split(b'\n', 1)
                        print(f"\r[CHAT] {mensagem_completa[5:].decode(protocolo.CODIFICACAO)}\n> ", end='')
                    except ValueError:
                        break
                
                elif protocolo.DELIMITADOR_HEADER in buffer:
                    header_bytes, buffer = buffer.split(protocolo.DELIMITADOR_HEADER, 1)
                    
                    # Lógica de Protocolo: Interpreta a resposta do servidor
                    metadados = protocolo.parsear_cabecalho(header_bytes)

                    if metadados and metadados.get('status') == 'OK':
                        # Lógica de Aplicação: Inicia o recebimento do arquivo
                        receber_arquivo(sock, metadados, buffer)
                        buffer = b''
                    elif metadados:
                        print(f"\r[ERRO DO SERVIDOR] {metadados.get('status')}\n> ", end='')
                    else:
                        print("\r[ERRO] Recebido cabeçalho inválido do servidor.\n> ", end='')
                else:
                    break
        except (ConnectionResetError, ConnectionAbortedError):
            print("\n[INFO] Conexão encerrada.")
            os._exit(1)
        except Exception as e:
            print(f"\n[ERRO] Falha na comunicação: {e}")
            os._exit(1)

def receber_arquivo(sock, metadados, buffer_inicial):
    # Args:
    # sock: O objeto socket conectado
    # metadados (dict): Um dicionário com nome, tamanho e hash do arquivo
    # buffer_inicial (bytes): Bytes que já foram lidos do socket
    nome = metadados['nome']
    tamanho = metadados['tamanho']
    hash_esperado = metadados['hash']
    print(f"\r[ARQUIVO] Recebendo '{nome}' ({tamanho} bytes)...")

    dados_arquivo = bytearray(buffer_inicial)
    total_recebido = len(buffer_inicial)

    while total_recebido < tamanho:
        dados = sock.recv(min(4096, tamanho - total_recebido))
        if not dados:
            raise ConnectionError("Conexão interrompida durante o download.")
        dados_arquivo.extend(dados)
        total_recebido += len(dados)
        print(f"\r[ARQUIVO] {total_recebido}/{tamanho} bytes recebidos...", end='')

    print("\n[ARQUIVO] Download completo. Verificando integridade...")
    hash_recebido = calcular_hash_bytes(dados_arquivo)

    if hash_recebido == hash_esperado:
        with open("recebido_" + nome, 'wb') as f:
            f.write(dados_arquivo)
        print(f"[✓] Arquivo '{nome}' recebido com sucesso e verificado.")
    else:
        print(f"[✗] Arquivo corrompido! Hash não confere.")
    
    print("> ", end='')

def cliente_main():
    host = input("IP do servidor: ")
    porta = int(input("Porta: "))
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, porta))
        print(f"[✓] Conectado ao servidor {host}:{porta}.")
    except socket.error as e:
        print(f"[ERRO] Não foi possível conectar: {e}")
        return

    threading.Thread(target=receber_do_servidor, args=(s,), daemon=True).start()

    print("\nComandos: SAIR | ARQUIVO nome.ext | CHAT mensagem")
    while True:
        try:
            comando_input = input("> ")
            if not comando_input:
                continue

            if comando_input.upper() == "SAIR":
                s.sendall("SAIR".encode(protocolo.CODIFICACAO))
                break

            elif comando_input.upper().startswith("ARQUIVO "):
                nome_arquivo = comando_input.split(" ", 1)[1]
                s.sendall(protocolo.create_requisicao_arquivo(nome_arquivo))

            elif comando_input.upper().startswith("CHAT "):
                mensagem = comando_input.split(" ", 1)[1]
                s.sendall(protocolo.create_requisicao_chat(mensagem))

            else:
                print("[ERRO] Comando inválido.")
        except (socket.error, BrokenPipeError):
            print("\n[ERRO] Conexão com o servidor perdida.")
            break
        except KeyboardInterrupt:
            s.sendall("SAIR".encode(protocolo.CODIFICACAO))
            break
            
    s.close()
    print("[INFO] Conexão fechada.")

if __name__ == "__main__":
    cliente_main()