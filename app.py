import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Mapas em Streamlit",
    page_icon="🗺️",
    layout="wide"
)

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
    ("Streamlit - Nativo", "Plotly Express - Marcadores", "Plotly Express - Mapa de Calor", "Plotly Express - Tamanho"),
    help="Selecione o motor de renderização do mapa"
)

# Filtar por estado
if map_option != "Streamlit - Nativo":
    filtrar_por_estado = st.sidebar.checkbox("Filtrar por Estado", value=False)
    if filtrar_por_estado:
        estado_selecionado = st.sidebar.selectbox(
            "Selecione o estado:",
            sorted(estados['nome'].unique())
        )
        df_estado = df_merged[df_merged['estado'] == estado_selecionado].copy()  # Filtra df_merged
    else:
        estado_selecionado = "Todos os Estados"
        df_estado = df_merged.copy()
else:
    estado_selecionado = st.sidebar.selectbox(
        "Selecionar estado para Mapa Streamlit:",
        ["Todos os Estados"] + list(estados['nome'].unique())
    )
    df_estado = df_merged.copy() # Garante que df_estado esteja definido para o Streamlit também


# Filtrar por região
regioes_brasil = df_estado['regiao'].unique() # Usa df_estado já filtrado
filtrar_por_regiao = st.sidebar.checkbox("Filtrar por Região", value=False)
if filtrar_por_regiao:
    regiao_selecionada = st.sidebar.multiselect("Selecione a(s) região(ões):", regioes_brasil)
    df_filtered_regiao = df_estado[df_estado['regiao'].isin(regiao_selecionada)] # Aplica filtro à df_estado
else:
    df_filtered_regiao = df_estado.copy()

# Filtrar por UF
ufs_brasil = df_filtered_regiao['uf'].unique()
filtrar_por_uf = st.sidebar.checkbox("Filtrar por Unidade Federativa (UF)", value=False)
if filtrar_por_uf:
    uf_selecionada = st.sidebar.multiselect("Selecione a(s) UF(s):", ufs_brasil)
    df_final = df_filtered_regiao[df_filtered_regiao['uf'].isin(uf_selecionada)] # Cria novo df para exibição
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
    if map_option == "Plotly Express - Tamanho":
        tamanho_pop = st.sidebar.checkbox("Mostrar tamanho do marcador pela população", value=True)
        max_tamanho_marcador = st.sidebar.slider("Tamanho máximo do marcador:", 5, 50, 20)
    else:
        tamanho_pop = False
        max_tamanho_marcador = 20


# --- Exibição do Mapa ---
st.subheader(f"Mapa {map_option.split(' - ')[-1] if ' - ' in map_option else map_option}")

config = {'scrollZoom': True}

if map_option == "Plotly Express - Marcadores":
    st.write("Este mapa utiliza marcadores para representar a localização dos municípios. Passe o mouse para detalhes.")
    fig = px.scatter_mapbox(
        df_final, # Usa df_final
        lat="latitude",
        lon="longitude",
        hover_name="municipio",
        hover_data=["estado", "uf", "regiao", "pop_21"],
        color=color_column,
        zoom=initial_zoom,
        height=map_height
    )
    fig.update_layout(mapbox_style=map_style, dragmode='zoom', showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, config=config, use_container_width=True)

elif map_option == "Plotly Express - Mapa de Calor":
    st.write("Este mapa de calor mostra a densidade de municípios. Cores intensas indicam maior concentração.")
    fig = px.density_mapbox(
        df_final, # Usa df_final
        lat="latitude",
        lon="longitude",
        z=df_final.index,  # Usando o índice como medida de densidade
        radius=10,
        center=go.layout.mapbox.Center(
            lat=df_final['latitude'].mean(), # Usa df_final
            lon=df_final['longitude'].mean()
        ),
        zoom=initial_zoom,
        mapbox_style=map_style,
        height=map_height
    )
    st.plotly_chart(fig, config=config, use_container_width=True)

elif map_option == "Plotly Express - Tamanho":
    st.write("Este mapa exibe marcadores onde o tamanho é proporcional à população do município em 2021.")
    if tamanho_pop:
        fig = px.scatter_mapbox(
            df_final, # Usa df_final
            lat="latitude",
            lon="longitude",
            hover_name="municipio",
            hover_data=["estado", "uf", "regiao", "pop_21"],
            size="pop_21",
            size_max=max_tamanho_marcador,
            zoom=initial_zoom,
            height=map_height
        )
        fig.update_layout(mapbox_style=map_style, dragmode='zoom', showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, config=config, use_container_width=True)
    else:
        st.info("Selecione a opção 'Mostrar tamanho do marcador pela população' na barra lateral.")


elif map_option == "Streamlit - Nativo":
    st.write("Mapa interativo básico do Streamlit para exibir pontos geográficos.")
    if not df_final.empty: # Usa df_final
        st.map(df_final[['latitude', 'longitude']], height=700, use_container_width=True)
    else:
        st.warning("Não há dados para exibir com os filtros selecionados.")

with st.expander("Visualizar Dados Filtrados"):
    st.dataframe(df_final) # Exibe df_final

with st.expander("Visualizar Dados Brutos"):
    st.dataframe(df_merged)


# --- Rodapé ---

st.caption('🧑‍💻 Made by [**Robson Ricardo**](https://github.com/jobsrobson)')