# Observatorio de empleo, capacitación y tendencias de perfiles laborales

**Taller de Programación II – UADE**
Proyecto 5 – Grupo 5

## Integrantes

- Juan Cruz Garofalo
- Juan Bautista Fernandez Riccillo
- Pedro Levandovsky
- Ulises Mogliati
- Manuel De Benedictis

## Descripción

Programa en Python que recolecta ofertas laborales de distintas fuentes, las limpia y las analiza para detectar qué habilidades se piden y en qué nivel de seniority.

- **Fuentes de datos:** web scraping (Real Python Fake Jobs), API pública (Remotive) y un histórico simulado en un archivo `.zip`.
- **Proceso ETL:** extracción, limpieza y unión de los datos con Pandas, y guardado en CSV.
- **Análisis:** clasificación por seniority (junior, semi senior, senior), detección de habilidades, agrupaciones, merge/join/concat y comparación temporal.
- **Visualizaciones:** ranking de habilidades, ofertas por mes e histograma.
- **Exportación:** CSV, Excel y JSON.
- **Email:** envío del informe con gráfico y CSV adjuntos vía Gmail (SMTP).

El código está organizado por los temas de la materia (N14 a N25): JSON y XML, métodos HTTP, `requests`, autenticación con API key/token, OpenWeatherMap, ETL, Pandas, gráficos y email.

## Requisitos

- Python 3.9 o superior

```bash
pip install -r requirements.txt
```

## Cómo ejecutarlo

```bash
python observatorio_laboral.py
```

### Variables de entorno (opcionales)

Las claves no están escritas en el código. Si no se cargan, el programa saltea esas partes y sigue funcionando.

| Variable | Para qué se usa |
|---|---|
| `OPENWEATHER_API_KEY` | Consulta del clima en OpenWeatherMap (N18) |
| `TOKEN_PRUEBA` | Token de prueba para el header `Authorization` (N17) |
| `EMAIL_REMITENTE` | Cuenta de Gmail que envía el informe (N24) |
| `EMAIL_PASSWORD` | Contraseña de aplicación de Gmail (N24) |
| `EMAIL_DESTINATARIOS` | Destinatarios del informe, separados por coma (N24) |

Ejemplo en Windows:

```bash
set OPENWEATHER_API_KEY=mi_clave
```

## Archivos que genera

- `historico_ofertas.zip`: histórico simulado
- `ofertas_limpias.csv`, `ofertas_limpias.xlsx`, `ofertas_limpias.json`: datos procesados
- `top_habilidades.png`, `ofertas_por_mes.png`, `histograma_habilidades.png`: gráficos
