@app.route("/atualizar_responsavel", methods=["POST"])
def atualizar_responsavel():
    if "username" in session:
        username = session["username"]
        projeto = request.form["projeto"]
        atualizar_responsavel = request.form.get("mudar_responsavel", None)
        linha_selecionada = request.form.getlist("selecionados")
        linha_selecionada = list(map(int, linha_selecionada))
        tamanho_lista = len(linha_selecionada)

        conn = sqlite3.connect("database.db")
        query = "SELECT * FROM arquivos"
        df_tabela = pd.read_sql_query(query, conn)
        df_selecionado = df_tabela.loc[df_tabela["id"].isin(linha_selecionada)]
        status_atual = df_selecionado["status"].values.tolist()
        id_documentos = df_selecionado["id"].values.tolist()
        caminho_projeto = df_selecionado["caminho"].values.tolist()
        conn.close()

        if tamanho_lista <= 0:
            return redirect(
                url_for(
                    "documentos",
                    projeto=projeto,
                    atualizar=atualizar,
                    df_selecionado=df_selecionado,
                )
            )
        else:

            partes = nome_arquivo.split("-", 4)
            padrao = "-".join(partes[:4])

            result_teste = df_teste[df_teste["nome"].str.contains(padrao, regex=False)]

            # result_teste = df_teste[df_teste["projeto"] == projeto_recebido]


            parte = nome.split("_")
            numero_parte = parte[0]

            partes = numero_parte.split("-")
            sequencial = partes[4]
            # sequencial = numero_parte.split("_")[0]
            sequenciais.append(sequencial)


            caminho_origem = os.path.join(diretorio_default, arquivo_existente)



            for i in range(tamanho_lista):
                nome_do_arquivo = os.path.basename(caminho_projeto[i])
                if status_atual[i] == "Criado" or status_atual[i] == "Em Desenvolvimento":
                
                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                query = f"""UPDATE arquivos SET responsavel = '{username}', caminho = '{caminho}' WHERE id = '{id_documentos[i]}' """
                c.execute(query)
                conn.commit()


                else:
                    

                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                query = f"""UPDATE arquivos SET responsavel = '{username}' WHERE id = '{id_documentos[i]}' """
                c.execute(query)
                conn.commit()

                responsavel_status = status_atual[0]

                return redirect(
                    url_for(
                        "documentos",
                        projeto=projeto,
                        responsavel_status=responsavel_status,
                        atualizar=atualizar,
                        df_selecionado=df_selecionado,
                    )
                )
