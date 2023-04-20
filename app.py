from flask import Flask, session, render_template, request, redirect, url_for, flash
import pandas as pd
import datetime
import sqlite3
import cria_tabelas
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.static_folder = "static"
app.secret_key = "2@2"
bootstrap = Bootstrap(app)


@app.route("/")
def index():
    return render_template("index.html")


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
    return render_template("index.html")


# Rota para sair da sessão


@app.route("/logout")
def logout():
    session.pop("username", None)  # Remover nome do usuário da sessão
    return redirect(url_for("index"))


# Rota da pagina usuario, todas acoes serao dadas aqui


@app.route("/user")
def user():
    if (
        "username" in session
    ):  # verificando se o nome de usuário está armazenado na sessão
        # recuperando o nome de usuário da sessão
        username = session["username"]
        login_time = session["login_time"]
        # now = datetime.datetime.now()
        # login_time = now.strftime("%d/%m/%Y %H:%M:%S")

        conn = sqlite3.connect("database.db")
        # Consulta na tabela "arquivos" com base no nome do usuário logado
        df = pd.read_sql_query(
            f"SELECT DISTINCT projeto FROM arquivos",
            conn
            # f"SELECT * FROM arquivos WHERE responsavel = '{session['username']}'", conn
        )
        # Fecha a conexão com o banco de dados
        conn.close()

        # Renderiza a página "user.html" e passa os dados da tabela "arquivos" para a variável "tabela"
        tabela = df.to_html(classes="table table-striped")

        return render_template(
            "user.html", username=username, login_time=login_time, tabela=tabela
        )
    else:
        # redirecionando para a página de login se o nome de usuário não estiver na sessão
        return redirect("/")


@app.route("/projetos")
def projetos():
    if (
        "username" in session
    ):  # verificando se o nome de usuário está armazenado na sessão
        # recuperando o nome de usuário da sessão
        username = session["username"]
        login_time = session["login_time"]

        # Renderiza o template com o nome e o caminho do último arquivo adicionado pelo usuário logado

        return render_template(
            "projetos.html", username=username, login_time=login_time
        )
    else:
        # redirecionando para a página de login se o nome de usuário não estiver na sessão
        return redirect("/")


# Rota para abrir os documentos de um determinado projeto


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
