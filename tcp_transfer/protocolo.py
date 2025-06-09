DELIMITADOR_HEADER = b'\n\n'
DELIMITADOR_LINHA = '\n'
CODIFICACAO = 'utf-8'

def create_requisicao_arquivo(nome_arquivo):
    return f"ARQUIVO {nome_arquivo}".encode(CODIFICACAO)

def create_requisicao_chat(mensagem):
    return f"CHAT {mensagem}".encode(CODIFICACAO)

def create_msg_chat_broadcast(mensagem):
    return f"CHAT:{mensagem}\n".encode(CODIFICACAO)

def create_cabecalho_arquivo(nome_arquivo, tamanho_arquivo, hash_arquivo):
    headers = [
        "STATUS:OK",
        f"NOME:{nome_arquivo}",
        f"TAMANHO:{tamanho_arquivo}",
        f"HASH:{hash_arquivo}"
    ]
    return (DELIMITADOR_LINHA.join(headers)).encode(CODIFICACAO) + DELIMITADOR_HEADER

def create_erro_arquivo_nao_encontrado():
    return b"STATUS:ERRO_ARQUIVO_NAO_ENCONTRADO" + DELIMITADOR_HEADER

def create_comando_invalido():
    return b"STATUS:COMANDO_INVALIDO" + DELIMITADOR_HEADER

def parsear_cabecalho(header_bytes):
    # Interpreta os bytes do cabeçalho e retorna um dicionário com os dados retorna none se invalidos 
    try:
        dados = {}
        header_str = header_bytes.decode(CODIFICACAO)
        linhas = header_str.split(DELIMITADOR_LINHA)
        
        status_key, status_value = linhas[0].split(':', 1)
        dados[status_key.lower()] = status_value

        if status_value == 'OK':
            for linha in linhas[1:]:
                chave, valor = linha.split(':', 1)
                dados[chave.lower()] = valor
            dados['tamanho'] = int(dados['tamanho'])
        
        return dados
    except (ValueError, IndexError):
        return None