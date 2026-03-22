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
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_OPENAI}", "Content-Type": "application/json"}
    prompt = f"Dime la Fase Lunar, posición del Sol y planetas retrógrados para el {FECHA_HOY}. Sé preciso."
    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0}
    return requests.post(url, headers=headers, json=data).json()['choices'][0]['message']['content']

def limpieza_total_segura():
    try:
        response = requests.get(f"{WP_URL}?per_page=50", auth=(WP_USER, WP_PASS))
        if response.status_code == 200:
            for p in response.json():
                if p['slug'].startswith("horoscopo-hoy-"):
                    requests.delete(f"{WP_URL}/{p['id']}?force=true", auth=(WP_USER, WP_PASS))
    except Exception as e: print(f"Error: {e}")

def generar_contenido(signo, clima):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_OPENAI}", "Content-Type": "application/json"}
    
    # Hemos añadido: "Usa un lenguaje místico pero con garra, evita sonar como un libro de texto"
    prompt = f"""Eres la 'Bruja Sin Escoba'. Horóscopo para {signo} del {FECHA_HOY}.
    CONTEXTO ASTRAL: {clima}
    INSTRUCCIONES:
    - Traduce los tránsitos planetarios a consejos prácticos y audaces.
    - No seas aburrida ni académica. Usa un tono místico, sabio y un pelín irónico.
    - Formato PLANO (sin negritas). 
    - Títulos: 🍏 Salud y Bienestar, 💰 Finanzas y Carrera, ❤️ Amor y Relaciones, 🔮 Mensaje del Oráculo.
    - 400 palabras."""

    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.85}
    return requests.post(url, headers=headers, json=data).json()['choices'][0]['message']['content']

def subir_a_wordpress(signo, contenido):
    url_img = IMAGENES_SIGNOS[signo]
    html_imagen = f'<div style="text-align: center; margin-bottom: 25px;"><img src="{url_img}" style="width: 100%; max-width: 450px; border-radius: 15px;"></div>'
    contenido_final = html_imagen + f'<p style="text-align:center;"><b>{FECHA_HOY}</b></p>' + contenido.replace("\n", "<br>")
    slug = f"horoscopo-hoy-{signo.lower()}".replace("é", "e").replace("á", "a").replace("ó", "o")
    payload = {"title": f"Horóscopo hoy {signo}", "content": contenido_final, "status": "publish", "slug": slug, "parent": PARENT_ID}
    requests.post(WP_URL, json=payload, auth=(WP_USER, WP_PASS))

if __name__ == "__main__":
    limpieza_total_segura()
    clima = obtener_clima_astral()
    for signo in SIGNOS:
        print(f"Publicando {signo}...")
        try:
            texto = generar_contenido(signo, clima)
            subir_a_wordpress(signo, texto)
        except Exception as e: print(f"Error {signo}: {e}")
    print("Finalizado.")
