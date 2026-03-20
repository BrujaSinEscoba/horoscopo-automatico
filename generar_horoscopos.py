import requests
import json
import datetime
import os

# --- CONFIGURACIÓN DESDE LA "CAJA FUERTE" (SECRETS) ---
API_KEY_OPENAI = os.getenv("OPENAI_API_KEY")
WP_USER = os.getenv("WP_USER")
WP_PASS = os.getenv("WP_PASS")

# URLs fijas
WP_URL = "https://www.brujasinescoba.com/wp-json/wp/v2/pages"
PARENT_ID = 61

SIGNOS = [
    "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", 
    "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
]

# Fecha automática en español
meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
ahora = datetime.datetime.now()
FECHA_HOY = f"{ahora.day} de {meses[ahora.month - 1]} de {ahora.year}"

def limpieza_total_segura():
    print("🔍 Iniciando limpieza de horóscopos diarios anteriores...")
    try:
        response = requests.get(f"{WP_URL}?per_page=50", auth=(WP_USER, WP_PASS))
        if response.status_code == 200:
            paginas = response.json()
            for p in paginas:
                if p['slug'].startswith("horoscopo-hoy-"):
                    p_id = p['id']
                    requests.delete(f"{WP_URL}/{p_id}?force=true", auth=(WP_USER, WP_PASS))
                    print(f"🗑️ Borrado con éxito: {p['slug']}")
        else:
            print(f"⚠️ Error al acceder a WP para limpiar: {response.status_code}")
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")

def generar_contenido(signo):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_OPENAI}", "Content-Type": "application/json"}
    
    prompt = f"""Escribe el horóscopo para el signo {signo} para el día {FECHA_HOY}.
    
    Instrucciones de formato CRUCIALES:
    1. Escribe el texto en formato PLANO. 
    2. NO uses asteriscos (**), ni almohadillas (###), ni ningún símbolo de Markdown.
    3. Escribe la fecha {FECHA_HOY} al inicio en una línea sola.
    4. Usa exactamente estos títulos con sus emoticonos (en texto plano, sin negritas):
    
    🍏 Salud y Bienestar
    💰 Finanzas y Carrera
    ❤️ Amor y Relaciones
    🔮 Mensaje del Oráculo

    Estilo: 400 palabras, tono moderno, directo y práctico. 
    No añadas introducciones ni despedidas."""

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def subir_a_wordpress(signo, contenido):
    slug = f"horoscopo-hoy-{signo.lower()}".replace("é", "e").replace("á", "a").replace("ó", "o")
    payload = {
        "title": f"Horóscopo hoy {signo}",
        "content": contenido,
        "status": "publish",
        "slug": slug,
        "parent": PARENT_ID,
        "format": "standard"
    }
    
    response = requests.post(WP_URL, json=payload, auth=(WP_USER, WP_PASS))
    if response.status_code == 201:
        print(f"✅ {signo} publicado con éxito.")
    else:
        print(f"❌ Error en {signo}: {response.status_code}")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    limpieza_total_segura()
    for signo in SIGNOS:
        print(f"Generando {signo}...")
        try:
            texto = generar_contenido(signo)
            subir_a_wordpress(signo, texto)
        except Exception as e:
            print(f"❌ Error con {signo}: {e}")
    
    print("\n✨ ¡Proceso finalizado!")
