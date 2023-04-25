from flask import (
    Flask,
    session,
    render_template,
    make_response,
    request,
    redirect,
    url_for,
    flash,
)
import pandas as pd
import datetime
import sqlite3
import cria_tabelas
from flask_bootstrap import Bootstrap

df_tabela = pd.DataFrame

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


# Rota da pagina usuario, todas acoes serao dadas aqui


@app.route("/projetos")
def user():
    if "username" in session:
        username = session["username"]
        login_time = session["login_time"]

        conn = sqlite3.connect("database.db")
        df = pd.read_sql_query(f"SELECT DISTINCT projeto FROM arquivos", conn)
        conn.close()

        # Adiciona um link no nome dos projetos na coluna "projeto" da tabela
        df["projeto"] = (
            "<a href='/projetos/" + df["projeto"] + "'>" + df["projeto"] + "</a>"
        )

        # Renderiza a página "user.html" e passa os dados da tabela "arquivos" para a variável "tabela"
        tabela = df.to_html(
            classes="table table-striped table-user", escape=False, index=False
        )

        return render_template(
            "projetos.html", username=username, login_time=login_time, tabela=tabela
        )
    else:
        # redirecionando para a página de login se o nome de usuário não estiver na sessão
        return redirect("/")


@app.route("/user")
def projetos():
    global df_tabela

    if "username" in session:
        # recuperando o nome de usuário da sessão
        username = session["username"]
        login_time = session["login_time"]

        conn = sqlite3.connect("database.db")
        df_tabela = pd.read_sql_query(
            f"SELECT nome, status, responsavel, data_avaliacao FROM arquivos WHERE responsavel = '{username}'",
            # f"SELECT * FROM arquivos WHERE responsavel = '{session['username']}'", conn
            conn,
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


# Rota para abrir os documentos de um determinado projeto
@app.route("/projetos/<projeto>")
def documentos(projeto):
    global df_tabela

    username = session["username"]
    login_time = session["login_time"]

    conn = sqlite3.connect("database.db")
    # c = conn.cursor()
    # c.execute(f'''SELECT * FROM arquivos WHERE projeto="{(projeto)}"''')
    # documentos = c.fetchall()
    df_tabela = pd.read_sql_query(
        f'''SELECT * FROM arquivos WHERE projeto="{(projeto)}"''',
        conn,
    )
    documentos = [tuple(row) for row in df_tabela.values]

    conn.close()

    # obtém a URL da página anterior
    referrer = request.referrer

    response = make_response(
        render_template(
            "documentos.html",
            username=username,
            login_time=login_time,
            projeto=projeto,
            documentos=documentos,
            referrer=referrer,
        )
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/atualizar_linha", methods=["POST"])
def atualizar_linha():
    global df_tabela

    projeto = request.form["projeto"]
    linha_selecionada = request.form.getlist("selecionados")

    df_tabela["linha"] = 0
    for linha in linha_selecionada:
        df_tabela["linha"] = 1

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Define todas as linhas para 0, exceto a selecionada, que será atualizada para 1
    c.execute("UPDATE arquivos SET linha = 0 WHERE projeto = ?", (projeto,))
    for linha in linha_selecionada:
        c.execute("UPDATE arquivos SET linha = 1 WHERE id = ?", (linha,))

    conn.commit()
    conn.close()
    df_tabela.drop(df_tabela.index, inplace=True)
    return redirect(url_for("documentos", projeto=projeto))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
