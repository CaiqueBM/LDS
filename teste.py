import xlwings as xw


caminho_ld_padrao = r"C:\Users\lanch\Desktop\modeloGRD\ABS-AEX-LD-001_R06.xlsx"
caminho_grd_padrao = r"C:\Users\lanch\Desktop\modeloGRD\GRD-ABS-AEX-07.xlsx"

# Abrir o arquivo Excel
app = xw.App(visible=False)
workbook = app.books.open(caminho_ld_padrao)

# Obter a planilha desejada
planilha = workbook.sheets["F. Rosto"]

# Ler os valores das células
for row in planilha.range("A1:N20").value:
    for cell in row:
        print(cell)
        # shape = planilha.shapes[0]
        shape = planilha.shapes["nomeempresa"]  # Nome da forma
        if shape.text == "nome_empresa":
            shape.text = str("teste")
        if cell == "empresa":
            planilha.api.Names.Add(Name="NomeCelula", RefersTo="='F. Rosto'!$J$1")


workbook.save()

# Fechar o arquivo Excel
workbook.close()
app.quit()
