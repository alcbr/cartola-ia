import streamlit as st
import requests
import pandas as pd

# Configuração de Página Premium
st.set_page_config(page_title="IA Cartola Chapa Man (teste)", page_icon="⚽", layout="wide")

# Interface Customizada (Tema Dark)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { background-color: #1e2130; color: white; border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { background-color: #00ff00 !important; color: black !important; font-weight: bold; }
    .stButton>button {
        width: 100%; background: linear-gradient(90deg, #00ff00 0%, #00cc00 100%);
        color: black !important; font-weight: bold; border-radius: 8px; border: none; padding: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300)
def carregar_dados():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        url_m = "https://api.cartola.globo.com/atletas/mercado"
        res = requests.get(url_m, headers=headers, timeout=15).json()
        df = pd.DataFrame(res["atletas"])
        clubes = res["clubes"]
        posicoes = res["posicoes"]
        
        df["clube_nome"] = df["clube_id"].astype(str).apply(lambda x: clubes[x]["nome"] if x in clubes else "N/A")
        df["pos_abrev"] = df["posicao_id"].apply(lambda x: posicoes[str(x)]["abreviacao"].upper())
        
        url_p = "https://api.cartola.globo.com/partidas"
        partidas = requests.get(url_p, headers=headers, timeout=15).json().get("partidas", [])
        return df, partidas
    except:
        return pd.DataFrame(), []

st.title("🛡️ IA Cartola Chapa Man (teste)")
st.markdown("### Inteligência de Dados para Escalação")

df_base, partidas = carregar_dados()

if df_base.empty:
    st.error("Erro na conexão com a API do Cartola. Tente novamente em instantes.")
    st.stop()

# --- CÁLCULOS ESTATÍSTICOS ---
times_casa = [p["clube_casa_id"] for p in partidas]
df_base["mando"] = df_base["clube_id"].apply(lambda x: 1.5 if x in times_casa else 0)
df_base["previsao"] = (df_base["media_num"] * 0.8) + df_base["mando"]
df_base["custo_beneficio"] = df_base["previsao"] / (df_base["preco_num"] + 0.1)

# Filtro de Prováveis com Fallback
df_f = df_base[df_base["status_id"] == 7].copy()
if len(df_f) < 15: 
    df_f = df_base.copy()

# Sidebar de Configurações
with st.sidebar:
    st.header("⚙️ Parâmetros")
    orcamento = st.number_input("Cartoletas Disponíveis", value=140.0, min_value=40.0)
    formacao = st.selectbox("Escolha a Formação", ["4-3-3", "3-4-3", "3-5-2", "4-4-2"])
    estrat = st.radio("Estratégia da IA", ["Elite", "Custo-Benefício", "Surpresas"])

# MAPEAMENTO TÁTICO
esquemas = {
    "4-3-3": {"GOL": 1, "LAT": 2, "ZAG": 2, "MEI": 3, "ATA": 3, "TEC": 1},
    "3-4-3": {"GOL": 1, "ZAG": 3, "MEI": 4, "ATA": 3, "TEC": 1},
    "3-5-2": {"GOL": 1, "ZAG": 3, "MEI": 5, "ATA": 2, "TEC": 1},
    "4-4-2": {"GOL": 1, "LAT": 2, "ZAG": 2, "MEI": 4, "ATA": 2, "TEC": 1}
}

# ORDEM DE EXIBIÇÃO
ORDEM_VISUAL = {"GOL": 0, "LAT": 1, "ZAG": 2, "MEI": 3, "ATA": 4, "TEC": 5}

def montar_time():
    lista_vagas = []
    config = esquemas[formacao]
    
    for pos, qtd in config.items():
        pool = df_f[df_f["pos_abrev"] == pos]
        if pool.empty: 
            pool = df_base[df_base["pos_abrev"] == pos]
        
        if estrat == "Elite": 
            pool = pool.sort_values("previsao", ascending=False)
        elif estrat == "Custo-Benefício": 
            pool = pool.sort_values("custo_beneficio", ascending=False)
        else: 
            pool = pool.sort_values("preco_num", ascending=True)
        
        lista_vagas.append(pool.head(qtd))

    time_df = pd.concat(lista_vagas).reset_index(drop=True)
    
    # Ajuste de Orçamento
    tentativas = 0
    while time_df["preco_num"].sum() > orcamento and tentativas < 60:
        time_df = time_df.sort_values("preco_num", ascending=False)
        for i in range(len(time_df)):
            atleta = time_df.iloc[i]
            reserva = df_f[(df_f["pos_abrev"] == atleta["pos_abrev"]) & 
                          (~df_f["atleta_id"].isin(time_df["atleta_id"])) & 
                          (df_f["preco_num"] < atleta["preco_num"])].sort_values("preco_num", ascending=True).head(1)
            
            if not reserva.empty:
                time_df.iloc[i] = reserva.iloc[0]
                break
        tentativas += 1
    
    # Aplica a Ordem de Visualização
    time_df["ordem_sort"] = time_df["pos_abrev"].map(ORDEM_VISUAL)
    time_df = time_df.sort_values("ordem_sort").drop(columns=["ordem_sort"])
    
    return time_df

# --- EXECUÇÃO ---
if st.button("⚡ ESCALAR TIME AGORA"):
    final_df = montar_time()
    
    if not final_df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Custo Total", f"C$ {final_df['preco_num'].sum():.2f}")
        c2.metric("Potencial", f"{final_df['previsao'].sum():.2f} pts")
        
        cap_name = final_df.sort_values("previsao", ascending=False).iloc[0]["apelido"]
        c3.metric("Capitão Sugerido", cap_name)
        
        st.dataframe(final_df[["pos_abrev", "apelido", "clube_nome", "preco_num", "media_num", "previsao"]], 
                     use_container_width=True, hide_index=True)
    else:
        st.error("Erro ao gerar escalação.")

st.divider()

# --- RADAR DE ATLETAS ---
st.subheader("🔍 Radar de Atletas (Ranking)")
tabs = st.tabs(["🧤 Goleiros", "🛡️ Zagueiros", "🏃 Laterais", "🧠 Meias", "⚽ Atacantes"])

def gerar_ranking(pos_ref):
    pool = df_f[df_f["pos_abrev"] == pos_ref]
    if pool.empty: 
        pool = df_base[df_base["pos_abrev"] == pos_ref]
    return pool.sort_values("previsao", ascending=False)[["apelido", "clube_nome", "previsao"]].head(10)

with tabs[0]: st.table(gerar_ranking("GOL"))
with tabs[1]: st.table(gerar_ranking("ZAG"))
with tabs[2]: st.table(gerar_ranking("LAT"))
with tabs[3]: st.table(gerar_ranking("MEI"))
with tabs[4]: st.table(gerar_ranking("ATA"))
