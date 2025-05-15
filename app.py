import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Visualização de Mapas com População",
    page_icon="🌍",
    layout="wide"
)

# Título da aplicação
st.title("Visualização Interativa de Mapas do Brasil com Dados de População")

# Sidebar
st.sidebar.title("🗺️ Mapas em Streamlit")
st.sidebar.write("Personalize a visualização do mapa com as opções abaixo.")

# --- Dados ---
@st.cache_data
def load_data():
    municipios = pd.read_csv("dados_municipais.csv")
    return municipios

df_merged = load_data()

# Criar DataFrame de estados
estados = df_merged[['estado']].drop_duplicates().rename(columns={'estado': 'nome'})


# --- Filtros ---
st.sidebar.subheader("Filtros Geográficos")

# Selecionar o tipo de mapa
map_option = st.sidebar.selectbox(
    "Opção de Mapa:",
    ("Streamlit - Nativo", "Plotly Express - Marcadores", "Plotly Express - Mapa de Calor", "Plotly Express - Tamanho da População"),
    help="Selecione o motor de renderização do mapa"
)

# Filtrar por estado (Removido quando o mapa é Nativo)
if map_option != "Streamlit - Nativo":
    filtrar_por_estado = st.sidebar.checkbox("Filtrar por Estado", value=False)
    if filtrar_por_estado:
        estado_selecionado = st.sidebar.selectbox(
            "Selecione o estado:",
            ["Todos os Estados"] + list(estados['nome'].unique())
        )
        df_estado = df_merged[df_merged['estado'] == estado_selecionado].copy()
    else:
        estado_selecionado = "Todos os Estados"
        df_estado = df_merged.copy()
else:
    df_estado = df_merged.copy()

# Filtrar por região
regioes_brasil = df_estado['regiao'].unique()
filtrar_por_regiao = st.sidebar.checkbox("Filtrar por Região", value=False)
if filtrar_por_regiao:
    regiao_selecionada = st.sidebar.multiselect("Selecione a(s) região(ões):", regioes_brasil)
    df_filtered_regiao = df_estado[df_estado['regiao'].isin(regiao_selecionada)].copy()
else:
    df_filtered_regiao = df_estado.copy()

# Filtrar por UF
ufs_brasil = df_filtered_regiao['uf'].unique()
filtrar_por_uf = st.sidebar.checkbox("Filtrar por Unidade Federativa (UF)", value=False)
if filtrar_por_uf:
    uf_selecionada = st.sidebar.multiselect("Selecione a(s) UF(s):", ufs_brasil)
    df_final = df_filtered_regiao[df_filtered_regiao['uf'].isin(uf_selecionada)].copy()
else:
    df_final = df_filtered_regiao.copy()



# --- Opções de Personalização (Plotly Express) ---
if map_option.startswith("Plotly Express"):
    st.sidebar.subheader("Personalização do Mapa")

    # Escolha do estilo do mapa base
    map_style = st.sidebar.selectbox(
        "Estilo do Mapa Base:",
        ["open-street-map", "carto-positron", "carto-darkmatter"],
        index=0
    )

    # Ajuste do zoom inicial
    default_zoom = 3 if estado_selecionado == 'Todos os Estados' else 5
    initial_zoom = st.sidebar.slider("Zoom Inicial:", 1, 15, default_zoom)

    # Altura do mapa
    map_height = st.sidebar.slider("Altura do Mapa (pixels):", 400, 1000, 600)

    # Opções específicas para o mapa de marcadores
    if map_option == "Plotly Express - Marcadores":
        colorir_por_uf = st.sidebar.checkbox("Colorir municípios por UF", value=False)
        color_column = 'uf' if colorir_por_uf else None
    else:
        color_column = None

    # Opções específicas para o mapa de tamanho da população
    if map_option == "Plotly Express - Tamanho da População":
        tamanho_pop = st.sidebar.checkbox("Mostrar tamanho do marcador pela população", value=True)
        max_tamanho_marcador = st.sidebar.slider("Tamanho máximo do marcador:", 5, 50, 20)
    else:
        tamanho_pop = False
        max_tamanho_marcador = 20


# --- Exibição do Mapa ---
st.subheader(f"Mapa {map_option.split(' - ')[-1] if ' - ' in map_option else map_option}")

config = {'scrollZoom': True}

def plot_map(df, map_type, style, zoom, height, color=None, size=None, size_max=20):
    """Função para plotar o mapa com base nos parâmetros fornecidos."""
    if map_type == "Plotly Express - Marcadores":
        st.write("Este mapa utiliza marcadores para representar a localização dos municípios. Passe o mouse para detalhes.")
        fig = px.scatter_mapbox(
            df,
            lat="latitude",
            lon="longitude",
            hover_name="municipio",
            hover_data=["estado", "uf", "regiao", "pop_21"],
            color=color,
            zoom=zoom,
            height=height
        )
        fig.update_layout(mapbox_style=style, dragmode='zoom', showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, config=config, use_container_width=True)

    elif map_type == "Plotly Express - Mapa de Calor":
        st.write("Este mapa de calor mostra a densidade de municípios. Cores intensas indicam maior concentração.")
        fig = px.density_mapbox(
            df,
            lat="latitude",
            lon="longitude",
            z=df.index,
            radius=10,
            center=go.layout.mapbox.Center(
                lat=df['latitude'].mean(),
                lon=df['longitude'].mean()
            ),
            zoom=zoom,
            mapbox_style=style,
            height=height
        )
        st.plotly_chart(fig, config=config, use_container_width=True)

    elif map_type == "Plotly Express - Tamanho da População":
        st.write("Este mapa exibe marcadores onde o tamanho é proporcional à população do município em 2021.")
        if size:
            fig = px.scatter_mapbox(
                df,
                lat="latitude",
                lon="longitude",
                hover_name="municipio",
                hover_data=["estado", "uf", "regiao", "pop_21"],
                size=size,
                size_max=size_max,
                zoom=zoom,
                height=height
            )
            fig.update_layout(mapbox_style=style, dragmode='zoom', showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, config=config, use_container_width=True)
        else:
            st.info("Selecione a opção 'Mostrar tamanho do marcador pela população' na barra lateral.")

    elif map_type == "Streamlit - Nativo":
        st.write("Mapa interativo básico do Streamlit para exibir pontos geográficos.")
        if not df.empty:
            st.map(df[['latitude', 'longitude']], height=600, use_container_width=True)
        else:
            st.warning("Não há dados para exibir com os filtros selecionados.")


with st.expander("Visualizar Dados Filtrados"):
    st.dataframe(df_final)

with st.expander("Visualizar Dados Brutos"):
    st.dataframe(df_merged)



# --- Rodapé ---

st.caption('🧑‍💻 Made by [**Robson Ricardo**](https://github.com/jobsrobson)')
