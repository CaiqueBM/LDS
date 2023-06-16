    clc
clear
N = 1;
potenciaAtiva = (200+(20*N))*10^3; %kW
fp = 0.95;
comprimento = 280+(20*N); %km
frequencia = 60; %Hz
temperaturaDoCondutor = 45+N; %�C
TemperaturaAmbiente = 25; %�C
PressaoAtmosferica = 76; %cmHg
percentualDeCargaLeve = 0.1; %
regVmax = 10; %
perdaMaxCorona = 10; %kW/km
rendimentoMin = 92; %

E0 = 8.854187817*10^-12;
w = 2*pi*frequencia;
theta = -acos(fp); %c�
resultado = 0;


    tensaoOtima = 5.5*sqrt(0.62*comprimento+(potenciaAtiva*1.2/100))    % kV

    tensaoOtima = 345;  % kV
        
    correnteLinha =  (1.2*potenciaAtiva)/(fp*sqrt(3)*tensaoOtima)*(fp+1i*sin(theta));%amperes
    
    [numData, txtData] = xlsread('cabosACSR-2.xlsx');%tabela dados dos cabos
    
    %Determinando parametros do condutor a partir da tabela de cabos de aluminio 
    for g = 46:-1:1
      if resultado==0  
        diametroExt = numData(g,3); %Diametro externo em mm
        secNom = numData(g,2);%Se��o Nominal mm�
        nomeCond = txtData(g,1);
        capCorrente = numData(g,11); %Capacidade de corrente em amperes
        resistencia60Hz = numData(g,10); %resistencia eletrica ca a 50�C 
        raioMedioGeometrico = numData(g,4); %
        if resultado==0 
        for c = 1:4
  
            if ((correnteLinha/c)<= capCorrente)
                for k = 1:2
                  if resultado==0

                    quantSubCondutores = c;
                    
                    if (quantSubCondutores == 1);
                               distSubcondutores = 0;
                                    else distSubcondutores = (35+5*(c+k-3))*(10^-2); 
                    end
                    
                    raio = diametroExt/2;

                    distHorizontal1 = 0.22 + 0.01*tensaoOtima;
                    distHorizontal2 = 0.37*sqrt(frequencia) + 0.0076*tensaoOtima;
                    if(distHorizontal1 > distHorizontal2)
                        distHorizontal = distHorizontal1;
                    else
                        distHorizontal = distHorizontal2;   
                    end
                  
                    DMG = (distHorizontal*distHorizontal*2*distHorizontal)^(1/3);
                        switch quantSubCondutores
                            case 1
                                r1 = raioMedioGeometrico;
                                RMG = raio;
                                tipoDeDisposicaoDosCondutores = '1 por fase';
                            case 2
                                r1 = (raioMedioGeometrico*distSubcondutores)^(1/2);
                                RMG = (raio*distSubcondutores)^(1/2);
                                tipoDeDisposicaoDosCondutores = '2 em feixe';
                            case 3
                                r1 = (raioMedioGeometrico*distSubcondutores^2)^(1/3);
                                RMG = (raio*distSubcondutores^2)^(1/3);
                                tipoDeDisposicaoDosCondutores = '3 em triangulo';
                            case 4
                                r1 = 1.09*(raioMedioGeometrico*distSubcondutores^3)^(1/4);
                                RMG = 1.09*(raio*distSubcondutores^3)^(1/4);
                                tipoDeDisposicaoDosCondutores = '4 em quadrado';
                        end

                    R = resistencia60Hz*(228 + temperaturaDoCondutor)/(228 + 50);
                    L = 2*10^-7*log(DMG/r1);
                    C = 2*pi*E0/(log(DMG/RMG));
                    
                           if (quantSubCondutores == 1);
                               distVertical = 0;
                                    else distVertical = 0.5 + 0.01*tensaoOtima; 
                           end
                    

                    XC = w*C*(10^3);           %ohms/km capacitancia
                    YSH = XC*1i;                  %ohms/km Admit�ncia Shunt

                    XL = w*L*(10^3)*1i;           %ohms/km  indutivancia
                    Req = R/quantSubCondutores;   %ohms/km resistencia equivalente
                    Zs = (Req + XL);             %ohms/km Imped�ncia

                    Zc = sqrt(Zs/YSH);
                    gama = sqrt(Zs*YSH);

                    A = cosh(gama*comprimento);
                    B = Zc*(sinh(gama*comprimento));
                    C = (1/Zc)*sinh(gama*comprimento);
                    D = A;
                    
                    
                    Ir = correnteLinha/sqrt(3);
                    Vr = (tensaoOtima/sqrt(3))*10^3;            %[V] tens�o carga 
                    VsPesada = A*Vr + B*Ir;
                    IsPesada = C*Vr + D*Ir;
                    VsLeve = A*Vr + B*Ir*percentualDeCargaLeve;
                    IsLeve = C*Vr + D*Ir*percentualDeCargaLeve;
                    
                    regTensao = abs((abs(VsLeve)-abs(VsPesada))/abs(VsPesada))*100;
                                            

                    
                    deltinha = (3.9211*PressaoAtmosferica)/(273 + TemperaturaAmbiente);
                    raioExt = diametroExt/(2*10);
                    Vo = 21.1*deltinha*raioExt*1*log((distHorizontal*100)/raioExt);
                    perdaCorona = (241/deltinha)*(frequencia+25)*sqrt(raioExt/(distHorizontal*100))*(((tensaoOtima/sqrt(3)) - Vo)^2)*10^-5;
                    perdaJoule = R*comprimento*(correnteLinha^2)*10^-3;
                    
                                        
                    rendimento = (potenciaAtiva)/((potenciaAtiva)+abs(perdaJoule)+perdaCorona*comprimento)*100;
                    
                    if (perdaCorona<=perdaMaxCorona)
                        if (regTensao<=regVmax)
                            if(rendimento>=rendimentoMin)
                                resultado=1;
                            end
                        end
                     end
                  end
               end
            end
          end
        end
      end
    end
    
%fprintf('\n\nValores de tens�o, corrente e pot�ncia para �ngulo de disparo de %d�.', ang_disp)

    fprintf('\nTens�o nominal em KV:  %3.2f\n\n', tensaoOtima);
    
    fprintf('Corrente de Linha:  %3.2f\n\n', abs(correnteLinha));
    
    fprintf('Tipo de disposicao dos condutores:  '), disp(tipoDeDisposicaoDosCondutores);
    
    fprintf('\nDist�ncia horizontal entre as fases (m):  %3.2f\n\n', distHorizontal);

    fprintf('Dist�ncia vertical entre as fases (m):  %3.2f\n\n', distVertical);    

    fprintf('Condutor utilizado:'), disp(nomeCond);

    fprintf('Capacidade de Corrente do condutor escolhido:  %3.2f\n\n', capCorrente);

    fprintf('Quantidade de condutores por fase:  %3.0f\n\n', quantSubCondutores);

    fprintf('Dist�ncia entre subcondutores (m):  %3.2f\n\n', distSubcondutores);

    fprintf('Regula��o de tens�o (%):  %3.2f\n\n', regTensao);

    fprintf('Perdas por efeito corona (kW):  %3.2f\n\n', perdaCorona);

    fprintf('Rendimento:  %3.2f\n\n', rendimento);