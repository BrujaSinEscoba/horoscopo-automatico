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

# Cabecera para que WordPress no nos bloquee (User-Agent)
HEADERS_WP = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

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

tz_madrid = pytz.timezone('Europe/Madrid')
ahora_madrid = datetime.datetime.now(tz_madrid)
meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
FECHA_HOY = f"{ahora_madrid.day} de {meses[ahora_madrid.month - 1]} de {ahora_madrid.year}"

def limpieza_total_segura():
    print(f"🔍 Limpiando horóscopos anteriores...")
    try:
        # Añadimos HEADERS_WP aquí
        response = requests.get(f"{WP_URL}?per_page=100", auth=(WP_USER, WP_PASS), headers=HEADERS_WP)
        if response.status_code != 200:
            print(f"❌ Error conectando a WP: {response.status_code}")
            print(f"Detalle del error: {response.text}")
            sys.exit(1)
            
        paginas = response.json()
        for p in paginas:
            if p['slug'].startswith("horoscopo-hoy-"):
                res = requests.delete(f"{WP_URL}/{p['id']}?force=true", auth=(WP_USER, WP_PASS), headers=HEADERS_WP)
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
    prompt = (f"Eres la 'Bruja Sin Escoba'. Escribe el horóscopo completo para {signo} del día {FECHA_HOY}. "
              f"Estilo místico y canalla. 5 puntos: Energía, Amor, Trabajo, Salud y Advertencia.")
    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.85}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        sys.exit(1)
    return response.json()['choices'][0]['message']['content']

def subir_a_wordpress(signo, contenido):
    url_img = IMAGENES_SIGNOS[signo]
    signo_url = signo.lower().replace("é", "e").replace("á", "a").replace("ó", "o")
    html_imagen = f'<div style="text-align: center; margin-bottom: 20px;"><img src="{url_img}" style="width: 100%; max-width: 450px; height: auto; border-radius: 15px;"></div>'
    contenido_final = html_imagen + f'<p style="text-align: center;"><b>{FECHA_HOY}</b></p>' + contenido.replace("\n", "<br>")
    
    payload = {"title": f"Horóscopo hoy {signo}", "content": contenido_final, "status": "publish", "slug": f"horoscopo-hoy-{signo_url}", "parent": PARENT_ID}
    # Añadimos HEADERS_WP aquí también
    res = requests.post(WP_URL, json=payload, auth=(WP_USER, WP_PASS), headers=HEADERS_WP)
    if res.status_code != 201:
        print(f"❌ Error subiendo {signo}: {res.status_code}")
        sys.exit(1)
    print(f"✅ {signo} publicado.")

if __name__ == "__main__":
    limpieza_total_segura()
    for signo in SIGNOS:
        print(f"🔮 Procesando {signo}...")
        texto = generar_contenido(signo)
        subir_a_wordpress(signo, texto)
    print(f"\n✨ ¡Proceso finalizado!")
