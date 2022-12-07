import streamlit as st
import pandas as pd
from scipy.stats import poisson
import numpy as np

st.title('Minha IA que prevê jogos da copa do Catar 2022!')

#importando arquivo csv
selecoes = pd.read_excel('DadosCopaDoMundoQatar2022.xlsx', sheet_name = 'selecoes', index_col=0)
# simular uma partida | cada vez q roda gera valores que sao o numero de gols |  size == len 
# np.random.poisson(lam=m,size=1)
# m == media de gols
# para encontrar essa media vamos precisar da coluna pontos ranking da fifa
fifa = selecoes['PontosRankingFIFA']
# usar esse ranking para medir força, mas faremos q a ultima selecao tenha de 6 a 7 vezes menos força do q a primeira, entao utilizaremos:
# a é a ultima selecao do ranking e b é a primeira
a, b = min(fifa), max(fifa)
#parametro fixos de força a e força b
fa, fb = 0.15 , 1
# usando transformação linear de escala numérica - gráfico uma reta (equação do primeiro grau)
b1 = (fb - fa) / (b - a)
b0 = fb - b * b1
forca = b0 + b1 * fifa
# print(selecoes)

# função para calcular as medias (l1 e l2)
def MediaPoisson(selecao1, selecao2):
  forca1 = forca[selecao1]
  forca2 = forca[selecao2]
  mgols = 2.75
  l1 = (mgols * forca1) / (forca1 + forca2)
  l2 = mgols - l1
  return l1, l2

# função resultado para dizer Vitoria, Empate, Derrota a partir do numero de gols
def Resultado(gols1, gols2):
  if gols1 > gols2:
    resultado = 'V'
  elif gols1 < gols2:
    resultado = 'D'
  else:
    resultado = 'E'
  return resultado

# função que calcula os pontos de cada equipe
def Pontos(gols1, gols2):
  resultado = Resultado(gols1, gols2)
  if resultado == 'V':
    pontos1, pontos2 = 3, 0
  elif resultado == 'D':
    pontos1, pontos2 = 0, 3
  else:
    pontos1, pontos2 = 1, 1
  return pontos1, pontos2, resultado

# retorna tudo o que o jogo gera: saldo, numero de gols, pontos de ganha ou empata, placar
def Jogo(selecao1, selecao2):
  l1, l2 = MediaPoisson(selecao1, selecao2) 
  gols1 = int(np.random.poisson(lam=l1,size=1))
  gols2 = int(np.random.poisson(lam=l2,size=1))
  saldo1 = gols1 - gols2
  saldo2 = - saldo1
  pontos1, pontos2, resultado = Pontos(gols1, gols2)
  placar = f'{gols1}X{gols2}'
  return [gols1, gols2, saldo1, saldo2, pontos1, pontos2, resultado, placar]
  #return f'Placar: {placar} | {selecao1}: Resultado: {resultado}, Gols: {gols1}, Saldo: {saldo1}, Pontuação: {pontos1} | {selecao2}: Gols: {gols2}, Saldo: {saldo2}, Pontuação: {pontos2}'

# essa funcao mede a probabilidade de um time marcar gols de acordo com a media | a media == 3: maiores chances de fazer 1, 2 ,3, 4 gols
def Distribuicao(media):
  probs = []
  for i in range(7):
    probs.append(poisson.pmf(i, media))
  probs.append(1 - sum(probs))
  return probs

def ProbabilidadesPartidas(selecao1, selecao2):
  l1, l2 = MediaPoisson(selecao1, selecao2)
  d1, d2 = Distribuicao(l1), Distribuicao(l2)
  matriz = np.outer(d1, d2)
  vitoria = np.tril(matriz).sum() - np.trace(matriz)
  derrota = np.triu(matriz).sum() - np.trace(matriz)
  empate = 1 - (vitoria + derrota)
  probs = np.around([vitoria, empate, derrota], 3)
  probsp = [f'{100*i:.1f}%' for i in probs]
  nomes = ['0', '1', '2', '3', '4', '5', '6', '7+']
  matriz = pd.DataFrame(matriz, columns = nomes, index = nomes)
  matriz.index = pd.MultiIndex.from_product([[selecao1], matriz.index])
  matriz.columns = pd.MultiIndex.from_product([[selecao2], matriz.columns])

  output = {'Seleção 1': selecao1, 'Seleção 2': selecao2,
            'Força 1': forca[selecao1], 'Força 2': forca[selecao2],
            'Média 1': l1, 'Média 2': l2,
            'Probabilidades': probsp, 'Matriz': matriz}
  return output

# app começa agora
listaselecoes1 = selecoes.index.tolist()
listaselecoes1.sort()
listaselecoes2 = listaselecoes1.copy()

#colocando so botoes
j1, j2 = st.columns(2)
selecao1 = j1.selectbox('Escolha a primeira Seleção', listaselecoes1)
listaselecoes2.remove(selecao1)
selecao2 = j2.selectbox('Escola a segunda Seleção', listaselecoes2, index=1)
st.markdown('-----')

jogo = ProbabilidadesPartidas(selecao1, selecao2)
prob = jogo['Probabilidades']
matriz = jogo['Matriz']

# metric coloca informações de dashboard
col1, col2, col3, col4, col5 = st.columns(5)
col1.image(selecoes.loc[selecao1, 'LinkBandeiraGrande'])
col2.metric(selecao1, prob[0])
col3.metric('Empate', prob[1])
col4.metric(selecao2, prob[2])
col5.image(selecoes.loc[selecao2, 'LinkBandeiraGrande'])

st.markdown('----')
st.markdown('## Probabilidades dos Placares')

# essa função mostra os resultados da tabela em %
def aux(x):
    return f'{str(round(100*x,1))}%'

st.table(matriz.applymap(aux))

# Probabilidade de todos os jogos da copa
st.markdown('---')
st.markdown('## Probabilidades dos Jogos da Copa Qatar-2022')
st.markdown('*A relação vitória, Empate e Derrota é em relação a Seleção 1.')
#jogosCopa = pd.read_excel('outputEstimativaJogosCopaMundo.xlsx', index_col=0)
#st.table(jogosCopa[['grupo', 'seleção1', 'seleção2', 'Vitória', 'Empate', 'Derrota']])