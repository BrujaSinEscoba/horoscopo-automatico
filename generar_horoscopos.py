import os
import requests
import json
import datetime
import pytz

# --- CONFIGURACIÓN ---
API_KEY_OPENAI = os.getenv("OPENAI_API_KEY")
WP_USER = os.getenv("WP_USER")
WP_PASS = os.getenv("WP_PASS")
WP_URL = "https://www.brujasinescoba.com/wp-json/wp/v2/pages"
PARENT_ID = 61

IMAGENES_SIGNOS = {
    "Aries": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Aries.jpeg",
    "Tauro": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Tauro.jpeg",
    "Géminis": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Geminis.jpeg",
    "Cáncer": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Cancer.jpeg",
    "Leo": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Leo.jpeg",
    "Virgo": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Virgo.jpeg",
    "Libra": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Libra.jpeg",
    "Escorpio": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Escorpio.jpeg",
    "Sagitario": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Sagitario.jpeg",
    "Capricornio": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Capricornio.jpeg",
    "Acuario": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Acuario.jpeg",
    "Piscis": "https://www.brujasinescoba.com/wp-content/uploads/2026/03/Piscis.jpeg"
}

SIGNOS = list(IMAGENES_SIGNOS.keys())

tz_espana = pytz.timezone('Europe/Madrid')
ahora_espana = datetime.datetime.now(tz_espana)
meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
FECHA_HOY = f"{ahora_espana.day} de {meses[ahora_espana.month - 1]} de {ahora_espana.year}"

def obtener_clima_astral():
    """La IA actúa como astrónoma para darnos la posición real de los planetas hoy"""
    print("🔭 Consultando las efemérides planetarias...")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_OPENAI}", "Content-Type": "application/json"}
    
    prompt = f"""Hoy es {FECHA_HOY}. Actúa como un motor de efemérides astronómicas. 
    Dime brevemente para esta fecha:
    1. Fase Lunar y en qué signo está la Luna.
    2. Posición del Sol (Signo).
    3. Planetas retrógrados (Mercurio, Venus, Marte, Júpiter, Saturno).
    4. Tránsitos o aspectos importantes de hoy (ej: conjunciones o cuadraturas).
    Sé técnico y preciso."""

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def limpieza_total_segura():
    print("🔍 Limpiando horóscopos anteriores...")
    try:
        response = requests.get(f"{WP_URL}?per_page=50", auth=(WP_USER, WP_PASS))
        if response.status_code == 200:
            for p in response.json():
                if p['slug'].startswith("horoscopo-hoy-"):
                    requests.delete(f"{WP_URL}/{p['id']}?force=true", auth=(WP_USER, WP_PASS))
    except Exception as e: print(f"❌ Error limpieza: {e}")

def generar_contenido(signo, clima_astral):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_OPENAI}", "Content-Type": "application/json"}
    
    prompt = f"""Eres la 'Bruja Sin Escoba'. Escribe el horóscopo para {signo} del día {FECHA_HOY}.
    
    CONTEXTO ASTRAL REAL DE HOY:
    {clima_astral}
    
    REGLAS DE ORO:
    - Usa el contexto astral anterior para que tus predicciones sean reales y profesionales.
    - No seas genérica. Si un planeta está retrógrado, explica cómo afecta a {signo} específicamente.
    - Tono sabio, directo y místico. Sin intro ni despedida.
    - Formato PLANO (sin negritas ni asteriscos).
    - Títulos exactos con sus iconos: 🍏 Salud y Bienestar, 💰 Finanzas y Carrera, ❤️ Amor y Relaciones, 🔮 Mensaje del Oráculo.
    - Extensión: 400 palabras."""

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def subir_a_wordpress(signo, contenido):
    url_img = IMAGENES_SIGNOS[signo]
    html_imagen = f'<div style="text-align: center; margin-bottom: 25px;"><img src="{url_img}" style="width: 100%; max-width: 450px; border-radius: 15px;"></div>'
    
    # Ponemos la fecha arriba para que el lector sepa de qué día es
    fecha_html = f'<p style="text-align:center; font-weight:bold;">{FECHA_HOY}</p>'
    contenido_final = html_imagen + fecha_html + contenido.replace("\n", "<br>")
    
    slug = f"horoscopo-hoy-{signo.lower()}".replace("é", "e").replace("á", "a").replace("ó", "o")
    payload = {
        "title": f"Horóscopo hoy {signo}",
        "content": contenido_final,
        "status": "publish",
        "slug": slug,
        "parent": PARENT_ID
    }
    requests.post(WP_URL, json=payload, auth=(WP_USER, WP_PASS))

if __name__ == "__main__":
    limpieza_total_segura()
    # PASO 1: Miramos el cielo
    clima = obtener_clima_astral()
    print(f"🌌 El cielo hoy dice:\n{clima}\n")
    
    # PASO 2: Generamos cada signo basado en el cielo
    for signo in SIGNOS:
        print(f"🔮 Publicando {signo} con rigor astral...")
        try:
            texto = generar_contenido(signo, clima)
            subir_a_wordpress(signo, texto)
        except Exception as e: print(f"❌ Error {signo}: {e}")
        
    print("\n✨ ¡Proceso finalizado con éxito!")
