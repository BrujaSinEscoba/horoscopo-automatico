import os
import requests
import json
import datetime
import pytz

# --- CONFIGURACIÓN DESDE GITHUB SECRETS ---
API_KEY_OPENAI = os.getenv("OPENAI_API_KEY")
WP_USER = os.getenv("WP_USER")
WP_PASS = os.getenv("WP_PASS")
WP_URL = "https://www.brujasinescoba.com/wp-json/wp/v2/pages"
PARENT_ID = 61

# Diccionario de imágenes de AI Puffer
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

# --- CONFIGURACIÓN DE FECHA (ZONA HORARIA MADRID) ---
tz_madrid = pytz.timezone('Europe/Madrid')
ahora_madrid = datetime.datetime.now(tz_madrid)
meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
FECHA_HOY = f"{ahora_madrid.day} de {meses[ahora_madrid.month - 1]} de {ahora_madrid.year}"

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
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")

def generar_contenido(signo):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_OPENAI}", "Content-Type": "application/json"}
    
    # PROMPT SIN PLANETAS (PARA EVITAR INVENTOS) Y CON EL ESTILO QUE TE GUSTA
    prompt = f"""Eres la 'Bruja Sin Escoba'. Escribe el horóscopo para el signo {signo} del día {FECHA_HOY}.
    
    INSTRUCCIONES DE ESTILO:
    1. No hables de posiciones planetarias ni fases lunares.
    2. Usa un lenguaje místico, sabio, directo y con un toque irónico o audaz (estilo con garra).
    3. Escribe en formato PLANO. NO uses asteriscos (**), ni almohadillas (###).
    4. Escribe la fecha {FECHA_HOY} al inicio en una línea sola.
    5. Usa exactamente estos títulos con sus emoticonos (sin negritas):
    
    🍏 Salud y Bienestar
    💰 Finanzas y Carrera
    ❤️ Amor y Relaciones
    🔮 Mensaje del Oráculo

    Estilo: 400 palabras, tono moderno y práctico. Sin introducciones ni despedidas."""

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def subir_a_wordpress(signo, contenido):
    # Imagen centrada
    url_img = IMAGENES_SIGNOS[signo]
    html_imagen = (
        f'<div style="text-align: center; margin-bottom: 25px;">'
        f'<img src="{url_img}" alt="Horóscopo {signo}" style="width: 100%; max-width: 450px; height: auto; border-radius: 15px;">'
        f'</div>'
    )
    
    # Generamos el link personalizado al horóscopo semanal/mensual
    signo_url = signo.lower().replace("é", "e").replace("á", "a").replace("ó", "o")
    link_final = (
        f'<div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;">'
        f'<p><b>Consulta el horóscopo completo de {signo} (semanal y mensual) aquí:</b></p>'
        f'<p><a href="https://www.brujasinescoba.com/horoscopos/horoscopo-{signo_url}/" target="_blank" rel="noopener">Horóscopo de {signo} completo</a></p>'
        f'</div>'
    )
    
    # Combinamos todo respetando saltos de línea para WordPress
    contenido_final = html_imagen + contenido.replace("\n", "<br>") + link_final
    
    slug = f"horoscopo-hoy-{signo_url}"
    
    payload = {
        "title": f"Horóscopo hoy {signo}",
        "content": contenido_final,
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
        print(f"🔮 Generando y publicando {signo}...")
        try:
            texto = generar_contenido(signo)
            subir_a_wordpress(signo, texto)
        except Exception as e:
            print(f"❌ Error con {signo}: {e}")
    
    print("\n✨ ¡Proceso finalizado con éxito!")
