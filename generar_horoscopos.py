import os
import requests
import json
import datetime
import pytz  # Librería para que la fecha siempre sea la de España

# --- CONFIGURACIÓN ---
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

# --- CÁLCULO DE LA FECHA EN ESPAÑA ---
# Esto evita que si GitHub corre a las 00:01 ponga la fecha de ayer
tz_espana = pytz.timezone('Europe/Madrid')
ahora_espana = datetime.datetime.now(tz_espana)
meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
FECHA_HOY = f"{ahora_espana.day} de {meses[ahora_espana.month - 1]} de {ahora_espana.year}"

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
    
    # PROMPT MEJORADO PARA EVITAR REPETICIONES Y TEXTOS PLANOS
    prompt = f"""Escribe el horóscopo para el signo {signo} para el día {FECHA_HOY}.
    
    INSTRUCCIONES DE ESTILO CRUCIALES:
    1. Eres la 'Bruja Sin Escoba': sabia, directa, un poco mística y nada predecible.
    2. EVITA frases trilladas como 'hoy es un buen día para', 'escucha a tu cuerpo' o 'la comunicación es clave'. Sé más original y audaz.
    3. Escribe en formato PLANO. NO uses asteriscos (**), ni almohadillas (###), ni Markdown.
    4. Escribe la fecha {FECHA_HOY} al inicio en una línea sola.
    5. Usa exactamente estos títulos con sus emoticonos (sin negritas):
    
    🍏 Salud y Bienestar
    💰 Finanzas y Carrera
    ❤️ Amor y Relaciones
    🔮 Mensaje del Oráculo

    Estilo: 400 palabras, tono moderno, directo y práctico. 
    No añadas introducciones ni despedidas."""

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85  # Más creatividad para evitar que los textos sean iguales cada día
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def subir_a_wordpress(signo, contenido):
    # Lógica de la imagen centrada
    url_img = IMAGENES_SIGNOS[signo]
    alt_text = f"Ilustración del signo {signo} - Bruja Sin Escoba"
    
    html_imagen = (
        f'<div style="text-align: center; margin-bottom: 25px;">'
        f'<img src="{url_img}" alt="{alt_text}" style="width: 100%; max-width: 450px; height: auto; border-radius: 15px;">'
        f'</div>'
    )
    
    # Combinamos imagen + texto (respetando saltos de línea para WordPress)
    contenido_final = html_imagen + contenido.replace("\n", "<br>")
    
    # Generamos el slug quitando tildes
    slug = f"horoscopo-hoy-{signo.lower()}".replace("é", "e").replace("á", "a").replace("ó", "o")
    
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

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    limpieza_total_segura()
    
    for signo in SIGNOS:
        print(f"🔮 Generando y publicando {signo}...")
        try:
            texto = generar_contenido(signo)
            subir_a_wordpress(signo, texto)
        except Exception as e:
            print(f"❌ Error crítico con {signo}: {e}")
    
    print("\n✨ ¡Proceso finalizado con éxito!")
