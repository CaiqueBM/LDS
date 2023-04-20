import sqlite3
import os
import re

# Define o diretório raiz
diretorio = r"Z:\\Projetos"

# Conexão com o banco de dados
conn = sqlite3.connect("database.db")
c = conn.cursor()

# Cria as tabelas se não existirem
c.execute(
    """
    CREATE TABLE IF NOT EXISTS log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        login_time TEXT
    )
"""
)

c.execute(
    """
    CREATE TABLE IF NOT EXISTS arquivos (
        nome TEXT,
        projeto TEXT,
        caminho TEXT PRIMARY KEY,
        status TEXT,
        responsavel TEXT,
        data_criado TEXT,
        data_avaliacao TEXT,
        data_revisao TEXT,
        aprovador TEXT,
        data_aprovado TEXT,
        descricao TEXT
    )
"""
)


# Percorre recursivamente todos os diretórios a partir do diretório raiz
for diretorio_atual, subdiretorios, arquivos in os.walk(diretorio):
    for nome_arquivo in arquivos:
        caminho_completo = os.path.join(diretorio_atual, nome_arquivo)

        # Tratamento para conexão de rede
        try:
            with open(caminho_completo, "r", encoding="utf-8") as f:
                pass
        except Exception as e:
            print(f"Erro ao abrir arquivo: {e}")
            continue

        # Extrai o nome do projeto usando expressão regular
        projeto = re.search(r"(?<=Projetos\\).*?(?=\\)", caminho_completo)
        projeto_arquivo = projeto.group(0)

        c.execute(
            "INSERT INTO arquivos (nome, projeto, caminho) VALUES (?, ?, ?)",
            (nome_arquivo, projeto_arquivo, caminho_completo),
        )
        conn.commit()

        # Seleciona os arquivos duplicados e imprime o resultado
        cursor = c.execute(
            "SELECT caminho, COUNT(*) FROM arquivos GROUP BY caminho HAVING COUNT(*) > 1"
        )
        duplicados = cursor.fetchall()

        print("Arquivos duplicados:")
        for dup in duplicados:
            print(f"Nome do arquivo: {dup[0]} - Quantidade: {dup[1]}")

# Fecha a conexão com o banco de dados
conn.close()


# Busca os valores que vao para a tabela de projeto dos usuarios
def get_data():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT nome, projeto FROM arquivos")
    data = c.fetchall()
    conn.close()
    return data
