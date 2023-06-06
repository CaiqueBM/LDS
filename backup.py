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
import csv

# from babkuppy import para_avaliacao
from cria_tabelas import gerar
from flask_bootstrap import Bootstrap
import os
import re
import shutil
import difflib
import xlwings as xw


app = Flask(__name__)


gerar()
df_tabela = pd.DataFrame
df_arquivo = pd.DataFrame(columns=["nome", "projeto", "titulo"])
diretorio_raiz = r"C:\Users\lanch\Desktop\Projeto"
diretorio_default = r"C:\\Users\\lanch\\Desktop\\Default"
atualizar = "intermedio"
pasta_destino = ""
linha_selecionada = ""
df_projeto = pd.DataFrame(columns=["projeto", "abreviacao", "descricao"])
novo_caminho = ""
control = ""
responsavel_status = ""
df_selecionado = pd.DataFrame
aprovado_exibido = False
mudar_status = ""
abreviacao = ""
data_atualizada = ""

app.static_folder = "static"
app.secret_key = "2@2"
bootstrap = Bootstrap(app)


@app.route("/")
def index():
    return render_template("login.html")


# Rota login de usuario


@app.route("/login", methods=["POST"])
def login():
    global abreviacao
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
                session["abreviacao"] = fields[2]
                abreviacao = session["abreviacao"]
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
            f"SELECT DISTINCT projeto FROM arquivos WHERE (responsavel = '{username}' OR aprovador = '{username}')",
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
    if "username" in session:
        global df_tabela
        global pasta_destino
        global atualizar
        global control
        global responsavel_status
        global df_selecionado
        global aprovado_exibido
        global mudar_status
        global abreviacao
        global data_atualizada

        username = session["username"]
        login_time = session["login_time"]
        abreviacao = session["abreviacao"]

        conn = sqlite3.connect("database.db")

        df_tabela = pd.read_sql_query(
            f"SELECT * FROM arquivos WHERE projeto=? AND (responsavel=? OR aprovador=?)",
            conn,
            params=(projeto, username, username),
        )

        conn.close()

        if control == "atualizar":
            atualizar = "atualizar"
        elif control == "renomear":
            atualizar = "renomear"
        elif control == "gerar_grd":
            atualizar = "gerar_grd"
        else:
            atualizar = "intermedio"

        nome_pasta = False
        doc = [tuple(row) for row in df_tabela.values]
        # obtém a URL da página anterior
        status_list = df_tabela["status"].unique()

        if not df_selecionado.empty:
            doc_selecionado = [tuple(row) for row in df_selecionado.values]
            for item in doc_selecionado:
                if item[9] is not None and username in item[9]:
                    aprovado_exibido = False
                    break
                else:
                    aprovado_exibido = True

            return render_template(
                "user_projetos.html",
                username=username,
                login_time=login_time,
                projeto=projeto,
                status_list=status_list,
                doc=doc,
                nome_pasta=nome_pasta,
                pasta_destino=pasta_destino,
                atualizar=atualizar,
                responsavel_status=responsavel_status,
                doc_selecionado=doc_selecionado,
                aprovado_exibido=aprovado_exibido,
                abreviacao=abreviacao,
                data_atualizada=data_atualizada,
            )

        return render_template(
            "user_projetos.html",
            username=username,
            login_time=login_time,
            projeto=projeto,
            status_list=status_list,
            doc=doc,
            nome_pasta=nome_pasta,
            pasta_destino=pasta_destino,
            atualizar=atualizar,
            responsavel_status=responsavel_status,
            abreviacao=abreviacao,
            data_atualizada=data_atualizada,
        )


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

        # Renderiza a página "projetos.html" e passa os dados da tabela "arquivos" para a variável "tabela"
        tabela = df_link.to_html(
            classes="table table-striped table-user",
            escape=False,
            index=False,
            table_id="myTable",
        )

        return render_template(
            "projetos.html",
            username=username,
            login_time=login_time,
            tabela=tabela,
        )
    else:
        # redirecionando para a página de login se o nome de usuário não estiver na sessão
        return redirect("/")


# Rota para abrir os documentos de um determinado projeto
@app.route("/projetos/<projeto>")
def documentos(projeto):
    if "username" in session:
        global df_tabela
        global diretorio_default
        global df_arquivos

        username = session["username"]
        login_time = session["login_time"]

        # Diretorio dos arquivos Default para criar para começar um projeto
        arquivos_na_pasta = [arquivo for arquivo in os.listdir(diretorio_default)]

        conn = sqlite3.connect("database.db")

        df_tabela = pd.read_sql_query(
            f'''SELECT * FROM arquivos WHERE projeto="{(projeto)}"''',
            conn,
        )
        documentos = [tuple(row) for row in df_tabela.values]

        status_list = df_tabela["status"].unique()

        disc = []
        sub = []

        with open("disc.csv", "r", encoding="utf-8") as arquivo:
            for line in arquivo:
                fields = line.strip().split(";")
                disc.append(fields[1])

        with open("sub.csv", "r", encoding="utf-8") as arquivo:
            for line in arquivo:
                fields = line.strip().split(";")
                sub.append(fields[1])

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
                disc=disc,
                sub=sub,
            )
        )
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


# -------------- Atualizar o status do responsavel, gerar GRD ----------------
@app.route("/intermediador", methods=["POST"])
def intermediador():
    if "username" in session:
        global linha_selecionada
        global atualizar
        global control
        global responsavel_status
        global df_tabela
        global df_selecionado
        global mudar_status

        username = session["username"]
        projeto = request.form["projeto"]
        linha_selecionada = request.form.getlist("selecionados")
        linha_selecionada = list(map(int, linha_selecionada))

        conn = sqlite3.connect("database.db")
        query = "SELECT * FROM arquivos"
        df_tabela = pd.read_sql_query(query, conn)
        df_selecionado = df_tabela.loc[df_tabela["id"].isin(linha_selecionada)]
        status_atual = df_selecionado["status"].values.tolist()
        conn.close()

        responsavel_status = status_atual[0]

        control = "atualizar"

        return redirect(
            url_for(
                "user_projetos",
                projeto=projeto,
                responsavel_status=responsavel_status,
                atualizar=atualizar,
                df_selecionado=df_selecionado,
            )
        )


@app.route("/atualizar_status", methods=["GET", "POST"])
def atualizar_status():
    if "username" in session:
        global abreviacao
        global df_tabela
        global diretorio_raiz
        global pasta_destino
        global linha_selecionada
        global atualizar
        global control
        global responsavel_status
        global mudar_status
        global data_atualizada
        global abreviacao

        status = [
            "Criado",
            "Em Desenvolvimento",
            "Para Avaliacao",
            "Para Entrega",
            "Entregue",
        ]

        username = session["username"]
        projeto = request.form["projeto"]
        aprovador = request.form.get("aprovador", None)
        responsavel = request.form.get("nome_responsavel", None)
        status_aprovador = request.form.get("status_aprovador", None)
        status_atualizar = request.form.get("status_atualizar", None)
        now = datetime.datetime.now()
        data_atualizada = now.strftime("%d/%m/%Y")
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

        pasta_destino = ""

        if tamanho <= 0:
            control = ""
            linha_selecionada = []
            return redirect(
                url_for(
                    "user_projetos",
                    projeto=projeto,
                    atualizar=atualizar,
                    pasta_destino=pasta_destino,
                )
            )

        if (
            status_atualizar == "atualizar"
            or status_aprovador == "aprovado"
            or status_aprovador == "reprovado"
        ):
            if status_atual[0] == "Criado":
                control = ""
                linha_selecionada = []

                if caminho_projeto is not None:
                    projeto_arquivo = re.search(
                        r"\d...([A-Za-z\s]+[\w-]+)", caminho_projeto[0]
                    )
                    projeto_arquivo = projeto_arquivo.group(0)

                # Itera sobre os resultados e move cada arquivo para a pasta de destino
                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                for i in range(tamanho):
                    nome_do_arquivo = os.path.basename(caminho_projeto[i])

                    # Atualiza o status do arquivo na base de dados
                    novo_status = status[
                        (status.index(status_atual[i]) + 1) % len(status)
                    ]
                    query = f"""UPDATE arquivos SET status = '{novo_status}', responsavel = '{username}', data_avaliacao = '{data_atualizada}' WHERE id = '{id_documentos[i]}' """
                    c.execute(query)
                    conn.commit()

                conn.close()
                linha_selecionada = []
                df_tabela = df_tabela.dropna()
                df_selecionado = df_selecionado.dropna()
            elif status_atual[0] == "Em Desenvolvimento":
                control = ""
                linha_selecionada = []
                if caminho_projeto is not None:
                    projeto_arquivo = re.search(
                        r"\d...([A-Za-z\s]+[\w-]+)", caminho_projeto[0]
                    )
                    projeto_arquivo = projeto_arquivo.group(0)

                pasta_destino = os.path.join(
                    diretorio_raiz,
                    projeto_arquivo,
                    "Arquivos do Projeto",
                    "Para Avaliacao",
                )

                # Itera sobre os resultados e move cada arquivo para a pasta de destino
                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                for i in range(tamanho):
                    nome_do_arquivo = os.path.basename(caminho_projeto[i])
                    novo_caminho = os.path.join(pasta_destino, nome_arq[i])

                    # Atualiza o status do arquivo na base de dados
                    novo_status = status[
                        (status.index(status_atual[i]) + 1) % len(status)
                    ]
                    query = f"""UPDATE arquivos SET caminho='{novo_caminho}', status = '{novo_status}', responsavel = '{username}', data_avaliacao = '{data_atualizada}', aprovador = '{aprovador}' WHERE id = '{id_documentos[i]}' """
                    c.execute(query)
                    conn.commit()
                    shutil.move(caminho_projeto[i], pasta_destino)

                conn.close()
                linha_selecionada = []
                df_tabela = df_tabela.dropna()
            elif status_atual[0] == "Para Avaliacao":
                if status_aprovador == "reprovado":
                    control = ""
                    linha_selecionada = []

                    if caminho_projeto is not None:
                        projeto_arquivo = re.search(
                            r"\d...([A-Za-z\s]+[\w-]+)", caminho_projeto[0]
                        )
                        projeto_arquivo = projeto_arquivo.group(0)

                    pasta_destino = os.path.join(
                        diretorio_raiz,
                        projeto_arquivo,
                        "Arquivos do Projeto",
                        "Area de Trabalho",
                        responsavel,
                    )

                    # Itera sobre os resultados e move cada arquivo para a pasta de destino
                    conn = sqlite3.connect("database.db")
                    c = conn.cursor()
                    for i in range(tamanho):
                        nome_do_arquivo = os.path.basename(caminho_projeto[i])
                        novo_caminho = os.path.join(pasta_destino, nome_arq[i])

                        # Atualiza o status do arquivo na base de dados
                        novo_status = status[
                            (status.index(status_atual[i]) + 1) % len(status)
                        ]
                        query = f"""UPDATE arquivos SET caminho='{novo_caminho}', status = 'Em Desenvolvimento', responsavel = '{responsavel}', aprovador = '' WHERE id = '{id_documentos[i]}' """
                        c.execute(query)
                        conn.commit()

                        shutil.move(caminho_projeto[i], pasta_destino)

                    linha_selecionada = []
                    df_tabela = df_tabela.dropna()
                elif status_aprovador == "aprovado":
                    control = ""

                    if caminho_projeto is not None:
                        projeto_arquivo = re.search(
                            r"\d...([A-Za-z\s]+[\w-]+)", caminho_projeto[0]
                        )
                        projeto_arquivo = projeto_arquivo.group(0)

                    pasta_destino = os.path.join(
                        diretorio_raiz,
                        projeto_arquivo,
                        "Arquivos do Projeto",
                        "Para Entrega",
                        "novapasta",
                    )
                    os.makedirs(pasta_destino, exist_ok=True)

                    # Itera sobre os resultados e move cada arquivo para a pasta de destino
                    conn = sqlite3.connect("database.db")
                    c = conn.cursor()
                    for i in range(tamanho):
                        nome_do_arquivo = os.path.basename(caminho_projeto[i])
                        novo_caminho = os.path.join(pasta_destino, nome_arq[i])

                        # Atualiza o status do arquivo na base de dados
                        novo_status = status[
                            (status.index(status_atual[i]) + 1) % len(status)
                        ]
                        query = f"""UPDATE arquivos SET caminho='{novo_caminho}', status = '{novo_status}', responsavel = '{username}', data_aprovado = '{data_atualizada}' WHERE id = '{id_documentos[i]}' """
                        c.execute(query)
                        conn.commit()

                        shutil.move(caminho_projeto[i], pasta_destino)

                    conn.close()
                    linha_selecionada = []
                    df_tabela = df_tabela.dropna()
            elif status_atual[0] == "Para Entrega":
                print("0")
        elif status_atualizar == "gerar_grd":
            control = "gerar_grd"

        elif status_atualizar == "cancelar":
            linha_selecionada = []
            df_tabela = df_tabela.dropna()
            df_selecionado = df_selecionado.dropna()
            control = ""

        return redirect(
            url_for(
                "user_projetos",
                projeto=projeto,
                atualizar=atualizar,
                pasta_destino=pasta_destino,
                data_atualizada=data_atualizada,
                abreviacao=abreviacao,
            )
        )


@app.route("/renomear_pasta", methods=["POST"])
def renomear_pasta():
    if "username" in session:
        global df_tabela
        global pasta_destino
        global novo_caminho
        global atualizar
        global control
        global mudar_status

        projeto = request.form["projeto"]
        nome_pasta = request.form["nome_pasta"]
        caminho_projeto = request.form["caminho"]

        now = datetime.datetime.now()
        data_envio = now.strftime("%d/%m/%Y")

        conn = sqlite3.connect("database.db")
        query = "SELECT * FROM arquivos"
        df_renomear = pd.read_sql_query(query, conn)
        conn.close()

        projeto_arquivo = re.search(r"\d...([A-Za-z\s]+[\w-]+)", caminho_projeto)
        projeto_arquivo = projeto_arquivo.group(0)

        caminho_atual = os.path.join(
            diretorio_raiz,
            projeto_arquivo,
            "Arquivos do Projeto",
            "Para Entrega",
            "novapasta",
        )

        novo_caminho = os.path.join(
            diretorio_raiz,
            projeto_arquivo,
            "Arquivos do Projeto",
            "Para Entrega",
            nome_pasta,
        )

        os.rename(caminho_atual, novo_caminho)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        for index, row in df_renomear.iterrows():
            nome_do_arquivo = os.path.basename(row["caminho"])
            caminho_arq = os.path.join(caminho_atual, nome_do_arquivo)

            if row["caminho"] == caminho_arq:
                caminho_arq = os.path.join(novo_caminho, nome_do_arquivo)
                query = f"""UPDATE arquivos SET caminho = '{caminho_arq}' WHERE id = {row["id"]}"""
                c.execute(query)
                conn.commit()

        conn.close()

        control = ""

        return redirect(
            url_for(
                "user_projetos",
                projeto=projeto,
                atualizar=atualizar,
                data_envio=data_envio,
            )
        )


@app.route("/gerar_grd", methods=["POST"])
def gerar_grd():
    if "username" in session:
        global abreviacao
        global diretorio_raiz
        global pasta_destino
        global linha_selecionada
        global novo_caminho
        global df_projeto
        global df_arquivo
        global atualizar
        global control
        global df_tabela
        global mudar_status

        tipos = {
            "A": "PRELIMINAR",
            "B": "PARA APROVAÇAO",
            "C": "PARA CONHECIMENTO",
            "D": "PARA COTAÇAO",
            "E": "PARA CONSTRUÇAO",
            "F": "CONFORME COMPRADO",
            "G": "CONFORME CONSTRUIDO",
            "H": "CANCELADO",
        }
        username = session["username"]
        projeto_atual = request.form["projeto"]
        tipo = request.form["tipo"]
        descricao = request.form["descricao"]
        verificado = request.form["verificado"]
        aprovado = request.form["aprovado"]
        autorizado = request.form["autorizado"]

        # -------------------- Buscar nome do projeto na pasta --------------------
        folders = [
            f
            for f in os.listdir(diretorio_raiz)
            if os.path.isdir(os.path.join(diretorio_raiz, f))
        ]
        # Criar uma expressão regular para verificar se o nome da pasta contém a parte fornecida
        pattern = re.compile(rf".*{re.escape(projeto_atual)}.*", re.IGNORECASE)
        # Percorrer os nomes das pastas e verificar se eles correspondem à expressão regular
        projeto = [f for f in folders if re.match(pattern, f)]

        caminho_projeto = os.path.join(diretorio_raiz, projeto[0])
        caminho_verificado = os.path.join(
            caminho_projeto, "Arquivos do Projeto", "Para Entrega"
        )

        # buscar abreviacao
        conn = sqlite3.connect("database.db")
        query = "SELECT * FROM dados_projeto"
        df_projeto = pd.read_sql_query(query, conn)
        result_projeto = df_projeto[df_projeto["projeto"] == projeto[0]]
        abreviacao_empresa = result_projeto["abreviacao"].iloc[0]
        descricao_projeto = result_projeto["descricao"].iloc[0]

        # ------------------- LISTA DE DOCUMENTOS -------------------------
        # Fazer uma copia da GRD Padrao para a pasta a ser entregue ()
        caminho_padrao = r"C:\Users\lanch\Desktop\modeloGRD"
        caminho_ld_padrao = r"C:\Users\lanch\Desktop\modeloGRD\LD_padrao.xlsx"
        caminho_grd_padrao = r"C:\Users\lanch\Desktop\modeloGRD\GRD_padrao.xlsx"

        pastas = []
        pasta_GRD_recente = None
        ultima_data_criacao = 0
        # Percorre todos os diretórios e arquivos no caminho fornecido
        for diretorio_atual, subdiretorios, arquivos in os.walk(caminho_verificado):
            for subdiretorio in subdiretorios:
                pastas.append(subdiretorio)

                # Verifica se o nome da pasta contém "GRD"
                if re.search(r"GRD", subdiretorio):
                    caminho_pasta = os.path.join(diretorio_atual, subdiretorio)
                    data_criacao = os.path.getctime(caminho_pasta)
                    # Verifica se é a pasta mais recente
                    if (
                        data_criacao > ultima_data_criacao
                        and caminho_pasta == novo_caminho
                    ):
                        pasta_GRD_anterior = pasta_GRD_recente
                        pasta_GRD_recente = caminho_pasta

        # Gerar LD
        if pasta_GRD_anterior is None:
            # Criaçao de uma nova GRD, primeira entrega
            # Abrir o arquivo Excel
            app = xw.App(visible=False)
            workbook = app.books.open(caminho_ld_padrao)  # LD vazia para preencher
            # Obter a planilha desejada
            planilha = workbook.sheets["F. Rosto"]

            # Nome da Empresa-Cidade
            planilha.range("J1").value = projeto_atual  # projeto
            shape_empresa = planilha.shapes["nome_empresa1"]
            shape_empresa.text = projeto_atual  # projeto
            # Descriçao do projeto
            planilha.range("A5").value = descricao_projeto  # descricao_projeto

            # Logica para adicionar a primeira revisao
            X = 12  # linha 12 é a primeira a ser adicionada a revisao 0
            planilha.range("A" + str(X)).value = "0"  # Revisao
            # Tipo (TE)
            planilha.range("B" + str(X)).value = str(tipo)  # tipo TE
            """if tipo in tipos:
                tipo_te = tipos[tipo]
                planilha.range("B" + str(X)).value = str(tipo)  # tipo TE"""

            # Descriçao
            planilha.range("C" + str(X)).value = str(descricao)  # descricao_projeto

            # Feito por:
            planilha.range("J" + str(X)).value = abreviacao  # abreviacao do responsavel

            # Verificado
            planilha.range("K" + str(X)).value = verificado  # quem verificou
            # Aprovado
            planilha.range("L" + str(X)).value = aprovado  # quem aprovou
            # Aut.
            planilha.range("M" + str(X)).value = autorizado  # quem autorizou

            # Data de envio
            now = datetime.datetime.now()
            data_envio = now.strftime("%d/%m/%Y")
            planilha.range("N" + str(X)).value = data_envio  # data

            nome_ld = "ABS-" + abreviacao_empresa + "-LD-" + "001" + "_R0" + ".xlsx"
            planilha.range("J6").value = nome_ld  # nome da lista de documentos
            nome_ld = os.path.join(novo_caminho, nome_ld)

            # workbook.save(nome_ld)

            # Modificando a planilha LISTA
            planilha = workbook.sheets["Lista"]

            shape_empresa = planilha.shapes["nome_empresa2"]
            shape_empresa.text = projeto_atual  # projeto

            conn = sqlite3.connect("database.db")
            query = "SELECT * FROM arquivos"
            df_tabela = pd.read_sql_query(query, conn)
            df_selecionado = df_tabela.loc[df_tabela["id"].isin(linha_selecionada)]
            nome_arq = df_selecionado["nome"].values.tolist()
            status_atual = df_selecionado["status"].values.tolist()
            id_documentos = df_selecionado["id"].values.tolist()
            conn.close()

            padrao = r"R\d+"

            X = 11

            conn = sqlite3.connect("database.db")
            query = "SELECT * FROM dados_arquivo"
            df_arquivo = pd.read_sql_query(query, conn)

            for nome in nome_arq:
                result_arquivo = df_arquivo[df_arquivo["nome"] == nome]
                titulo = result_arquivo["titulo"].iloc[0]
                planilha.range("B" + str(X)).value = nome
                planilha.range("C" + str(X)).value = str(titulo)
                resultado = re.search(r"_Rev(\d+)", nome)
                if resultado:
                    revisao = resultado.group(1)
                    planilha.range("D" + str(X)).value = revisao
                expressoes = [
                    "LC",
                    "LD",
                    "LE",
                    "LI",
                    "LM",
                    "PLT",
                    "ET",
                    "SE",
                    "ILU",
                    "UNF",
                    "SPDA",
                    "TRIF",
                    "REDE",
                    "ARQR",
                    "DIAG",
                ]
                padrao = r"\b(?:{})\b".format("|".join(expressoes))
                match = re.search(padrao, nome)
                if match:
                    tipo_expressao = match.group(0)
                    # novo_nome = nome_arq.replace(expressao_encontrada, "")
                planilha.range("I" + str(X)).value = tipo_expressao
                planilha.range("F" + str(X)).value = "1"
                planilha.range("K" + str(X)).value = "100"

                A1 = ["SPDA", "SE", "UNF", "TRIF", "PLT", "SPDA", "REDE", "ILU"]
                A2 = []
                A3 = ["DIAG"]
                A4 = [
                    "LC",
                    "LD",
                    "LE",
                    "LI",
                    "LM",
                    "ET",
                ]

                if tipo_expressao in A1:
                    planilha.range("H" + str(X)).value = "A1"
                if tipo_expressao in A2:
                    planilha.range("H" + str(X)).value = "A2"
                if tipo_expressao in A3:
                    planilha.range("H" + str(X)).value = "A3"
                if tipo_expressao in A4:
                    planilha.range("H" + str(X)).value = "A4"
                X = X + 1

            workbook.save(nome_ld)
            # Fechar o arquivo Excel
            workbook.close()
            app.quit()
            # ------------------------- GRD ------------------------------------
            app = xw.App(visible=False)
            workbook = app.books.open(caminho_grd_padrao)  # LD vazia para preencher
            # Obter a planilha desejada
            planilha = workbook.sheets["GRD"]

            nome_grd = "GRD-ABS-" + abreviacao_empresa + "-001" + ".xlsx"
            nome_grd = os.path.join(novo_caminho, nome_grd)

            shape_empresa = planilha.shapes["nome_empresa3"]
            shape_empresa.text = str(projeto_atual)  # projeto

            planilha.range("N7").value = data_envio  # data de envio
            planilha.range("N10").value = "data_envio"  # data de envio

            X = 36
            planilha.range("A" + str(X)).value = "01"  # primeiro elemento
            planilha.range("H" + str(X)).value = nome_ld  # nome da lista de documentos
            planilha.range("K" + str(X)).value = "Lista de documentos"  # Revisao
            planilha.range("O" + str(X)).value = "0"  # Revisao
            planilha.range("P" + str(X)).value = str(tipo)  # tipo TE
            planilha.range("S" + str(X)).value = "1"  # Quantidade
            planilha.range("T" + str(X)).value = "DOC.ELETRÔNICO"  # Revisao
            planilha.range("V" + str(X)).value = "Original"  # Revisao
            padrao = r"R\d+"
            X = 37

            conn = sqlite3.connect("database.db")
            query = "SELECT * FROM dados_arquivo"
            df_arquivo = pd.read_sql_query(query, conn)

            for nome in nome_arq:
                planilha.range("A" + str(X)).value = str(X - 36)  #  proximos elementos
                result_arquivo = df_arquivo[df_arquivo["nome"] == nome]
                titulo = result_arquivo["titulo"].iloc[0]
                planilha.range("H" + str(X)).value = nome
                planilha.range("K" + str(X)).value = str(titulo)
                resultado = re.search(r"_Rev(\d+)", nome)
                if resultado:
                    revisao = resultado.group(1)
                    planilha.range("O" + str(X)).value = revisao
                planilha.range("P" + str(X)).value = str(tipo)  # tipo TE
                planilha.range("S" + str(X)).value = "1"
                planilha.range("T" + str(X)).value = "DOC.ELETRÔNICO"
                planilha.range("V" + str(X)).value = "Original"

                if tipo_expressao in A1:
                    planilha.range("Q" + str(X)).value = "A1"
                if tipo_expressao in A2:
                    planilha.range("Q" + str(X)).value = "A2"
                if tipo_expressao in A3:
                    planilha.range("Q" + str(X)).value = "A3"
                if tipo_expressao in A4:
                    planilha.range("Q" + str(X)).value = "A4"
                X = X + 1

            workbook.save(nome_grd)
            # Fechar o arquivo Excel
            workbook.close()
            app.quit()
        else:
            # Atualizaçao de uma GRD ja existente, subir revisao

            # Abrir o arquivo Excel
            app = xw.App(visible=False)
            workbook = app.books.open(caminho_ld_padrao)

            # Obter a planilha desejada
            planilha = workbook.sheets["F. Rosto"]
            # Nome da Empresa-Cidade
            planilha.range("J1").value = projeto  # projeto
            shape_empresa = planilha.shapes["Retângulo: Cantos Arredondados 4"]
            shape_empresa.text = projeto  # projeto
            # Descriçao do projeto
            planilha.range("A5").value = descricao_projeto  # descricao_projeto

            # Logica para ler qual a ultima revisao

            for row in planilha.range("A12:A31").options(ndim=2).value:
                for cell in row:
                    print(cell)
                    if cell is not None:
                        ultima_revisao = int(cell)
                        X = (
                            planilha.range("A" + str(planilha.cells.last_cell.row))
                            .end("up")
                            .row
                            + 1
                        )  # Proxima linha em branco, adicionar os parametros

            # Buscar o nome de todos os arquivos a serem enviados na pagina
            # Mostrar no formulario o nome de cada arquivo e na frente os campos necessarios
            # Revisao
            planilha.range("A" + str(X)).value = ultima_revisao + 1  # Revisao
            # Tipo (TE)
            if tipo in tipos:
                te = tipos[tipo]
                planilha.range("B" + str(X)).value = te  # tipo TE
            # Descriçao
            planilha.range("D" + str(X)).value = descricao  # descricao_projeto

            # Feito por:
            if username in nomes:
                abreviacao = nomes[username]
                planilha.range(
                    "J" + str(X)
                ).value = abreviacao  # abreviacao do responsavel

            # Verificado
            planilha.range("K" + str(X)).value = verificado  # quem verificou
            # Aprovado
            planilha.range("L" + str(X)).value = aprovado  # quem aprovou
            # Aut.
            planilha.range("M" + str(X)).value = autorizado  # quem autorizou

            # Data de envio
            now = datetime.datetime.now()
            data_envio = now.strftime("%d/%m/%Y")
            planilha.range("N" + str(X)).value = data_envio  # data

            nome_ld = "ABS-" + abreviacao_empresa + "-LD-" + "001" + "_R0" + ".xlsx"
            planilha.range("H7").value = nome_ld  # nome da lista de documentos
            nome_ld = os.path.join(caminho_padrao, nome_ld)

            conn = sqlite3.connect("database.db")
            query = "SELECT * FROM arquivos"
            df_tabela = pd.read_sql_query(query, conn)
            df_selecionado = df_tabela.loc[df_tabela["id"].isin(linha_selecionada)]
            nome_arq = df_selecionado["nome"].values.tolist()
            status_atual = df_selecionado["status"].values.tolist()
            id_documentos = df_selecionado["id"].values.tolist()
            conn.close()

            # Buscar o titulo
            conn = sqlite3.connect("database.db")
            query = "SELECT * FROM dados_projeto"
            df_projeto = pd.read_sql_query(query, conn)
            projeto_dados = df_projeto["projeto"].values.tolist()
            abreviacao_empresa = df_projeto["abreviacao"].values.tolist()
            descricao_projeto = df_projeto["descricao"].values.tolist()

            query = "SELECT * FROM dados_arquivo"
            df_arquivo = pd.read_sql_query(query, conn)
            nomes_arquivos = df_projeto["nome"].values.tolist()
            projeto = df_projeto["projeto"].values.tolist()
            titulo = df_projeto["titulo"].values.tolist()
            conn.close()

            padrao = r"R\d+"

            # Logica para ler qual a ultima revisao

            for row in planilha.range("A12:A31").options(ndim=2).value:
                for cell in row:
                    print(cell)
                    if cell is not None:
                        ultima_revisao = int(cell)
                        X = (
                            planilha.range("A" + str(planilha.cells.last_cell.row))
                            .end("up")
                            .row
                            + 1
                        )  # Proxima linha em branco, adicionar os parametros

            for i, nome in nome_arq:
                if nome == nomes:
                    planilha.range("B" + str(X)).value = nomes_arquivos[i]
                    planilha.range("C" + str(X)).value = titulo[i]
                    resultado = re.search(padrao, nomes_arquivos[i])
                    if resultado:
                        revisao = resultado.group(0)
                        planilha.range("D" + str(X)).value = revisao
                    expressoes = [
                        "LC",
                        "LD",
                        "LE",
                        "LI",
                        "LM",
                        "PLT",
                        "ET",
                        "SE",
                        "ILU",
                        "UNF",
                        "SPDA",
                        "TRIF",
                        "REDE",
                        "ARQR",
                        "DIAG",
                    ]
                    padrao = r"\b(?:{})\b".format("|".join(expressoes))
                    match = re.search(padrao, nome_arq)
                    if match:
                        tipo_expressao = match.group(0)
                        # novo_nome = nome_arq.replace(expressao_encontrada, "")
                    planilha.range("I" + str(X)).value = tipo_expressao
                    planilha.range("F" + str(X)).value = "1"
                    planilha.range("K" + str(X)).value = "100"

                    A1 = ["SPDA", "DIAG", "SE", "UNF", "TRIF", "PLT", "SPDA", "REDE"]
                    A2 = []
                    A3 = []
                    A4 = ["LC", "LD", "LE", "LI", "LM", "ET", "ILU"]

                    if tipo_expressao == "A1":
                        planilha.range("H" + str(X)).value = "A1"
                    if tipo_expressao == "A2":
                        planilha.range("H" + str(X)).value = "A2"
                    if tipo_expressao == "A3":
                        planilha.range("H" + str(X)).value = "A3"
                    if tipo_expressao == "A4":
                        planilha.range("H" + str(X)).value = "A4"
                    X = X + 1

            workbook.save(nome_ld)

            # Fechar o arquivo Excel
            workbook.close()
            app.quit()

            pasta_GRD_recente = None
            pasta_GRD_anterior = None

        control = ""

        return redirect(
            url_for(
                "user_projetos",
                projeto=projeto,
            )
        )


# -------------------------------------- CRIAR ARQUIVOS --------------------------------------


@app.route("/criar_arquivo", methods=["POST"])
def criar_arquivo():
    if "username" in session:
        global df_tabela
        global diretorio_raiz
        global diretorio_default
        global df_projeto
        global df_arquivo

        projeto = request.form["projeto"]
        username = session["username"]
        disciplina = request.form["disc"]
        sub = request.form["sub"]
        titulo = request.form["titulo"]

        now = datetime.datetime.now()
        data_atualizada = now.strftime("%d/%m/%Y %H:%M:%S")

        diretorio_novos = os.path.join(
            diretorio_raiz,
            difflib.get_close_matches(projeto, os.listdir(diretorio_raiz))[0],
        )

        # -------------------- Buscar nome do projeto na pasta --------------------
        folders = [
            f
            for f in os.listdir(diretorio_raiz)
            if os.path.isdir(os.path.join(diretorio_raiz, f))
        ]

        # Criar uma expressão regular para verificar se o nome da pasta contém a parte fornecida
        pattern = re.compile(rf".*{re.escape(projeto)}.*", re.IGNORECASE)

        # Percorrer os nomes das pastas e verificar se eles correspondem à expressão regular
        projeto = [f for f in folders if re.match(pattern, f)]

        # ---------------------Buscar abreviacao da empresa-------------------

        # Buscar o titulo
        conn = sqlite3.connect("database.db")
        query = "SELECT * FROM dados_projeto"
        df_projeto = pd.read_sql_query(query, conn)

        result = df_projeto[df_projeto["projeto"] == projeto[0]]

        abreviacao_empresa = result["abreviacao"].iloc[0]
        descricao_empresa = result["descricao"].iloc[0]

        arquivo_existente = request.form["arquivo_existente"]
        name, extension = os.path.splitext(arquivo_existente)

        # --------------- Sequencia dos arquivos ---------------------
        caminho_projeto = os.path.join(diretorio_raiz, projeto[0])
        # Encontre todos os arquivos no diretório
        files = os.listdir(caminho_projeto)
        # Expressão regular para extrair o número sequencial do nome do arquivo
        pattern = r"(\d{3})_R"
        seq = 0
        for file in files:
            # Verifique se o nome do arquivo corresponde ao padrão esperado
            match = re.search(pattern, file)
            if match:
                # Obtenha o número sequencial encontrado no nome do arquivo
                sequence = int(match.group(1))

                # Atualize o número sequencial máximo, se necessário
                if sequence > seq:
                    seq = sequence

        # ------------------- Buscar os dados no CSV ---------------------
        disc = []
        with open("disc.csv", "r", encoding="utf-8-sig") as arquivo:
            for line in arquivo:
                fields = line.strip().split(";")
                if fields[1] == disciplina:
                    disciplina = fields[0]
        sub1 = []
        with open("sub.csv", "r", encoding="utf-8-sig") as arquivo:
            for line in arquivo:
                fields = line.strip().split(";")
                if fields[1] == sub:
                    sub = fields[0]

        nome_arquivo = (
            "ABS-"
            + str(abreviacao_empresa)
            + "-"
            + str(disciplina)
            + "-"
            + str(sub)
            + "-"
            + str(seq)
            + "_Rev0"
            + str(extension)
        )

        """if not df_tabela.empty:
            nova_linha = df_tabela.index[-1]
        else:
            nova_linha = 0  # ou qualquer outro valor válido para o seu caso
        df_tabela["nome"][nova_linha] = nome_arquivo
        df_tabela["responsavel"][nova_linha] = username
        df_tabela["status"][nova_linha] = "Criado"
        df_tabela["data_criado"][nova_linha] = data_atualizada"""

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

        c.execute(
            "INSERT INTO dados_arquivo (nome, projeto, titulo) VALUES (?, ?, ?)",
            (nome_arquivo, projeto[0], titulo),
        )
        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "documentos",
                projeto=projeto,
                titulo=titulo,
            )
        )


@app.route("/criar_projeto", methods=["POST"])
def criar_projeto():
    if "username" in session:
        global diretorio_raiz
        global df_projeto

        pasta_default = r"C:\Users\lanch\Desktop\Projeto\3 - Caique"
        nome_projeto_inicial = request.form["nome_projeto"]
        abreviacao_empresa = request.form["abreviacao_empresa"]
        descricao_projeto = request.form["descricao_projeto"]

        projetos = os.listdir(diretorio_raiz)
        maior_numero = 0
        for projeto in projetos:
            numero = re.search(r"^(\d+) -", projeto)
            if numero:
                numero_int = int(numero.group(1))
                if numero_int > maior_numero:
                    maior_numero = numero_int
        numero_projeto = maior_numero + 1
        nome_projeto = str(numero_projeto) + " - " + nome_projeto_inicial

        pasta_atualizada = os.path.join(diretorio_raiz, nome_projeto)

        # adicionar o nome do projeto, a abreviacao e a descricao do projeto

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO dados_projeto (projeto, abreviacao, descricao) VALUES (?, ?, ?)",
            (nome_projeto, abreviacao_empresa, descricao_projeto),
        )
        conn.commit()
        conn.close()

        shutil.copytree(pasta_default, pasta_atualizada)
        return redirect(
            url_for(
                "projetos",
            )
        )


# ----------------------------- REVISAO ---------------------------------------------------


@app.route("/revisao", methods=["GET", "POST"])
def upload_files():
    if "username" in session:
        global diretorio_raiz

        projeto = request.form["projeto"]

        conn = sqlite3.connect("database.db")
        query = "SELECT * FROM arquivos"
        df_renomear = pd.read_sql_query(query, conn)
        conn.close()

        caminho_projeto = df_renomear.iloc[0]["caminho"]

        projeto_arquivo = re.search(r"\d...([A-Za-z\s]+[\w-]+)", caminho_projeto)
        projeto_arquivo = projeto_arquivo.group(0)

        pasta_revisao = os.path.join(
            diretorio_raiz, projeto_arquivo, "Arquivos do Projeto", "Para Revisao"
        )

        files = request.files.getlist("files[]")
        for file in files:
            filename = file.filename
            file.save(os.path.join(pasta_revisao, filename))

        # Guardar novamente na tabela SQL com caminho correto

        return redirect(
            url_for(
                "user_projetos",
                projeto=projeto,
            )
        )


# --------------------------------------------------------------------------------


@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    # Lógica para lidar com o formulário de configurações (atualização de diretórios, usuários, etc.)
    if request.method == "POST":
        # Processar os dados enviados pelo formulário e atualizar as configurações
        # Exemplo: atualizar diretórios ou adicionar/remover usuários
        print("0")

    # Renderizar o template da página de configurações
    return render_template("configuracoes.html")


# --------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
