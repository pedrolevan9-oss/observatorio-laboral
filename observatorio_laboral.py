"""
Observatorio laboral
Proyecto 5 - Grupo 5

Integrantes:
Juan Cruz Garofalo
Juan Bautista Fernandez Riccillo
Pedro Levandovsky
Ulises Mogliati
Manuel De Benedictis 
"""

# Librerias a instalar: pip install requests beautifulsoup4 pandas openpyxl matplotlib
import os
import json
import smtplib
import xml.etree.ElementTree as ET
from datetime import date
from email.message import EmailMessage
import requests
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

# lista de skills que queremos buscar en las ofertas
habilidades_objetivo = ["python", "sql", "pandas", "api", "cloud", "aws",
                         "docker", "java", "javascript", "excel", "linux"]

# palabras clave para saber si el puesto es junior, semi senior o senior
categorias_perfil = {
    "junior": ["trainee", "jr", "junior"],
    "semi_senior": ["semi senior", "ssr"],
    "senior": ["senior", "sr", "lead"],
}


def obtener_ofertas_scraping():
    # pagina de prueba para practicar scraping
    url = "https://realpython.github.io/fake-jobs/"
    html = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")

    # cada oferta esta en un div con esa clase
    tarjetas = soup.find_all("div", class_="card-content")

    ofertas = []
    for tarjeta in tarjetas:
        # buscamos cada dato adentro de la tarjeta
        titulo_tag = tarjeta.select_one("h2.title")
        empresa_tag = tarjeta.select_one("h3.company")
        ubicacion_tag = tarjeta.select_one("p.location")
        link_tag = tarjeta.select_one("a.card-footer-item")

        oferta = {
            "titulo": titulo_tag.get_text(strip=True),
            "empresa": empresa_tag.get_text(strip=True),
            "ubicacion": ubicacion_tag.get_text(strip=True),
            "link": link_tag.get("href", None),  # si no tiene href que no se rompa
            "fuente": "scraping",
        }
        ofertas.append(oferta)

    return ofertas

def consultar_ofertas_api():
    url = "https://remotive.com/api/remote-jobs"
    parametros = {"category": "software-dev", "limit": 20}

    # try/except por si falla la conexion o la API no responde
    try:
        respuesta = requests.get(url, params=parametros, timeout=10)
        respuesta.raise_for_status()  # tira error si el status no es 200
        datos = respuesta.json()
    except requests.exceptions.Timeout:
        print("La API tardo demasiado en responder.")
        return []
    except requests.exceptions.HTTPError as error_http:
        print("Error HTTP:", error_http)
        return []
    except requests.exceptions.RequestException as error:
        print("No se pudo consultar la API:", error)
        return []

    ofertas_crudas = datos.get("jobs", [])

    # nos quedamos solo con los campos que usamos, con valores por defecto
    ofertas = [
        {
            "titulo": oferta.get("title", "Sin titulo"),
            "empresa": oferta.get("company_name", "Sin dato"),
            "categoria": oferta.get("category", "Sin dato"),
            "descripcion": oferta.get("description", ""),
            "fuente": "api",
        }
        for oferta in ofertas_crudas
    ]

    return ofertas


def extraer_habilidades(texto):
    # pasamos todo a minuscula para que encuentre "Python" y "python"
    texto_minuscula = texto.lower()
    return [h for h in habilidades_objetivo if h in texto_minuscula]


def clasificar_seniority(titulo):
    titulo_minuscula = titulo.lower()
    # recorremos cada nivel y sus palabras, el primero que aparece en el titulo gana
    for nivel, palabras_clave in categorias_perfil.items():
        for palabra in palabras_clave:
            if palabra in titulo_minuscula:
                return nivel
    return "sin_especificar"


def calcular_metricas(ofertas):
    # contamos cuantas ofertas vienen de cada fuente
    total = len(ofertas)
    cantidad_scraping = len([o for o in ofertas if o["fuente"] == "scraping"])
    cantidad_api = len([o for o in ofertas if o["fuente"] == "api"])

    # el if es para no dividir por cero si no hay ofertas
    if total > 0:
        porcentaje_scraping = cantidad_scraping / total * 100
        porcentaje_api = cantidad_api / total * 100
    else:
        porcentaje_scraping = 0
        porcentaje_api = 0

    return {
        "total": total,
        "cantidad_scraping": cantidad_scraping,
        "cantidad_api": cantidad_api,
        "porcentaje_scraping": round(porcentaje_scraping, 1),
        "porcentaje_api": round(porcentaje_api, 1),
    }


# ---------------------------------------------------------------
# N14 - JSON y XML
# JSON se lee casi como un diccionario, con las claves.
# XML usa etiquetas que se abren y se cierran (parecido al HTML) y lo recorremos con ElementTree.
# ---------------------------------------------------------------
# ejemplos chiquitos escritos a mano para probar las funciones
texto_json = '{"jobs": [{"title": "Data Analyst Jr", "company_name": "Empresa A"}, {"title": "Python Developer Senior", "company_name": "Empresa B"}]}'

texto_xml = """
<ofertas>
    <oferta id="1">
        <titulo>Data Analyst Jr</titulo>
        <empresa>Empresa A</empresa>
    </oferta>
    <oferta id="2">
        <titulo>Python Developer Senior</titulo>
        <empresa>Empresa B</empresa>
    </oferta>
</ofertas>
"""


def leer_json(texto):
    # json.loads convierte el texto en diccionario
    datos = json.loads(texto)
    ofertas = []
    for oferta in datos["jobs"]:
        ofertas.append({"titulo": oferta["title"], "empresa": oferta["company_name"]})
    return ofertas


def leer_xml(texto):
    # fromstring nos da la etiqueta de arriba de todo (la raiz)
    raiz = ET.fromstring(texto)
    ofertas = []
    for oferta in raiz.findall("oferta"):
        ofertas.append({
            "id": oferta.get("id"),  # el id es un atributo, por eso va con get
            "titulo": oferta.find("titulo").text,
            "empresa": oferta.find("empresa").text,
        })
    return ofertas


# ---------------------------------------------------------------
# N15 - Metodos HTTP: GET y POST (y los otros 3 solo explicados)
# ---------------------------------------------------------------
metodos_http = {
    "GET": "pedir datos sin modificar nada (ej: consultar ofertas)",
    "POST": "enviar datos nuevos al servidor (ej: cargar una oferta nueva)",
    "PUT": "reemplazar un registro completo (ej: actualizar todos los datos de una oferta)",
    "PATCH": "modificar solo algunos campos (ej: cambiar solo el salario de una oferta)",
    "DELETE": "borrar un registro (ej: eliminar una oferta vencida)",
}


def ejemplo_get():
    # httpbin sirve para probar requests, nos devuelve lo que le mandamos
    try:
        respuesta = requests.get("https://httpbin.org/get", params={"busqueda": "python"}, timeout=10)
        print("GET -> status code:", respuesta.status_code)
    except requests.exceptions.RequestException as error:
        print("Error en el GET:", error)


def ejemplo_post():
    # en el POST mandamos los datos en el body, como json
    datos_a_enviar = {"titulo": "Analista de datos", "empresa": "Empresa X"}
    try:
        respuesta = requests.post("https://httpbin.org/post", json=datos_a_enviar, timeout=10)
        print("POST -> status code:", respuesta.status_code)
    except requests.exceptions.RequestException as error:
        print("Error en el POST:", error)


# ---------------------------------------------------------------
# N16 - requests: status codes, headers, parametros, timeout y errores
# (se instala con pip install requests)
# ---------------------------------------------------------------
# el User-Agent le dice al servidor quienes somos
headers_base = {"User-Agent": "ObservatorioLaboral/1.0 (TP universitario)"}


def consultar_con_requests(url, parametros=None, headers=None):
    # primero manejamos los errores de conexion
    try:
        respuesta = requests.get(url, params=parametros, headers=headers, timeout=10)
    except requests.exceptions.Timeout:
        print("Error: el servidor tardo demasiado (timeout).")
        return None
    except requests.exceptions.ConnectionError:
        print("Error: no hay conexion o la direccion no existe.")
        return None
    except requests.exceptions.RequestException as error:
        print("Error inesperado:", error)
        return None

    print("Status code:", respuesta.status_code)
    print("Tipo de contenido:", respuesta.headers.get("Content-Type"))

    # despues vemos que significa el status code
    if respuesta.status_code == 200:
        return respuesta
    elif respuesta.status_code == 401 or respuesta.status_code == 403:
        print("Error: sin permiso o clave incorrecta.")
    elif respuesta.status_code == 404:
        print("Error: la direccion no existe.")
    elif respuesta.status_code == 429:
        print("Error: demasiadas consultas.")
    elif respuesta.status_code >= 500:
        print("Error del servidor.")
    else:
        print("Respuesta no esperada.")
    return None


# ---------------------------------------------------------------
# N17 - Autenticacion con API key o token
# La clave no se escribe en el codigo, se lee de una variable de entorno.
# Ej: set OPENWEATHER_API_KEY=mi_clave
# ---------------------------------------------------------------
API_KEY_CLIMA = os.getenv("OPENWEATHER_API_KEY")
TOKEN_PRUEBA = os.getenv("TOKEN_PRUEBA", "token-de-prueba")  # token inventado, solo para probar


def probar_token_en_header():
    headers = {"Authorization": "Bearer " + TOKEN_PRUEBA}  # el token va en el header Authorization
    try:
        respuesta = requests.get("https://httpbin.org/bearer", headers=headers, timeout=10)
        print("Token en header -> status code:", respuesta.status_code)
    except requests.exceptions.RequestException as error:
        print("Error al probar el token:", error)


# ---------------------------------------------------------------
# N18 - Practica con una API publica: OpenWeatherMap
# (la API key se manda como parametro "appid")
# ---------------------------------------------------------------
def consultar_clima(ciudad):
    # si no cargamos la clave, salteamos la consulta
    if API_KEY_CLIMA is None:
        print("No hay API key cargada (OPENWEATHER_API_KEY). Se omite la consulta.")
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    parametros = {"q": ciudad, "appid": API_KEY_CLIMA, "units": "metric", "lang": "es"}

    respuesta = consultar_con_requests(url, parametros, headers_base)
    if respuesta is None:
        return None

    # sacamos del json solo lo que nos interesa
    datos = respuesta.json()
    return {
        "ciudad": datos["name"],
        "temperatura": datos["main"]["temp"],
        "humedad": datos["main"]["humidity"],
        "descripcion": datos["weather"][0]["description"],
    }


# ---------------------------------------------------------------
# N19 - Proceso ETL completo
# Extract: scraping + API + un archivo comprimido (.zip)
# Transform: limpiamos y juntamos todo con Pandas
# Load: lo guardamos en un CSV
# ---------------------------------------------------------------
archivo_historico = "historico_ofertas.zip"
archivo_salida = "ofertas_limpias.csv"


def crear_historico_simulado(nombre_zip):
    # datos inventados para simular ofertas de meses anteriores
    datos = {
        "titulo": ["Python Developer Jr", "Data Analyst SQL Semi Senior", "Backend Java Developer Senior",
                   "Analista de datos Excel", "SQL Developer Trainee", "Cloud AWS Engineer Senior"],
        "empresa": ["Empresa A", "Empresa B", "Empresa C", "Empresa D", "Empresa E", "Empresa F"],
        "ubicacion": ["Buenos Aires", "Cordoba", "Rosario", "Buenos Aires", "Mendoza", "Cordoba"],
        "fuente": ["historico"] * 6,
        "fecha": ["15/08/2026", "02/09/2026", "20/09/2026", "05/10/2026", "18/10/2026", "28/10/2026"],
    }
    # guardamos el csv adentro de un zip
    pd.DataFrame(datos).to_csv(nombre_zip, index=False,
                               compression={"method": "zip", "archive_name": "historico_ofertas.csv"})


def lista_a_texto(lista):
    # pasa ["python", "sql"] a "python, sql"
    return ", ".join(lista)


def etl_extraer(ofertas, nombre_zip):
    df_web_api = pd.DataFrame(ofertas)
    df_web_api["fecha"] = date.today().strftime("%d/%m/%Y")  # la fecha de hoy, cuando sacamos los datos
    crear_historico_simulado(nombre_zip)  # lo creamos de nuevo cada vez que corre el programa
    df_historico = pd.read_csv(nombre_zip)
    return df_web_api, df_historico


def etl_transformar(df_web_api, df_historico):
    # juntamos las ofertas actuales con el historico
    df = pd.concat([df_web_api, df_historico], ignore_index=True)

    # el historico y el scraping no tienen descripcion, la creamos vacia para que no falle
    if "descripcion" not in df.columns:
        df["descripcion"] = ""

    df["descripcion"] = df["descripcion"].fillna("")  # los nulos pasan a ser texto vacio
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y")  # pasamos la fecha a tipo datetime
    df["titulo"] = df["titulo"].str.strip()  # sacamos espacios de sobra
    df = df.drop_duplicates(subset=["titulo", "empresa"])  # sacamos ofertas repetidas

    df["seniority"] = df["titulo"].apply(clasificar_seniority)
    # buscamos las skills tanto en el titulo como en la descripcion
    texto_completo = df["titulo"] + " " + df["descripcion"]
    df["habilidades"] = texto_completo.apply(extraer_habilidades).apply(lista_a_texto)

    df = df.drop(columns=["descripcion"])  # ya no la necesitamos y es muy larga
    return df


def etl_cargar(df, nombre_archivo):
    df.to_csv(nombre_archivo, index=False)
    print("Archivo guardado:", nombre_archivo)


# ---------------------------------------------------------------
# N20 - Pandas: DataFrames, Series, operaciones basicas, tipos, nulos y funciones por columna
# ---------------------------------------------------------------
salario_por_nivel = {"junior": 800, "semi_senior": 1500, "senior": 2500}  # salarios inventados


def contar_habilidades(texto):
    # si el texto esta vacio no hay habilidades
    if texto == "":
        return 0
    return len(texto.split(", "))


# ---------------------------------------------------------------
# N21 - Leer datos con Pandas (CSV, Excel, JSON y comprimidos) y exportar a CSV, Excel y JSON
# ---------------------------------------------------------------
def exportar_resultados(df, nombre_base):
    df.to_csv(nombre_base + ".csv", index=False)
    df.to_excel(nombre_base + ".xlsx", index=False)  # para esto hay que tener openpyxl instalado
    df.to_json(nombre_base + ".json", orient="records", date_format="iso", force_ascii=False)
    print("Resultados exportados a CSV, Excel y JSON:", nombre_base)


# ---------------------------------------------------------------
# N22 - Pandas avanzado: agrupaciones, fechas, merge, join, concat y comparacion temporal
# ---------------------------------------------------------------
def contar_frecuencia_habilidades(df, nombre_columna):
    # diccionario para ir contando cuantas veces aparece cada habilidad
    frecuencias = {}
    for texto in df["habilidades"]:
        if texto != "":
            for habilidad in texto.split(", "):
                if habilidad in frecuencias:
                    frecuencias[habilidad] = frecuencias[habilidad] + 1
                else:
                    frecuencias[habilidad] = 1
    # lo pasamos a DataFrame para poder hacer el merge despues
    return pd.DataFrame(list(frecuencias.items()), columns=["habilidad", nombre_columna])


# ---------------------------------------------------------------
# N24 - Envio de emails con smtplib y EmailMessage
# El remitente, la clave y los destinatarios salen de variables de entorno (igual que en N17):
#   EMAIL_REMITENTE, EMAIL_PASSWORD (contrasena de aplicacion), EMAIL_DESTINATARIOS (separados por coma)
# ---------------------------------------------------------------
def enviar_informe(destinatarios, asunto, cuerpo, adjuntos):
    remitente = os.getenv("EMAIL_REMITENTE")
    clave = os.getenv("EMAIL_PASSWORD")

    # si falta algun dato no mandamos nada
    if remitente is None or clave is None or len(destinatarios) == 0:
        print("Faltan datos de email (EMAIL_REMITENTE, EMAIL_PASSWORD o EMAIL_DESTINATARIOS). No se envia.")
        return

    # armamos el mail
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = ", ".join(destinatarios)
    mensaje.set_content(cuerpo)

    # adjuntamos los archivos (png como imagen, lo demas como csv)
    for ruta in adjuntos:
        with open(ruta, "rb") as archivo:
            contenido = archivo.read()
        nombre = os.path.basename(ruta)
        if ruta.endswith(".png"):
            mensaje.add_attachment(contenido, maintype="image", subtype="png", filename=nombre)
        else:
            mensaje.add_attachment(contenido, maintype="text", subtype="csv", filename=nombre)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:  # nos conectamos al servidor de Gmail
            servidor.login(remitente, clave)
            servidor.send_message(mensaje)
        print("Email enviado a:", mensaje["To"])
    except smtplib.SMTPAuthenticationError:
        print("Error: usuario o contrasena de aplicacion incorrectos.")
    except (smtplib.SMTPException, OSError) as error:
        print("No se pudo enviar el email:", error)


# ---------------------------------------------------------------
# N25 - Protocolos de email (SMTP, POP e IMAP) y como usar Gmail
# ---------------------------------------------------------------
protocolos_email = {
    "SMTP": "protocolo para ENVIAR emails (es el que usamos con smtplib)",
    "POP": "protocolo para RECIBIR emails: los descarga al dispositivo y normalmente los saca del servidor",
    "IMAP": "protocolo para RECIBIR emails: los deja en el servidor y se sincronizan entre dispositivos",
}

servidores_gmail = {
    "SMTP (envio)": "smtp.gmail.com - puerto 465 (SSL) o 587 (STARTTLS)",
    "IMAP (recepcion)": "imap.gmail.com - puerto 993 (SSL)",
    "POP (recepcion)": "pop.gmail.com - puerto 995 (SSL)",
}

condiciones_gmail = [
    "Servidor de email que usamos en el proyecto: Gmail (smtp.gmail.com, puerto 465 con SSL).",
    "Gmail no acepta la contrasena comun de la cuenta desde Python.",
    "Opcion 1 - Contrasena de aplicacion: hay que activar la verificacion en 2 pasos y generar una clave de 16 caracteres en la cuenta de Google.",
    "Opcion 2 - OAuth 2.0: la aplicacion pide permiso a la cuenta y usa tokens en vez de la contrasena (mas seguro, pero mas complejo).",
    "Para usar IMAP o POP hay que habilitarlos en Gmail (Configuracion > Reenvio y correo POP/IMAP).",
    "La contrasena de aplicacion no se escribe en el codigo: se carga en la variable de entorno EMAIL_PASSWORD.",
]


# ------------------ Programa principal ------------------

print("=== Observatorio Laboral ===\n")

# juntamos las ofertas de las dos fuentes
ofertas_scraping = obtener_ofertas_scraping()
print(f"Scraping: se obtuvieron {len(ofertas_scraping)} ofertas.")

ofertas_api = consultar_ofertas_api()
print(f"API publica (Remotive): se obtuvieron {len(ofertas_api)} ofertas.\n")

todas_las_ofertas = ofertas_scraping + ofertas_api

# metricas basicas de cuantas ofertas hay
metricas = calcular_metricas(todas_las_ofertas)
print(f"Total de ofertas: {metricas['total']}")
print(f"De scraping: {metricas['cantidad_scraping']} ({metricas['porcentaje_scraping']}%)")
print(f"De API: {metricas['cantidad_api']} ({metricas['porcentaje_api']}%)\n")

# mostramos solo 10 para que no quede larguisimo
print("Clasificacion por seniority (primeras 10 ofertas):")
for oferta in todas_las_ofertas[:10]:
    nivel = clasificar_seniority(oferta["titulo"])
    print(f"  - {oferta['titulo']} -> {nivel}")

# las ofertas de scraping no tienen descripcion, por eso probamos solo con las de la API
print("\nHabilidades detectadas en las descripciones (API):")
for oferta in ofertas_api[:5]:
    habilidades = extraer_habilidades(oferta["descripcion"])
    print(f"  - {oferta['titulo']}: {habilidades}")


# ----- N14: JSON y XML -----
print("\n=== N14: JSON y XML ===")
print("Desde JSON:", leer_json(texto_json))
print("Desde XML:", leer_xml(texto_xml))


# ----- N15: GET y POST -----
print("\n=== N15: Metodos HTTP ===")
ejemplo_get()
ejemplo_post()
for metodo, descripcion in metodos_http.items():
    print(f"  - {metodo}: {descripcion}")


# ----- N16: requests -----
print("\n=== N16: requests ===")
# probamos buscar solo ofertas de python
respuesta_n16 = consultar_con_requests(
    "https://remotive.com/api/remote-jobs",
    {"category": "software-dev", "search": "python", "limit": 5},
    headers_base,
)
if respuesta_n16 is not None:
    print("Ofertas encontradas con 'python':", len(respuesta_n16.json().get("jobs", [])))


# ----- N17: autenticacion -----
print("\n=== N17: Autenticacion ===")
probar_token_en_header()


# ----- N18: OpenWeatherMap -----
print("\n=== N18: API publica OpenWeatherMap ===")
for ciudad in ["Buenos Aires,AR", "Cordoba,AR", "Rosario,AR"]:
    clima = consultar_clima(ciudad)
    if clima is not None:
        print(f"  - {clima['ciudad']}: {clima['temperatura']} C, humedad {clima['humedad']}%, {clima['descripcion']}")


# ----- N19: ETL -----
print("\n=== N19: ETL ===")
df_web_api, df_historico = etl_extraer(todas_las_ofertas, archivo_historico)
df_ofertas = etl_transformar(df_web_api, df_historico)
print("Filas despues de limpiar:", len(df_ofertas))
etl_cargar(df_ofertas, archivo_salida)


# ----- N20: Pandas -----
print("\n=== N20: Pandas ===")

# DataFrame (la tabla)
print(df_ofertas.head())
print("Filas y columnas:", df_ofertas.shape)

# Series (una sola columna)
print("\nOfertas por seniority:")
print(df_ofertas["seniority"].value_counts())

# Operaciones basicas: filtrar filas con una condicion
juniors = df_ofertas[df_ofertas["seniority"] == "junior"]
print("Cantidad de ofertas junior:", len(juniors))

# Funciones por columna: apply usa una funcion, map usa el diccionario
df_ofertas["cantidad_habilidades"] = df_ofertas["habilidades"].apply(contar_habilidades)
df_ofertas["salario_simulado"] = df_ofertas["seniority"].map(salario_por_nivel)

# Nulos: los "sin_especificar" no estan en el diccionario, entonces quedan en NaN
print("\nNulos en salario_simulado:", df_ofertas["salario_simulado"].isnull().sum())
promedio_salario = df_ofertas["salario_simulado"].mean()
df_ofertas["salario_simulado"] = df_ofertas["salario_simulado"].fillna(promedio_salario)  # los rellenamos con el promedio

# Cambio de tipo: de float a int
print("Tipo antes:", df_ofertas["salario_simulado"].dtype)
df_ofertas["salario_simulado"] = df_ofertas["salario_simulado"].astype(int)
print("Tipo despues:", df_ofertas["salario_simulado"].dtype)

# Metodos principales: describe da promedio, minimo, maximo, etc.
print("\nResumen estadistico:")
print(df_ofertas[["cantidad_habilidades", "salario_simulado"]].describe())


# ----- N21: leer datos y exportar resultados -----
print("\n=== N21: Importar y exportar ===")
exportar_resultados(df_ofertas, "ofertas_limpias")

# volvemos a leer los archivos para comprobar que se guardaron bien
df_csv = pd.read_csv("ofertas_limpias.csv", parse_dates=["fecha"])
df_excel = pd.read_excel("ofertas_limpias.xlsx")
df_json = pd.read_json("ofertas_limpias.json")
df_zip = pd.read_csv(archivo_historico)  # pandas lee el zip directo
print("Filas y columnas -> CSV:", df_csv.shape, "| Excel:", df_excel.shape,
      "| JSON:", df_json.shape, "| ZIP:", df_zip.shape)


# ----- N22: Pandas avanzado -----
print("\n=== N22: Pandas avanzado ===")

# Fechas: la columna ya la pasamos a datetime en N19, ahora sacamos el mes
df_ofertas["mes"] = df_ofertas["fecha"].dt.strftime("%Y-%m")

# Agrupaciones: contamos cuantas ofertas hay por mes
ofertas_por_mes = df_ofertas.groupby("mes").size()
print("Ofertas por mes:")
print(ofertas_por_mes)

cantidad_por_nivel = df_ofertas.groupby("seniority").size()
salario_promedio = df_ofertas.groupby("seniority")["salario_simulado"].mean()

# Join: junta las dos tablas usando el indice (seniority)
resumen_nivel = cantidad_por_nivel.to_frame("cantidad").join(salario_promedio.to_frame("salario_promedio"))
print("\nResumen por seniority (join):")
print(resumen_nivel)

# Merge + comparacion en el tiempo: habilidades del historico vs ofertas actuales
total_historico = len(df_ofertas[df_ofertas["fuente"] == "historico"])
total_actual = len(df_ofertas) - total_historico

frecuencia_historico = contar_frecuencia_habilidades(df_ofertas[df_ofertas["fuente"] == "historico"], "historico")
frecuencia_actual = contar_frecuencia_habilidades(df_ofertas[df_ofertas["fuente"] != "historico"], "actual")

# merge por la columna habilidad; "outer" para no perder las que estan en una sola tabla
comparacion = pd.merge(frecuencia_historico, frecuencia_actual, on="habilidad", how="outer")
comparacion = comparacion.fillna(0)  # si una habilidad no aparece en una de las tablas, es 0
# pasamos a porcentaje porque hay distinta cantidad de ofertas en cada grupo
comparacion["historico_%"] = (comparacion["historico"] / total_historico * 100).round(1)
comparacion["actual_%"] = (comparacion["actual"] / total_actual * 100).round(1)
comparacion["variacion_%"] = comparacion["actual_%"] - comparacion["historico_%"]
print("\nComparacion temporal de habilidades (% de ofertas):")
print(comparacion[["habilidad", "historico_%", "actual_%", "variacion_%"]])

# Concat: pone un DataFrame abajo del otro
juniors_y_seniors = pd.concat([df_ofertas[df_ofertas["seniority"] == "junior"],
                               df_ofertas[df_ofertas["seniority"] == "senior"]])
print("\nOfertas junior + senior (concat):", len(juniors_y_seniors))


# ----- N23: graficos con DataFrame.plot -----
print("\n=== N23: Visualizaciones ===")
# nos quedamos con las 5 habilidades que mas aparecen
top_habilidades = contar_frecuencia_habilidades(df_ofertas, "cantidad").sort_values("cantidad", ascending=False).head(5)

# Ranking (grafico de barras)
top_habilidades.plot(kind="bar", x="habilidad", y="cantidad", title="Top 5 habilidades mas pedidas",
                     legend=False, rot=0)
plt.ylabel("Cantidad de ofertas")
plt.tight_layout()
plt.savefig("top_habilidades.png")
plt.close()  # cerramos para que no se mezcle con el grafico que sigue

# Tendencia (grafico de linea)
ofertas_por_mes.plot(kind="line", marker="o", title="Ofertas por mes")
plt.ylabel("Cantidad de ofertas")
plt.tight_layout()
plt.savefig("ofertas_por_mes.png")
plt.close()

# Histograma (cuantas ofertas piden 1, 2, 3... habilidades)
df_ofertas["cantidad_habilidades"].plot(kind="hist", bins=5, title="Habilidades por oferta")
plt.xlabel("Cantidad de habilidades")
plt.tight_layout()
plt.savefig("histograma_habilidades.png")
plt.close()
print("Graficos guardados: top_habilidades.png, ofertas_por_mes.png, histograma_habilidades.png")


# ----- N24: envio de email -----
print("\n=== N24: Envio de email ===")
# armamos la lista de destinatarios a partir de la variable de entorno (separados por coma)
destinatarios = []
for d in os.getenv("EMAIL_DESTINATARIOS", "").split(","):
    if d.strip() != "":
        destinatarios.append(d.strip())

# armamos el texto del mail con el top 5
cuerpo = "Hola, se adjunta el informe del Observatorio Laboral.\n\nTop 5 de habilidades mas pedidas:\n"
for habilidad, cantidad in zip(top_habilidades["habilidad"], top_habilidades["cantidad"]):
    cuerpo = cuerpo + f"- {habilidad}: {cantidad} ofertas\n"
cuerpo = cuerpo + "\nSe adjuntan el grafico y el CSV con los datos.\n\nSaludos,\nGrupo 5"

enviar_informe(destinatarios, "Informe Observatorio Laboral - Top de habilidades",
               cuerpo, ["top_habilidades.png", "ofertas_limpias.csv"])


# ----- N25: protocolos de email -----
print("\n=== N25: Protocolos de email ===")
for protocolo, descripcion in protocolos_email.items():
    print(f"  - {protocolo}: {descripcion}")
print("Servidores de Gmail:")
for tipo, datos_servidor in servidores_gmail.items():
    print(f"  - {tipo}: {datos_servidor}")
print("Condiciones para usar Gmail desde Python:")
for condicion in condiciones_gmail:
    print("  -", condicion)

print("\n=== Fin del programa ===")
