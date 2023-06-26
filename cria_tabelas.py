import sqlite3
import os
import re
import datetime

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

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS log_tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            projeto TEXT,
            status TEXT,
            data_status TEXT,
            responsavel TEXT
        )
    """
    )
    
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS diretorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            diretorio_raiz TEXT,
            diretorio_default TEXT,
            caminho_padrao TEXT,
            pasta_padrao_projeto TEXT
        )
    """
    )

    diretorio_raiz = r"""/media/hdfs/Engenharia/Projetos"""
    diretorio_default = r"""/media/hdfs/Engenharia/Projetos\Sistema LDS/Modelos de Arquivos"""
    caminho_padrao = r"""/media/hdfs/Engenharia/Projetos\Sistema LDS/GRD E LD padrao"""
    pasta_padrao_projeto = r"""/media/hdfs/Engenharia/Projetos/0000 - Novo Projeto"""

    diretorios = {
        "1": "diretorio_raiz",
        "2": "diretorio_default",
        "3": "caminho_padrao",
        "4": "pasta_padrao_projeto",
    }
    for n in range(1, 5):
        descricao = diretorios[str(n)]
        diretorio = eval(descricao)

        c.execute(
            "INSERT INTO diretorios (descricao, diretorio) VALUES (?, ?)",
            (descricao, diretorio),
        )
        conn.commit()
    conn.close()

    padrao_projetos = f"""Arquivos do Projeto\\\\([^\\\\]+)"""
    padrao_area_trabalho = f"""Area de Trabalho\\\\([^\\\\]+)"""
    diretorio = r"C:\Users\lanch\Desktop\Projeto"
    diretorio_status = ""

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

            resultado_projetos = re.search(padrao_projetos, caminho_completo)

            if resultado_projetos:
                diretorio_status = resultado_projetos.group(1)

            if str(diretorio_status) != "Referencias":
                if re.search(r"LD", nome_arquivo):
                    status = "Entregue"

                elif re.search(r"GRD", nome_arquivo):
                    status = "Entregue"

                elif diretorio_status == "Area de Trabalho":
                    resultado_pasta = re.search(padrao_area_trabalho, caminho_completo)

                    if resultado_pasta:
                        responsavel = resultado_pasta.group(1)

                    status = "Criado"
                    aprovador = None

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
                    aprovador = "Andre"
                    responsavel = "Andre"

                elif diretorio_status == "Para Entrega":
                    partes_subpasta = raiz.split("\\")
                    sub_pasta = partes_subpasta[8]

                    if sub_pasta != "Lixo":
                        if sub_pasta == "Aprovados":
                            status = "Para Entrega"
                            aprovador = "Andre"
                            responsavel = "Andre"
                        else:
                            status = "Entregue"
                            aprovador = "Andre"
                            responsavel = "Andre"
                    else:
                        continue

                elif diretorio_status == "Para Revisao":
                    continue

                if diretorio_status != "Area de Trabalho":
                    # Para cada arquivo, insira um registro na tabela do banco de dados
                    c.execute(
                        "INSERT OR IGNORE INTO arquivos (nome, caminho, projeto, data_criado, status, responsavel, aprovador) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            nome_arquivo,
                            caminho_completo,
                            projeto_arquivo,
                            data_criacao.strftime("%Y-%m-%d %H:%M:%S"),
                            status,
                            responsavel,
                            aprovador,
                        ),
                    )
                    conn.commit()

                    # Fecha a conexão com o banco de dados
    conn.close()
