import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Netflix Dashboard", layout="wide")


# Session state - guardar filtros entre reruns
if "tipo" not in st.session_state:
    st.session_state.tipo = "Todos"

if "anio_rango" not in st.session_state:
    st.session_state.anio_rango = (2000, 2021)

if "pais" not in st.session_state:
    st.session_state.pais = "Todos"


# Cargar y limpiar datos - solo corre una vez gracias al cache
@st.cache_data
def cargar_datos(ruta):
    df = pd.read_csv(ruta)

    df["date_added"] = pd.to_datetime(df["date_added"].str.strip(), errors="coerce")
    df["anio_agregado"] = df["date_added"].dt.year

    df["pais"] = df["country"].str.split(",").str[0].str.strip()
    df["duracion_num"] = df["duration"].str.extract(r"(\d+)")[0].astype(float)

    df["director"] = df["director"].fillna("Sin datos")
    df["listed_in"] = df["listed_in"].fillna("Sin datos")
    df["rating"] = df["rating"].fillna("Sin datos")
    df["pais"] = df["pais"].fillna("Sin datos")

    return df


# Cargar el archivo
try:
    df_raw = cargar_datos("netflix_titles.csv")
except FileNotFoundError:
    st.error("No se encontro netflix_titles.csv")
    st.stop()


# Dialog para ver el detalle de un titulo
@st.dialog("Detalle del titulo", width="large")
def ver_detalle(titulo):
    fila = df_raw[df_raw["title"] == titulo].iloc[0]

    st.subheader(fila["title"])
    st.caption(str(fila["type"]) + " | " + str(fila["release_year"]) + " | " + str(fila["rating"]))
    st.write(fila["description"])
    st.divider()

    col1, col2 = st.columns(2)
    col1.write("**Director:** " + str(fila["director"]))
    col1.write("**Pais:** " + str(fila["pais"]))
    col2.write("**Generos:** " + str(fila["listed_in"]))


# Sidebar con filtros
with st.sidebar:
    st.title("Netflix Dashboard")
    st.divider()

    st.caption("TIPO")
    tipo = st.radio(
        "Tipo",
        ["Todos", "Movie", "TV Show"],
        horizontal=True,
        label_visibility="collapsed",
        key="tipo"
    )

    st.divider()

    st.caption("AÑO")
    anio_rango = st.slider(
        "Año",
        min_value=1925,
        max_value=2021,
        value=st.session_state.anio_rango,
        label_visibility="collapsed",
        key="anio_rango"
    )

    st.divider()

    st.caption("PAIS")
    lista_paises = ["Todos"] + sorted(df_raw["pais"].replace("Sin datos", pd.NA).dropna().unique().tolist())
    pais = st.selectbox("Pais", lista_paises, label_visibility="collapsed", key="pais")

    st.divider()

    with st.popover("Mas filtros", use_container_width=True):
        lista_ratings = ["Todos"] + sorted(df_raw["rating"].replace("Sin datos", pd.NA).dropna().unique().tolist())
        rating_sel = st.selectbox("Rating:", lista_ratings)
        top_n = st.slider("Top N en graficos:", 5, 20, 10)

    st.divider()

    if st.button("Restablecer filtros", use_container_width=True):
        for k in ["tipo", "anio_rango", "pais"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()


# Aplicar filtros al dataframe
df = df_raw.copy()

if tipo != "Todos":
    df = df[df["type"] == tipo]

if pais != "Todos":
    df = df[df["pais"] == pais]

df = df[df["release_year"] >= anio_rango[0]]
df = df[df["release_year"] <= anio_rango[1]]

if rating_sel != "Todos":
    df = df[df["rating"] == rating_sel]

if len(df) == 0:
    st.warning("No hay resultados con los filtros seleccionados.")
    st.stop()


# Titulo de la pagina
st.title("Catalogo Netflix")
st.caption("Mostrando " + str(len(df)) + " titulos")
st.divider()


# KPIs
total = len(df)
n_movies = len(df[df["type"] == "Movie"])
n_shows = len(df[df["type"] == "TV Show"])
n_paises = df["pais"].replace("Sin datos", pd.NA).nunique()
n_directores = df[df["director"] != "Sin datos"]["director"].nunique()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total titulos", total)
col2.metric("Peliculas", n_movies)
col3.metric("Series", n_shows)
col4.metric("Paises", n_paises)
col5.metric("Directores", n_directores)

st.divider()


# Tabs principales
tab_overview, tab_peliculas, tab_series, tab_directores = st.tabs([
    "Overview",
    "Peliculas",
    "Series",
    "Directores"
])


# TAB OVERVIEW
with tab_overview:

    col_izq, col_der = st.columns([3, 2])

    with col_izq:
        df_timeline = df.dropna(subset=["anio_agregado"])
        df_timeline = df_timeline.groupby(["anio_agregado", "type"], as_index=False).size()
        df_timeline = df_timeline.rename(columns={"size": "count"})

        fig_timeline = px.bar(
            df_timeline,
            x="anio_agregado",
            y="count",
            color="type",
            title="Titulos agregados por año",
            labels={"anio_agregado": "Año", "count": "Titulos", "type": ""},
            color_discrete_map={"Movie": "#e50914", "TV Show": "#b20710"},
            barmode="stack"
        )
        fig_timeline.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cccccc"),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    with col_der:
        df_tipo = df.groupby("type", as_index=False).size()

        fig_donut = px.pie(
            df_tipo,
            names="type",
            values="size",
            title="Distribucion por tipo",
            hole=0.55,
            color="type",
            color_discrete_map={"Movie": "#e50914", "TV Show": "#b20710"}
        )
        fig_donut.update_traces(textinfo="percent+label", textposition="outside")
        fig_donut.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cccccc"),
            showlegend=False
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    st.subheader("Explorar titulos")

    busqueda = st.text_input("Buscar titulo", placeholder="Escribe un titulo...", label_visibility="collapsed")

    df_tabla = df.copy()
    if busqueda:
        df_tabla = df_tabla[df_tabla["title"].str.contains(busqueda, case=False, na=False)]

    titulos_lista = df_tabla["title"].dropna().tolist()

    col_sel, col_btn = st.columns([4, 1])
    titulo_elegido = col_sel.selectbox("Titulo", titulos_lista if titulos_lista else ["Sin resultados"], label_visibility="collapsed")

    if col_btn.button("Ver detalle", type="primary", disabled=(len(titulos_lista) == 0)):
        ver_detalle(titulo_elegido)

    st.dataframe(
        df_tabla[["title", "type", "release_year", "pais", "listed_in", "rating", "duration", "date_added"]].head(300),
        use_container_width=True,
        hide_index=True,
        height=380,
        column_config={
            "title":        st.column_config.TextColumn("Titulo", width="large"),
            "type":         st.column_config.TextColumn("Tipo", width="small"),
            "release_year": st.column_config.NumberColumn("Año", format="%d", width="small"),
            "pais":         st.column_config.TextColumn("Pais"),
            "listed_in":    st.column_config.TextColumn("Generos", width="large"),
            "rating":       st.column_config.TextColumn("Rating", width="small"),
            "duration":     st.column_config.TextColumn("Duracion", width="small"),
            "date_added":   st.column_config.DateColumn("Agregado", format="DD/MM/YYYY"),
        }
    )


# TAB PELICULAS
with tab_peliculas:

    df_movies = df[df["type"] == "Movie"]

    if len(df_movies) == 0:
        st.info("No hay peliculas con los filtros actuales.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            generos_lista = df_movies["listed_in"].str.split(", ").explode()
            generos_count = generos_lista.value_counts().head(top_n).reset_index()
            generos_count.columns = ["genero", "count"]

            fig_generos = px.bar(
                generos_count,
                x="count",
                y="genero",
                orientation="h",
                title="Top generos en peliculas",
                labels={"count": "Titulos", "genero": ""},
                color="count",
                color_continuous_scale="Reds"
            )
            fig_generos.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cccccc"),
                yaxis=dict(categoryorder="total ascending"),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_generos, use_container_width=True)

        with col2:
            df_duracion = df_movies.dropna(subset=["duracion_num"])

            fig_duracion = px.histogram(
                df_duracion,
                x="duracion_num",
                nbins=40,
                title="Distribucion de duracion",
                labels={"duracion_num": "Minutos"},
                color_discrete_sequence=["#e50914"]
            )
            fig_duracion.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cccccc")
            )
            st.plotly_chart(fig_duracion, use_container_width=True)

        df_por_anio = df_movies.groupby("release_year", as_index=False).size()
        df_por_anio = df_por_anio.rename(columns={"size": "count"})

        fig_anio = px.area(
            df_por_anio,
            x="release_year",
            y="count",
            title="Peliculas por año de lanzamiento",
            labels={"release_year": "Año", "count": "Peliculas"},
            color_discrete_sequence=["#e50914"]
        )
        fig_anio.update_traces(fill="tozeroy", fillcolor="rgba(229,9,20,0.12)")
        fig_anio.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cccccc")
        )
        st.plotly_chart(fig_anio, use_container_width=True)

        with st.expander("Estadisticas de duracion"):
            c1, c2, c3, c4 = st.columns(4)
            df_dur = df_movies.dropna(subset=["duracion_num"])
            c1.metric("Promedio", str(round(df_dur["duracion_num"].mean())) + " min")
            c2.metric("Mas larga", str(int(df_dur["duracion_num"].max())) + " min")
            c3.metric("Mas corta", str(int(df_dur["duracion_num"].min())) + " min")
            c4.metric("Mediana", str(round(df_dur["duracion_num"].median())) + " min")


# TAB SERIES
with tab_series:

    df_shows = df[df["type"] == "TV Show"]

    if len(df_shows) == 0:
        st.info("No hay series con los filtros actuales.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            df_temp = df_shows.dropna(subset=["duracion_num"])
            temporadas_count = df_temp["duracion_num"].value_counts().sort_index().reset_index()
            temporadas_count.columns = ["temporadas", "series"]

            fig_temp = px.bar(
                temporadas_count,
                x="temporadas",
                y="series",
                title="Series por numero de temporadas",
                labels={"temporadas": "Temporadas", "series": "Series"},
                color="series",
                color_continuous_scale="Reds"
            )
            fig_temp.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cccccc"),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_temp, use_container_width=True)

        with col2:
            generos_shows = df_shows["listed_in"].str.split(", ").explode()
            generos_shows_count = generos_shows.value_counts().head(top_n).reset_index()
            generos_shows_count.columns = ["genero", "count"]

            fig_gen_s = px.bar(
                generos_shows_count,
                x="count",
                y="genero",
                orientation="h",
                title="Top generos en series",
                labels={"count": "Series", "genero": ""},
                color="count",
                color_continuous_scale="Reds"
            )
            fig_gen_s.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cccccc"),
                yaxis=dict(categoryorder="total ascending"),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_gen_s, use_container_width=True)

        df_rating = df_shows.groupby("rating", as_index=False).size()
        df_rating = df_rating.sort_values("size", ascending=False)

        fig_rating = px.bar(
            df_rating,
            x="rating",
            y="size",
            title="Series por clasificacion",
            labels={"rating": "Rating", "size": "Series"},
            color="size",
            color_continuous_scale="Reds"
        )
        fig_rating.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cccccc"),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_rating, use_container_width=True)


# TAB DIRECTORES
with tab_directores:

    df_dirs = df[df["director"] != "Sin datos"]

    if len(df_dirs) == 0:
        st.info("No hay directores con los filtros actuales.")
    else:
        top_dirs = df_dirs.groupby("director", as_index=False).size()
        top_dirs = top_dirs.rename(columns={"size": "titulos"})
        top_dirs = top_dirs.sort_values("titulos", ascending=False).head(20)

        col1, col2 = st.columns([2, 3])

        with col1:
            st.subheader("Top 20 directores")
            st.dataframe(
                top_dirs,
                use_container_width=True,
                hide_index=True,
                height=500,
                column_config={
                    "director": st.column_config.TextColumn("Director"),
                    "titulos":  st.column_config.ProgressColumn(
                        "Titulos",
                        min_value=0,
                        max_value=int(top_dirs["titulos"].max()),
                        format="%d"
                    )
                }
            )

        with col2:
            fig_dirs = px.bar(
                top_dirs.head(15),
                x="titulos",
                y="director",
                orientation="h",
                title="Top 15 directores",
                labels={"titulos": "Titulos", "director": ""},
                color="titulos",
                color_continuous_scale="Reds",
                text="titulos"
            )
            fig_dirs.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cccccc"),
                yaxis=dict(categoryorder="total ascending"),
                coloraxis_showscale=False
            )
            fig_dirs.update_traces(textposition="outside", textfont=dict(color="#ccc"))
            st.plotly_chart(fig_dirs, use_container_width=True)


st.divider()
st.caption("Datos: Kaggle Netflix Shows dataset")
