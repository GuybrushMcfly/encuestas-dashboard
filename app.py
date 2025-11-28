# ---- IMPORTS ----
import json
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


# ---- CONFIGURACIÓN DE PÁGINA ----
st.set_page_config(page_title="Dashboard de Encuestas", layout="wide")


# ---- CARGAR CONFIGURACIÓN DESDE YAML ----
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)


# ---- CREAR OBJETO AUTENTICADOR ----
authenticator = stauth.Authenticate(
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    cookie_key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days']
)


# ---- LOGIN ----
authenticator.login()

if st.session_state["authentication_status"]:
    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.success(f"Bienvenido/a, {st.session_state['name']}")
    st.title("📊 Dashboard de Encuestas")

elif st.session_state["authentication_status"] is False:
    st.error("❌ Usuario o contraseña incorrectos.")
    st.stop()

elif st.session_state["authentication_status"] is None:
    st.warning("🔒 Ingresá tus credenciales para acceder al dashboard.")
    st.stop()



# ---- CARGA DE DATOS ----
scope = ["https://www.googleapis.com/auth/spreadsheets"]
credenciales_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = Credentials.from_service_account_info(credenciales_dict, scopes=scope)
gc = gspread.authorize(creds)

# Cargar la hoja nueva
sheet = gc.open_by_key("1440OXxY-2bw7NAFr01hGeiVYrbHu_G47u9IIoLfaAjM")
data = pd.DataFrame(sheet.worksheet("respuestas-informe").get_all_records())

# Renombrar para mantener compatibilidad
data = data.rename(columns={"comision": "nombre_actividad"})



# ================================================================
#  🔘 SELECTOR MÚLTIPLE DE COMISIONES (checkbox)
# ================================================================

st.subheader("📌 Seleccioná las comisiones que querés incluir en los gráficos")

todas_comisiones = sorted(data["nombre_actividad"].unique().tolist())

seleccion = st.multiselect(
    "Elegí una o varias comisiones:",
    todas_comisiones,
    default=todas_comisiones  # por defecto: todas seleccionadas
)

# Filtrar
if seleccion:
    data = data[data["nombre_actividad"].isin(seleccion)]



# ---- CONTADOR ----
st.markdown(f"Total de respuestas seleccionadas: **{len(data)}**")



# ---- FUNCIÓN DE GRÁFICO ----
def graficar_torta(columna, titulo, ax):
    conteo = data[columna].value_counts()
    colores = ["#F4A7B9", "#A9CCE3", "#ABEBC6", "#F9E79F", "#D2B4DE"]
    ax.pie(conteo, labels=conteo.index, autopct='%1.1f%%', colors=colores[:len(conteo)])
    ax.set_title(titulo, fontsize=12)


# ================================================================
#  📊 GRAFICOS (siempre los mismos)
# ================================================================

fig, axs = plt.subplots(2, 2, figsize=(14, 10))

graficar_torta("conocimientos_previos",
               "CONOCIMIENTOS PREVIOS SOBRE LOS TEMAS DESARROLLADOS",
               axs[0, 0])

graficar_torta("valoracion_curso",
               "VALORACIÓN GENERAL DEL CURSO",
               axs[0, 1])

graficar_torta("conocimientos_aplicables",
               "APLICACIÓN PRÁCTICA EN EL PUESTO DE TRABAJO",
               axs[1, 0])

graficar_torta("valoracion_docente",
               "VALORACIÓN DEL DESEMPEÑO DOCENTE",
               axs[1, 1])

st.pyplot(fig)



# ================================================================
#  ☁️ NUBE DE PALABRAS
# ================================================================
st.subheader("☁️ ¿Qué aprendizajes adquiriste en este curso?")

texto = data["aprendizajes_adquiridos"].dropna().astype(str).str.lower()
texto = texto.str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("utf-8")
texto = texto.str.replace(r"[^\w\s]", " ", regex=True).str.cat(sep=" ")

stopwords = STOPWORDS.union({
    "y", "de", "al", "el", "la", "los", "las", "que", "con", "en", "como", "para",
    "mi", "un", "q", "ya", "tenia", "hecho", "cuando", "mas", "habia", "del",
    "muy", "gral", "si", "_x000d", "_x000d_", "hay", "entre", "lo", "es", "hacia", "mis", "una",
    "eso", "su", "sus", "esa", "esas", "cual", "cuales", "tambien", "por", "sin", "se", "sobre",
    "ante", "rt", "o", "estar", "bien", "tener", "ser", "todo", "hacer", "cosa", "gracias", "otra", "otro", "otros", "otras"    
})

wordcloud = WordCloud(
    width=1000,
    height=400,
    background_color="white",
    max_words=40,
    stopwords=stopwords,
    colormap="viridis"
).generate(texto)

plt.figure(figsize=(12, 5))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("CONOCIMIENTOS ADQUIRIDOS EN EL CURSO", fontsize=18)

st.pyplot(plt)
