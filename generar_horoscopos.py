import os
import requests
import json
import datetime
import pytz

# --- CONFIGURACIÓN ---
API_KEY_OPENAI = os.getenv("OPENAI_API_KEY")
WP_USER = os.getenv("WP_USER")
WP_PASS = os.getenv("WP_PASS")
WP_URL = "ERROR-PRUEBA.com"
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

# --- FIJAMOS LA FECHA UNA SOLA VEZ PARA TODO EL PROCESO ---
tz_madrid = pytz.timezone('Europe/Madrid')
ahora_madrid = datetime.datetime.now(tz_madrid)
meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
# Esta variable FECHA_HOY es global; se hereda en todas las funciones
FECHA_HOY = f"{ahora_madrid.day} de {meses[ahora_madrid.month - 1]} de {ahora_madrid.year}"

def limpieza_total_segura():
    print(f"🔍 Limpiando horóscopos anteriores para asegurar la fecha de hoy ({FECHA_HOY})...")
    try:
        response = requests.get(f"{WP_URL}?per_page=50", auth=(WP_USER, WP_PASS))
        if response.status_code == 200:
            for p in response.json():
                if p['slug'].startswith("horoscopo-hoy-"):
                    requests.delete(f"{WP_URL}/{p['id']}?force=true", auth=(WP_USER, WP_PASS))
                    print(f"🗑️ Eliminado: {p['slug']}")
    except Exception as e: print(f"❌ Error en limpieza: {e}")

def generar_contenido(signo):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_OPENAI}", "Content-Type": "application/json"}
    
    prompt = f"""Eres la 'Bruja Sin Escoba'. Escribe el horóscopo para el signo {signo} del día {FECHA_HOY}.
    
    INSTRUCCIONES:
    - No hables de posiciones planetarias ni fases lunares.
    - Usa un lenguaje místico, sabio, directo y con un toque irónico o audaz.
    - Inspírate en la energía del día {ahora_madrid.day}.
    - Formato PLANO (sin negritas ni asteriscos).
    - Escribe la fecha {FECHA_HOY} al inicio en una línea sola.
    - Títulos exactos: 🍏 Salud y Bienestar, 💰 Finanzas y Carrera, ❤️ Amor y Relaciones, 🔮 Mensaje del Oráculo.
    - Extensión: 400 palabras."""

    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.85}
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def subir_a_wordpress(signo, contenido):
    url_img = IMAGENES_SIGNOS[signo]
    html_imagen = f'<div style="text-align: center; margin-bottom: 25px;"><img src="{url_img}" style="width: 100%; max-width: 450px; border-radius: 15px;"></div>'
    
    signo_url = signo.lower().replace("é", "e").replace("á", "a").replace("ó", "o")
    link_final = (
        f'<div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;">'
        f'<p><b>Consulta el horóscopo completo de {signo} (semanal y mensual) aquí:</b></p>'
        f'<p><a href="https://www.brujasinescoba.com/horoscopos/horoscopo-{signo_url}/" target="_blank" rel="noopener">Horóscopo de {signo} completo</a></p>'
        f'</div>'
    )
    
    # Insertamos la FECHA_HOY global también en el cuerpo del post por seguridad
    contenido_final = html_imagen + f'<p style="text-align:center;"><b>{FECHA_HOY}</b></p>' + contenido.replace("\n", "<br>") + link_final
    
    slug = f"horoscopo-hoy-{signo_url}"
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
    for signo in SIGNOS:
        print(f"🔮 Procesando {signo} para el {FECHA_HOY}...")
        try:
            texto = generar_contenido(signo)
            subir_a_wordpress(signo, texto)
        except Exception as e: print(f"❌ Error en {signo}: {e}")
    print(f"\n✨ ¡Proceso finalizado! Todos los signos publicados con fecha {FECHA_HOY}.")
