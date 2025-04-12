import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

import streamlit_authenticator as stauth

# ---- AUTENTICACIÓN ----
hashed_passwords = ['$2b$12$M1KnwIj5PusgAujBMY0iFeiGNSefhIZU7DdQy3Ubp1ImvHz43E9tK']  # demo1234

credentials = {
    "usernames": {
        "admin": {
            "name": "Administrador",
            "password": hashed_passwords[0]
        }
    }
}

authenticator = stauth.Authenticate(
    credentials, "encuesta_cookie", "abcdef", cookie_expiry_days=1
)

nombre, autenticado, username = authenticator.login("📥 Iniciar sesión", "main")

if autenticado:
    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.success(f"Bienvenido/a, {nombre}")


# ---- CONFIGURACIÓN ----
st.set_page_config(page_title="Dashboard de Encuestas", layout="wide")

elif not autenticado:
    st.warning("🔒 Ingresá tus credenciales para acceder al dashboard.")
    st.stop()

st.title("📊 Dashboard de Resultados de Encuestas")

# ---- CARGA DE DATOS ----
scope = ["https://www.googleapis.com/auth/spreadsheets"]
credenciales_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = Credentials.from_service_account_info(credenciales_dict, scopes=scope)
gc = gspread.authorize(creds)

# Abro la planilla
sheet = gc.open_by_key("1440OXxY-2bw7NAFr01hGeiVYrbHu_G47u9IIoLfaAjM")
respuestas = pd.DataFrame(sheet.worksheet("respuestas").get_all_records())
comisiones = pd.DataFrame(sheet.worksheet("comisiones").get_all_records())

# Merge con nombres de actividades
data = respuestas.merge(comisiones, on="comision", how="left")
data["nombre_actividad"].fillna("Sin nombre", inplace=True)

# ---- SELECTOR DE ACTIVIDAD ----
opciones = ["(Todas)"] + sorted(data["nombre_actividad"].unique().tolist())
actividad = st.selectbox("🔍 Seleccioná una actividad", opciones)

if actividad != "(Todas)":
    data = data[data["nombre_actividad"] == actividad]

st.subheader("🧮 Resumen general")
st.markdown(f"Total de respuestas: **{len(data)}**")

# ---- FUNCIONES DE GRÁFICOS ----
def graficar_torta(columna, titulo, ax):
    conteo = data[columna].value_counts()
    colores = ["#F4A7B9", "#A9CCE3", "#ABEBC6", "#F9E79F", "#D2B4DE"]
    ax.pie(conteo, labels=conteo.index, autopct='%1.1f%%', colors=colores[:len(conteo)])
    ax.set_title(titulo)

# ---- GRÁFICOS DE TORTA ----
fig, axs = plt.subplots(2, 2, figsize=(14, 10))

graficar_torta("conocimientos_previos", "CONOCIMIENTOS PREVIOS\n SOBRE LOS TEMAS DESARROLLADOS", axs[0, 0])
graficar_torta("valoracion_curso", "VALORACIÓN GENERAL DEL CURSO", axs[0, 1])
graficar_torta("conocimientos_aplicables", "APLICACIÓN PRÁCTICA DE LA CAPACITACIÓN\n EN EL PUESTO DE TRABAJO", axs[1, 0])
graficar_torta("valoracion_docente", "VALORACIÓN DEL DESEMPEÑO DOCENTE", axs[1, 1])

st.pyplot(fig)

# ---- NUBE DE PALABRAS ----
st.subheader("☁️ ¿Qué aprendizajes adquiriste en este curso?")

texto = data["aprendizajes_adquiridos"].dropna().astype(str).str.lower()
texto = texto.str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("utf-8")
texto = texto.str.replace(r"[^\w\s]", " ", regex=True).str.cat(sep=" ")

stopwords = STOPWORDS.union({
    "y", "de", "al", "el", "la", "los", "las", "que", "con", "en", "como", "para",
    "mi", "un", "q", "ya", "tenia", "hecho", "cuando", "más", "habia", "del",
    "muy", "gral", "si", "_x000d", "_x000d_", "hay", "entre", "lo", "es", "hacia", "mis", "mas", "una",
    "eso", "su", "sus", "esa", "esas", "cual", "cuales", "tambien", "por", "sin", "se", "sobre",
    "ante", "rt", "o", "estar", "bien", "tener", "ser", "todo", "hacer", "cosa", "juan", "ggo", "sabia",
    "gracias", "otro", "otros", "sirve", "divertida", "hace", "nada", "e", "donde", "buena"
})

wordcloud = WordCloud(width=1000, height=400, background_color="white", max_words=40,
                      stopwords=stopwords, colormap='viridis').generate(texto)

plt.figure(figsize=(12, 5))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("CONOCIMIENTOS ADQUIRIDOS EN EL CURSO", fontsize=18)
st.pyplot(plt)
