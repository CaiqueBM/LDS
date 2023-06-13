import tkinter as tk
import pandas as pd
import math
import cmath

def verificar_campos():
    tensoes_padroes = [6, 11.4, 34.5, 69, 88, 138, 230, 345, 440, 500, 600, 750, 1100]
    data_frame = pd.read_csv('cabos.csv')
    temp = 228
    condicao = False

    potencia_ativa = float(potencia_ativa_entry.get())
    fator_potencia = float(fator_potencia_entry.get())
    comprimento_linha = float(comprimento_entry.get())
    previsao_futura = float(previsao_aumento_carga_entry.get())
    T_aux = float(temperatura_operacao_entry.get())
   
    # Neste exemplo, vamos verificar se o campo "nome" e o campo "idade" estão preenchidos
    if potencia_ativa_entry.get() != "" and fator_potencia_entry.get() != "" and comprimento_entry.get() != "" and frequencia_entry.get() != "" and temperatura_operacao_entry.get() != "" and temperatura_ambiente_entry.get() != "" and pressao_atm_entry.get() != "" and percentual_carga_leve_entry.get() != "" and regulacao_maxima_entry.get() != "" and perda_efeito_corona_entry.get() != "" and rendimento_minimo_entry.get() != "" and previsao_aumento_carga_entry.get() != "":
        
        # Calculo da tensao otima
        potencia_corrigida = potencia_ativa * (1 + previsao_futura)
        tensao_otima = 5.5 * math.sqrt((0.62 * comprimento_linha) + (potencia_corrigida/100))
        # Escolher a tensao otima padrao
        tensao_otima = min(tensoes_padroes, key=lambda x: abs(x - tensao_otima))

        # Calculo da corrente
        corrente_modulo = (potencia_corrigida / 1000)/((math.sqrt(3)) * tensao_otima * fator_potencia)
        corrente_modulo = round(corrente_modulo, 3)
        corrente_angulo = - math.acos(fator_potencia)
        corrente_rect = cmath.rect(corrente_modulo, corrente_angulo)
        corrente_polar = cmath.polar(corrente_rect)

        # Escolha da bitola do condutor e buscando informaçoes do cabo
        for index, row in data_frame.iterrows():
            if condicao == False:
                corrente_max = row.iloc[12]
                nome_cabo = row.iloc[0]
                bitola = row.iloc[3]
                resistencia = row.iloc[3]
            
                for i in range(4):
                    if ((corrente_polar/i)<= corrente_max):
                        for k in range(1,2):
                            if condicao==False:
                                quantSubCondutores = i
                                if (quantSubCondutores == 1):
                                    distSubcondutores = 0
                                else:
                                    distSubcondutores = (35+5*(i+k-3))*(10^-2)
                            raio = diametroExt/2
                            distHorizontal1 = 0.22 + 0.01 * tensao_otima
                            distHorizontal2 = 0.37 * math.sqrt(frequencia) + 0.0076 * tensao_otima
                            if distHorizontal1 > distHorizontal2:
                                distHorizontal = distHorizontal1
                            else:
                                distHorizontal = distHorizontal2
                            
                            DMG = (distHorizontal*distHorizontal*2*distHorizontal)^(1/3)
                            
                            if quantSubCondutores == 1:
                                r1 = raioMedioGeometrico
                                RMG = raio
                                tipoDeDisposicaoDosCondutores = '1 por fase'
                            elif quantSubCondutores == 2:
                                r1 = (raioMedioGeometrico*distSubcondutores)^(1/2)
                                RMG = (raio*distSubcondutores)^(1/2)
                                tipoDeDisposicaoDosCondutores = '2 em feixe'
                            elif quantSubCondutores == 3:
                                r1 = (raioMedioGeometrico*distSubcondutores^2)^(1/3)
                                RMG = (raio*distSubcondutores^2)^(1/3)
                                tipoDeDisposicaoDosCondutores = '3 em triangulo'
                            elif quantSubCondutores == 4:
                                r1 = 1.09*(raioMedioGeometrico*distSubcondutores^3)^(1/4)
                                RMG = 1.09*(raio*distSubcondutores^3)^(1/4)
                                tipoDeDisposicaoDosCondutores = '4 em quadrado'

                            R = resistencia60Hz*(228 + temperaturaDoCondutor)/(228 + 50);
                            L = 2*10^-7*cmath.log(DMG/r1);
                            C = 2*cmath.pi*E0/(log(DMG/RMG));
                            if quantSubCondutores == 1:
                                distVertical = 0
                            else:
                                distVertical = 0.5 + 0.01* tensao_otima
                            
                            XC = w*C*(10^3)           #ohms/km capacitancia
                            YSH = XC*1i                  #ohms/km Admit�ncia Shunt

                            XL = w*L*(10^3)*1i           #ohms/km  indutivancia
                            Req = R/quantSubCondutores;   #ohms/km resistencia equivalente
                            Zs = (Req + XL);             #ohms/km Imped�ncia

                            Zc = sqrt(Zs/YSH)
                            gama = sqrt(Zs*YSH)

                            A = cosh(gama*comprimento)
                            B = Zc*(sinh(gama*comprimento))
                            C = (1/Zc)*sinh(gama*comprimento)
                            D = A


                            Ir = correnteLinha/sqrt(3)
                            Vr = (tensaoOtima/sqrt(3))*10^3;  #[V] tens�o carga
                            VsPesada = A*Vr + B*Ir
                            IsPesada = C*Vr + D*Ir
                            VsLeve = A*Vr + B*Ir*percentualDeCargaLeve
                            IsLeve = C*Vr + D*Ir*percentualDeCargaLeve

                            regTensao = abs((abs(VsLeve)-abs(VsPesada))/abs(VsPesada))*100



                            deltinha = (3.9211*PressaoAtmosferica)/(273 + TemperaturaAmbiente)
                            raioExt = diametroExt/(2*10)
                            Vo = 21.1*deltinha*raioExt*1*log((distHorizontal*100)/raioExt)
                            perdaCorona = (241/deltinha)*(frequencia+25)*sqrt(raioExt/(distHorizontal*100))*(((tensaoOtima/sqrt(3)) - Vo)^2)*10^-5
                            perdaJoule = R*comprimento*(correnteLinha^2)*10^-3


                            rendimento = (potenciaAtiva)/((potenciaAtiva)+abs(perdaJoule)+perdaCorona*comprimento)*100

                            if perdaCorona <= perdaMaxCorona:
                                if regTensao <= regVmax:
                                    if rendimento >= rendimentoMin:
                                        resultado=1
























            # Calculo da Resistencia Serie (Rs)
                if T_aux > 37.5:

                    T_2 = T_aux
                    T_1 = 50
                    res_1 = resistencia
                    resistencia = ((temp + T_2) * res_1) / (temp + T_1)
                
                elif T_aux <= 37.5:
                    T_2 = T_aux
                    T_1 = 25
                    res_2 = resistencia
                    resistencia = ((temp + T_1) * res_2) / (temp + T_2)
                    
            # Calculo da Indutancia Serie (Ls)
            

            # Calculo da Capacitancia Shunt (Csh)


            # Parametros ABCD


            # Calculo da Perda por Corona
                


            # Calculo da Regulaçao de tensao


            # Calculo do Rendimento


            resposta_texto = "Tensao otima: " + str(tensao_otima) + " kV" + "\n"
            resposta_texto += "Corrente: " + str(corrente_modulo) + " <" + str(corrente_angulo) + " kA" + "\n"

            resposta_label.config(text=resposta_texto)
        




# Criando a segunda janela
janela = tk.Tk()

# Criando os componentes da interface
potencia_ativa_label = tk.Label(janela, text="Potencia ativa da carga (kW):")
potencia_ativa_label.grid(row=0, column=0, sticky="w")
potencia_ativa_entry = tk.Entry(janela)
potencia_ativa_entry.grid(row=1, column=0)

fator_potencia_label = tk.Label(janela, text="Fator de potencia da carga:")
fator_potencia_label.grid(row=2, column=0, sticky="w")
fator_potencia_entry = tk.Entry(janela)
fator_potencia_entry.grid(row=3, column=0)

comprimento_label = tk.Label(janela, text="Comprimento da linha:")
comprimento_label.grid(row=4, column=0, sticky="w")
comprimento_entry = tk.Entry(janela)
comprimento_entry.grid(row=5, column=0)

frequencia_label = tk.Label(janela, text="Frequencia de operaçao:")
frequencia_label.grid(row=6, column=0, sticky="w")
frequencia_entry = tk.Entry(janela)
frequencia_entry.grid(row=7, column=0)

temperatura_operacao_label = tk.Label(janela, text="Temperatura de operaçao:")
temperatura_operacao_label.grid(row=8, column=0, sticky="w")
temperatura_operacao_entry = tk.Entry(janela)
temperatura_operacao_entry.grid(row=9, column=0)

temperatura_ambiente_label = tk.Label(janela, text="Temperatura ambiente:")
temperatura_ambiente_label.grid(row=10, column=0, sticky="w")
temperatura_ambiente_entry = tk.Entry(janela)
temperatura_ambiente_entry.grid(row=11, column=0)

pressao_atm_label = tk.Label(janela, text="Pressao atmosferica:")
pressao_atm_label.grid(row=12, column=0, sticky="w")
pressao_atm_entry = tk.Entry(janela)
pressao_atm_entry.grid(row=13, column=0)

percentual_carga_leve_label = tk.Label(janela, text="Percentual de carga leve:")
percentual_carga_leve_label.grid(row=0, column=1, sticky="w")
percentual_carga_leve_entry = tk.Entry(janela)
percentual_carga_leve_entry.grid(row=1, column=1)

regulacao_maxima_label = tk.Label(janela, text="Regulaçao de tensao maxima:")
regulacao_maxima_label.grid(row=2, column=1, sticky="w")
regulacao_maxima_entry = tk.Entry(janela)
regulacao_maxima_entry.grid(row=3, column=1)

perda_efeito_corona_label = tk.Label(janela, text="Perda por efeito corona maxima:")
perda_efeito_corona_label.grid(row=4, column=1, sticky="w")
perda_efeito_corona_entry = tk.Entry(janela)
perda_efeito_corona_entry.grid(row=5, column=1)

rendimento_minimo_label = tk.Label(janela, text="Rendimento minimo:")
rendimento_minimo_label.grid(row=6, column=1, sticky="w")
rendimento_minimo_entry = tk.Entry(janela)
rendimento_minimo_entry.grid(row=7, column=1)

previsao_aumento_carga_label = tk.Label(janela, text="Previsao aumento de carga:")
previsao_aumento_carga_label.grid(row=8, column=1, sticky="w")
previsao_aumento_carga_entry = tk.Entry(janela)
previsao_aumento_carga_entry.grid(row=9, column=1)

distancia_fases_label = tk.Label(janela, text="Distancia entre fases:")
distancia_fases_label.grid(row=10, column=1, sticky="w")
distancia_fases_entry = tk.Entry(janela)
distancia_fases_entry.grid(row=11, column=1)


verificar_button = tk.Button(janela, text="Verificar", command=verificar_campos)
verificar_button.grid(row=17, column=0, columnspan=2)

resposta_label = tk.Label(janela, text="")
resposta_label.grid(row=18, column=0, columnspan=2)




    # Iniciando o loop principal da janela
janela.mainloop()
