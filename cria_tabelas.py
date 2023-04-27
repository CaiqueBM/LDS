import sqlite3
import os
import re
import datetime


# Define o diretório raiz
diretorio = r"C:\\Users\\lanch\\Desktop\\Projeto"

# Conexão com o banco de dados
conn = sqlite3.connect("database.db")
c = conn.cursor()

# Cria as tabelas se não existirem

c.execute(
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        username TEXT PRIMARY KEY,
        senha TEXT
    )
"""
)

c.execute(
    """
    CREATE TABLE IF NOT EXISTS log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        login_time DATETIME
    )
"""
)

c.execute(
    """
    CREATE TABLE IF NOT EXISTS arquivos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        projeto TEXT,
        caminho TEXT UNIQUE,
        status TEXT,
        responsavel TEXT,
        data_criado TEXT,
        data_avaliacao TEXT,
        data_revisao TEXT,
        aprovador TEXT,
        data_aprovado TEXT,
        descricao TEXT
        linha INTEGER
    )
"""
)

# Percorre recursivamente todos os diretórios a partir do diretório raiz
for raiz, _, arquivos in os.walk(diretorio):
    for nome_arquivo in arquivos:
        # Para cada arquivo, extraia o nome do projeto a partir do caminho
        # completo usando uma expressão regular
        caminho_completo = os.path.join(raiz, nome_arquivo)
        projeto = re.search(r"(?<=\\)[0-9]+ - (.+?)(?=\\)", caminho_completo)
        projeto_arquivo = projeto.group(1) if projeto else None

        # Obtenha a data de criação do arquivo
        data_criacao = os.path.getctime(caminho_completo)
        data_criacao = datetime.datetime.fromtimestamp(data_criacao)

        # Para cada arquivo, insira um registro na tabela do banco de dados
        c.execute(
            "INSERT OR IGNORE INTO arquivos (nome, caminho, projeto, data_criado) VALUES (?, ?, ?, ?)",
            (
                nome_arquivo,
                caminho_completo,
                projeto_arquivo,
                data_criacao.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()

# Fecha a conexão com o banco de dados
conn.close()
