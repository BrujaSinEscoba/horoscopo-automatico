import os
import requests
import json
import datetime
import pytz
import sys

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

# Configuración de fecha en español (Madrid)
tz_madrid = pytz.timezone('Europe/Madrid')
ahora_madrid = datetime.datetime.now(tz_madrid)
meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
FECHA_HOY = f"{ahora_madrid.day} de {meses[ahora_madrid.month - 1]} de {ahora_madrid.year}"

def limpieza_total_segura():
    print(f"🔍 Limpiando horóscopos anteriores...")
    try:
        response = requests.get(f"{WP_URL}?per_page=100", auth=(WP_USER, WP_PASS))
        if response.status_code != 200:
            print(f"❌ Error conectando a WP: {response.status_code}")
            sys.exit(1)
            
        paginas = response.json()
        for p in paginas:
            if p['slug'].startswith("horoscopo-hoy-"):
                res = requests.delete(f"{WP_URL}/{p['id']}?force=true", auth=(WP_USER, WP_PASS))
                if res.status_code == 200:
                    print(f"🗑️ Eliminado: {p['slug']}")
                else:
                    print(f"⚠️ Error al eliminar {p['slug']}")
                    sys.exit(1)
    except Exception as e:
        print(f"❌ Fallo crítico en limpieza: {e}")
        sys.exit(1)

def generar_contenido(signo):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_OPENAI}", "Content-Type": "application/json"}
    
    # PROMPT MEJORADO PARA TEXTOS MÁS LARGOS
    prompt = (f"Eres la 'Bruja Sin Escoba'. Escribe el horóscopo detallado para {signo} del día {FECHA_HOY}. "
              f"Usa tu estilo místico, directo, canalla y un poco gamberro. "
              f"Divide obligatoriamente el texto en tres secciones con títulos en negrita: "
              f"1. Energía Astral (analiza el día), 2. Amor y Relaciones, 3. La Advertencia de la Bruja. "
              f"Extensión aproximada: entre 250 y 300 palabras.")
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"❌ Error OpenAI: {response.status_code}")
        sys.exit(1)
    
    return response.json()['choices'][0]['message']['content']

def subir_a_wordpress(signo, contenido):
    url_img = IMAGENES_SIGNOS[signo]
    signo_url = signo.lower().replace("é", "e").replace("á", "a").replace("ó", "o")
    
    html_imagen = f'<div style="text-align: center; margin-bottom: 20px;"><img src="{url_img}" style="max-width: 450px; border-radius: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.3);"></div>'
    contenido_final = html_imagen + f'<p style="text-align: center; font-size: 1.2em;"><b>{FECHA_HOY}</b></p>' + contenido.replace("\n", "<br>")
    
    payload = {
        "title": f"Horóscopo hoy {signo}",
        "content": contenido_final,
        "status": "publish",
        "slug": f"horoscopo-hoy-{signo_url}",
        "parent": PARENT_ID
    }
    
    res = requests.post(WP_URL, json=payload, auth=(WP_USER, WP_PASS))
    if res.status_code != 201:
        print(f"❌ Error subiendo {signo}: {res.status_code}")
        sys.exit(1)
    print(f"✅ {signo} publicado con éxito.")

if __name__ == "__main__":
    limpieza_total_segura()
    for signo in SIGNOS:
        print(f"🔮 Procesando {signo}...")
        texto = generar_contenido(signo)
        subir_a_wordpress(signo, texto)
    print(f"\n✨ ¡Proceso finalizado con éxito! La Bruja ha vuelto con fuerza.")
