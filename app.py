from flask import (
    Flask,
    session,
    render_template,
    make_response,
    request,
    redirect,
    url_for,
    flash,
    send_file,
)
import pandas as pd
import datetime
import sqlite3
from cria_tabelas import gerar
from flask_bootstrap import Bootstrap
import os
import re
import shutil
import difflib
import zipfile


gerar()
df_tabela = pd.DataFrame
diretorio_raiz = r"C:\Users\lanch\Desktop\Projeto"

app = Flask(__name__)


app.static_folder = "static"
app.secret_key = "2@2"
bootstrap = Bootstrap(app)


@app.route("/")
def index():
    return render_template("login.html")


# Rota login de usuario


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    with open("users.csv", "r", encoding="utf-8") as file:
        for line in file:
            fields = line.strip().split(";")
            if fields[0] == username and fields[1] == password:
                now = datetime.datetime.now()
                login_time = now.strftime("%d/%m/%Y %H:%M:%S")
                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                c.execute(
                    "INSERT INTO log (username, login_time) VALUES (?, ?)",
                    (username, login_time),
                )
                conn.commit()
                conn.close()
                session["username"] = username
                session["login_time"] = login_time
                return redirect("/user")

    flash("Nome de usuário ou senha incorretos")
    return render_template("login.html")


# Rota para sair da sessão


@app.route("/logout")
def logout():
    session.pop("username", None)  # Remover nome do usuário da sessão
    return redirect(url_for("index"))


# ----------------- Rota da pagina usuario, todas acoes serao dadas aqui---------------S


@app.route("/user")
def user():
    global df_tabela

    if "username" in session:
        # recuperando o nome de usuário da sessão
        username = session["username"]
        login_time = session["login_time"]
        conn = sqlite3.connect("database.db")
        df_tabela = pd.read_sql_query(
            f"SELECT DISTINCT projeto FROM arquivos WHERE responsavel = '{username}'",
            conn,
        )

        df_tabela["projeto"] = df_tabela["projeto"].apply(
            lambda x: f"<a href='/user/{x}'>{x}</a>"
        )

        # Feche a conexão com o banco de dados
        conn.close()
        tabela_projetos = df_tabela.to_html(
            classes="table table-striped table-user", escape=False, index=False
        )
        return render_template(
            "user.html",
            username=username,
            login_time=login_time,
            tabela_projetos=tabela_projetos,
        )
    else:
        # redirecionando para a página de login se o nome de usuário não estiver na sessão
        return redirect("/")


# Rota para abrir os documentos de um determinado projeto do usuario
@app.route("/user/<projeto>", methods=["GET", "POST"])
def user_projetos(projeto):
    global df_tabela

    username = session["username"]
    login_time = session["login_time"]

    conn = sqlite3.connect("database.db")

    df_tabela = pd.read_sql_query(
        f"SELECT * FROM arquivos WHERE projeto=? AND responsavel=?",
        conn,
        params=(projeto, username),
    )

    conn.close()
    doc = [tuple(row) for row in df_tabela.values]
    # obtém a URL da página anterior
    status_list = df_tabela["status"].unique()

    response = make_response(
        render_template(
            "user_projetos.html",
            username=username,
            login_time=login_time,
            projeto=projeto,
            status_list=status_list,
            doc=doc,
        )
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/projetos", methods=["GET"])
def projetos():
    if "username" in session:
        username = session["username"]
        login_time = session["login_time"]
        global df_tabela
        global diretorio_raiz
        df_link = pd.DataFrame(columns=["projeto"])

        for pasta in os.listdir(diretorio_raiz):
            if os.path.isdir(os.path.join(diretorio_raiz, pasta)):
                caminho_projeto = os.path.join(diretorio_raiz, pasta)
                projeto_arquivo = re.search(
                    r"\d...([A-Za-z\s]+[\w-]+)", caminho_projeto
                )
                if projeto_arquivo:
                    projeto = projeto_arquivo.group(1)
                else:
                    projeto = ""
                df_link.loc[len(df_link)] = [projeto]

        # Adiciona um link no nome dos projetos na coluna "projeto" da tabela
        df_link["projeto"] = (
            "<a href='/projetos/"
            + df_link["projeto"]
            + "'>"
            + df_link["projeto"]
            + "</a>"
        )

        # Renderiza a página "user.html" e passa os dados da tabela "arquivos" para a variável "tabela"
        tabela = df_link.to_html(
            classes="table table-striped table-user",
            escape=False,
            index=False,
            table_id="myTable",
        )

        return render_template(
            "projetos.html", username=username, login_time=login_time, tabela=tabela
        )
    else:
        # redirecionando para a página de login se o nome de usuário não estiver na sessão
        return redirect("/")


# Rota para abrir os documentos de um determinado projeto
@app.route("/projetos/<projeto>")
def documentos(projeto):
    global df_tabela

    username = session["username"]
    login_time = session["login_time"]

    # Diretorio dos arquivos Default para criar para começar um projeto
    diretorio = r"C:\\Users\\lanch\\Desktop\\Default"
    arquivos_na_pasta = [arquivo for arquivo in os.listdir(diretorio)]

    conn = sqlite3.connect("database.db")
    df_tabela = pd.read_sql_query(
        f'''SELECT * FROM arquivos WHERE projeto="{(projeto)}"''',
        conn,
    )
    documentos = [tuple(row) for row in df_tabela.values]

    status_list = df_tabela["status"].unique()

    conn.close()
    df_tabela.drop(df_tabela.index, inplace=True)

    response = make_response(
        render_template(
            "documentos.html",
            username=username,
            login_time=login_time,
            projeto=projeto,
            documentos=documentos,
            status_list=status_list,
            arquivos=arquivos_na_pasta,
        )
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ---------------------------- Atualizar o status do responsavel ------------------


@app.route("/atualizar_status", methods=["POST"])
def atualizar_status():
    global df_tabela
    global diretorio_raiz
    status = [
        "Criado",
        "Em Desenvolvimento",
        "Para Avaliacao",
        "Para Entrega",
    ]
    username = session["username"]
    now = datetime.datetime.now()
    data_atualizada = now.strftime("%d/%m/%Y %H:%M:%S")
    projeto = request.form["projeto"]
    linha_selecionada = request.form.getlist("selecionados")
    linha_selecionada = list(map(int, linha_selecionada))
    tamanho = len(linha_selecionada)

    conn = sqlite3.connect("database.db")
    query = "SELECT * FROM arquivos"
    df_tabela = pd.read_sql_query(query, conn)
    df_selecionado = df_tabela.loc[df_tabela["id"].isin(linha_selecionada)]
    nome_arq = df_selecionado["nome"].values.tolist()
    caminho_projeto = df_selecionado["caminho"].values.tolist()
    status_atual = df_selecionado["status"].values.tolist()
    id_documentos = df_selecionado["id"].values.tolist()
    conn.close()

    # Precisa de uma logica para verificar o status atual de cada arquivo marcado na checkbox
    pasta_destino = ""

    if status_atual[0] == "Criado":
        if caminho_projeto is not None:
            projeto_arquivo = re.search(r"\d...([A-Za-z\s]+[\w-]+)", caminho_projeto[0])
            projeto_arquivo = projeto_arquivo.group(0)

        # Itera sobre os resultados e move cada arquivo para a pasta de destino
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        for i in range(tamanho):
            nome_do_arquivo = os.path.basename(caminho_projeto[i])

            # Atualiza o status do arquivo na base de dados
            novo_status = status[(status.index(status_atual[i]) + 1) % len(status)]
            query = f"""UPDATE arquivos SET status = '{novo_status}', responsavel = '{username}', data_avaliacao = '{data_atualizada}' WHERE id = '{id_documentos[i]}' """
            c.execute(query)
            conn.commit()

        conn.close()
    elif status_atual[0] == "Em Desenvolvimento":
        if caminho_projeto is not None:
            projeto_arquivo = re.search(r"\d...([A-Za-z\s]+[\w-]+)", caminho_projeto[0])
            projeto_arquivo = projeto_arquivo.group(0)

        pasta_destino = os.path.join(
            diretorio_raiz, projeto_arquivo, "Arquivos do Projeto", "Para Avaliacao"
        )

        # Itera sobre os resultados e move cada arquivo para a pasta de destino
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        for i in range(tamanho):
            nome_do_arquivo = os.path.basename(caminho_projeto[i])
            novo_caminho = os.path.join(pasta_destino, nome_arq[i])

            # Atualiza o status do arquivo na base de dados
            novo_status = status[(status.index(status_atual[i]) + 1) % len(status)]
            query = f"""UPDATE arquivos SET caminho='{novo_caminho}', status = '{novo_status}', responsavel = '{username}', data_avaliacao = '{data_atualizada}' WHERE id = '{id_documentos[i]}' """
            c.execute(query)
            conn.commit()
            shutil.move(caminho_projeto[i], pasta_destino)

        conn.close()
    elif status_atual[0] == "Para Avaliacao":
        if caminho_projeto is not None:
            projeto_arquivo = re.search(r"\d...([A-Za-z\s]+[\w-]+)", caminho_projeto[0])
            projeto_arquivo = projeto_arquivo.group(0)

        pasta_destino = os.path.join(
            diretorio_raiz, projeto_arquivo, "Arquivos do Projeto", "Para Entrega"
        )
        # Itera sobre os resultados e move cada arquivo para a pasta de destino
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        for i in range(tamanho):
            nome_do_arquivo = os.path.basename(caminho_projeto[i])
            novo_caminho = os.path.join(pasta_destino, nome_arq[i])

            # Atualiza o status do arquivo na base de dados
            novo_status = status[(status.index(status_atual[i]) + 1) % len(status)]
            query = f"""UPDATE arquivos SET caminho='{novo_caminho}', status = '{novo_status}', responsavel = '{username}', data_avaliacao = '{data_atualizada}' WHERE id = '{id_documentos[i]}' """
            c.execute(query)
            conn.commit()

            shutil.move(caminho_projeto[i], pasta_destino)

        conn.close()

    return redirect(url_for("user_projetos", projeto=projeto))


# ----------------------------------- ZIPAR ARQUIVOS -----------------------------
"""@app.route("/zip", methods=["POST"])
def zip_files():
    linha_selecionada = request.form.getlist("selecionados")
    # linha_selecionada = linha_selecionada.split(",")
    linha_selecionada = list(map(int, linha_selecionada))
    tamanho = len(linha_selecionada)

    conn = sqlite3.connect("database.db")
    query = "SELECT * FROM arquivos"
    df_tabela = pd.read_sql_query(query, conn)
    df_selecionado = df_tabela.loc[df_tabela["id"].isin(linha_selecionada)]
    nome_arq = df_selecionado["nome"].values.tolist()
    caminho_projeto = df_selecionado["caminho"].values.tolist()
    status_atual = df_selecionado["status"].values.tolist()
    id_documentos = df_selecionado["id"].values.tolist()
    conn.close()

    zip_filename = "GRD-" + status_atual + ".zip"  # nome do arquivo ZIP ()

    with zipfile.ZipFile(zip_filename, "w") as zip:
        # Adiciona cada arquivo no diretório ao arquivo ZIP
        for file in os.listdir(caminho_projeto):
            if os.path.isfile(os.path.join(caminho_projeto, file)):
                zip.write(os.path.join(caminho_projeto, file), file)
    # Envia o arquivo ZIP de volta para o cliente
    return send_file(zip_filename, mimetype="zip", as_attachment=True)"""


# -------------------------------------- CRIAR ARQUIVOS --------------------------------------


@app.route("/criar_arquivo", methods=["POST"])
def criar_arquivo():
    global df_tabela
    global diretorio_raiz
    projeto = request.form["projeto"]
    username = session["username"]
    now = datetime.datetime.now()
    data_atualizada = now.strftime("%d/%m/%Y %H:%M:%S")
    diretorio_novos = os.path.join(
        diretorio_raiz,
        difflib.get_close_matches(projeto, os.listdir(diretorio_raiz))[0],
    )
    diretorio_default = (
        r"C:\\Users\\lanch\\Desktop\\Default"  # Diretorio para os arquivos Default
    )

    nome_arquivo = request.form["nome_arquivo"]
    extensao = request.form["extensao_arquivo"]
    arquivo_existente = request.form["arquivo_existente"]

    nome_arquivo = nome_arquivo + "_Rev0" + "." + extensao

    if not df_tabela.empty:
        nova_linha = df_tabela.index[-1]
    else:
        nova_linha = 0  # ou qualquer outro valor válido para o seu caso
    df_tabela["nome"][nova_linha] = nome_arquivo
    df_tabela["responsavel"][nova_linha] = username
    df_tabela["status"][nova_linha] = "Criado"
    df_tabela["data_criado"][nova_linha] = data_atualizada

    caminho_origem = os.path.join(diretorio_default, arquivo_existente)

    # Caminho de destino tem que ser a pasta do usuario na area de trabalho
    caminho_destino = os.path.join(
        diretorio_novos,
        "Arquivos do Projeto",
        "Area de Trabalho",
        username,
        nome_arquivo,
    )

    shutil.copyfile(caminho_origem, caminho_destino)

    projeto_arquivo = re.search(r"\d...([A-Za-z\s]+[\w-]+)", caminho_destino)
    projeto_arquivo = projeto_arquivo.group(1) if projeto else None

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO arquivos (nome, status, responsavel, data_criado, caminho, projeto) VALUES (?, ?, ?, ?, ?, ?)",
        (
            nome_arquivo,
            "Criado",
            username,
            data_atualizada,
            caminho_destino,
            projeto_arquivo,
        ),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("documentos", projeto=projeto))


@app.route("/criar_projeto", methods=["POST"])
def criar_projeto():
    global diretorio_raiz
    pasta_default = r"C:\Users\lanch\Desktop\Projeto\3 - Caique"
    nome_projeto = request.form["nome_projeto"]
    tipo_projeto = request.form["tipo_projeto"]

    projetos = os.listdir(diretorio_raiz)
    maior_numero = 0
    for projeto in projetos:
        numero = re.search(r"^(\d+) -", projeto)
        if numero:
            numero_int = int(numero.group(1))
            if numero_int > maior_numero:
                maior_numero = numero_int
    numero_projeto = maior_numero + 1
    nome_projeto = str(numero_projeto) + " - " + nome_projeto + "-ABS-" + tipo_projeto

    pasta_atualizada = os.path.join(diretorio_raiz, nome_projeto)

    shutil.copytree(pasta_default, pasta_atualizada)
    return redirect(url_for("projetos"))


# --------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
