import sqlite3
import os
import re
import datetime

diretorio = r"C:\\Users\\lanch\\Desktop\\Projeto"


def gerar():
    # Define o diretório raiz

    # Conexão com o banco de dados
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Cria as tabelas se não existirem

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
            nome TEXT UNIQUE,
            projeto TEXT,
            caminho TEXT UNIQUE,
            status TEXT,
            responsavel TEXT,
            data_criado TEXT,
            data_avaliacao TEXT,
            data_revisao TEXT,
            aprovador TEXT,
            data_aprovado TEXT,
            data_entregue TEXT,
            descricao TEXT,
            tagfinanceiro TEXT
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS dados_projeto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto TEXT,
            abreviacao TEXT,
            descricao TEXT
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS dados_arquivo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            projeto TEXT,
            titulo TEXT
        )
    """
    )

    padrao = r"Arquivos do Projeto\\([^\\]+)"

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

            resultado = re.search(padrao, caminho_completo)
            if resultado:
                diretorio_status = resultado.group(1)

            if diretorio_status == "Area de Trabalho":
                padrao = r"Area de Trabalho\\([^\\]+)"

                resultado = re.search(padrao, caminho_completo)
                if resultado:
                    diretorio_verificado = resultado.group(1)
                    responsavel = diretorio_verificado

                c.execute(
                    "INSERT OR IGNORE INTO arquivos (nome, caminho, projeto, data_criado, status, responsavel) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        nome_arquivo,
                        caminho_completo,
                        projeto_arquivo,
                        data_criacao.strftime("%Y-%m-%d %H:%M:%S"),
                        status,
                        responsavel,
                    ),
                )
                conn.commit()

            elif diretorio_status == "Para Avaliacao":
                status = "Para Avaliacao"

            elif diretorio_status == "Para Entrega":
                status = "Para Entrega"

            elif diretorio_status == "Para Revisao":
                status = "Para Revisao"

            if diretorio_status is not "Area de Trabalho":
                # Para cada arquivo, insira um registro na tabela do banco de dados
                c.execute(
                    "INSERT OR IGNORE INTO arquivos (nome, caminho, projeto, data_criado, status, responsavel) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        nome_arquivo,
                        caminho_completo,
                        projeto_arquivo,
                        data_criacao.strftime("%Y-%m-%d %H:%M:%S"),
                        status,
                        responsavel,
                    ),
                )
                conn.commit()

    # Fecha a conexão com o banco de dados
    conn.close()
