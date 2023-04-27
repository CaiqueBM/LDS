import os
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


diretorio = r"C:\\Users\\lanch\\Desktop\\Projeto"


class MyForm(FlaskForm):
    file_choices = [
        (filename, filename)
        for filename in os.listdir("diretorio")
        if os.path.isfile(os.path.join("diretorio", filename))
    ]
    my_list = SelectField(
        "Novo Documento", choices=file_choices, validators=[DataRequired()]
    )
    new_file_name = StringField("Nome do Novo Arquivo", validators=[DataRequired()])


# --------------------------------------------------------------------------------
