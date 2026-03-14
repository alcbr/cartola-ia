import streamlit as st
import requests
import pandas as pd

st.title("IA Escalador Cartola")

# ==============================
# CAMPOS DO USUÁRIO
# ==============================

cartoletas = st.number_input(
"Quantas cartoletas você tem?",
min_value=0.0,
value=100.0,
step=1.0
)

qtd_jogadores = st.number_input(
"Quantos jogadores mostrar no ranking?",
min_value=5,
max_value=100,
value=20,
step=1
)

# ==============================
# BUSCAR DADOS DA API
# ==============================

url = "https://api.cartola.globo.com/atletas/mercado"

data = requests.get(url).json()

players = pd.DataFrame(data["atletas"])

# ==============================
# CRIAR PREVISÃO SIMPLES
# ==============================

players["previsao"] = (
players["media_num"] * 0.7 +
players["jogos_num"] * 0.3
)

# ==============================
# RANKING
# ==============================

st.subheader("Ranking de jogadores")

top = players.sort_values("previsao", ascending=False)

st.dataframe(
top[
[
"apelido",
"preco_num",
"media_num",
"previsao"
]
].head(int(qtd_jogadores))
)

# ==============================
# GERAR TIME
# ==============================

if st.button("Gerar melhor time da rodada"):

    jogadores_ordenados = players.sort_values("previsao", ascending=False)

    time = []
    preco_total = 0

    for index, jogador in jogadores_ordenados.iterrows():

        preco = jogador["preco_num"]

        if preco_total + preco <= cartoletas:

            time.append(jogador)
            preco_total += preco

        if len(time) == 11:
            break

    time_df = pd.DataFrame(time)

    st.subheader("Time sugerido")

    st.dataframe(
    time_df[
    [
    "apelido",
    "preco_num",
    "media_num",
    "previsao"
    ]
    ])

    st.write("Custo total do time:", round(preco_total,2))
