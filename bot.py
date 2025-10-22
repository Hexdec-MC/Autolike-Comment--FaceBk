from playwright.sync_api import sync_playwright
import os, json, random, time, re

# ---------------- CONFIG ----------------
BRAVE_PATH = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
PERFIL_URL = "pon tu url de tu perfil"  # ⚠️ cambia solo esta URL
SESSION_DIR = os.path.abspath("fb_session")
JSON_COMENTARIOS = "comentarios.json"
JSON_ULTIMO = "ultimo_reel.json"
INTERVALO_SEGUNDOS = 30  # cada cuánto revisar (puedes poner 300 = 5 min)
# ----------------------------------------

def cargar_comentarios():
    if not os.path.exists(JSON_COMENTARIOS):
        print("⚠️ No se encontró el archivo comentarios.json.")
        return []
    with open(JSON_COMENTARIOS, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("comentarios", [])

def leer_ultimo_id():
    if os.path.exists(JSON_ULTIMO):
        with open(JSON_ULTIMO, "r") as f:
            data = json.load(f)
            return data.get("ultimo_id", "")
    return ""

def guardar_ultimo_id(reel_id):
    with open(JSON_ULTIMO, "w") as f:
        json.dump({"ultimo_id": reel_id}, f)

def limpiar_id(url):
    match = re.search(r'/reel/(\d+)', url)
    return match.group(1) if match else url

def procesar_reel(page, reel_id, comentarios):
    print(f"\n🎬 Procesando nuevo reel: {reel_id}")
    page.goto(f"https://www.facebook.com/reel/{reel_id}")
    page.wait_for_timeout(6000)

    # Like
    try:
        like_btn = page.locator("div[aria-label*='Me gusta']").first
        if like_btn:
            like_btn.click()
            print("👍 Me gusta aplicado.")
    except Exception as e:
        print(f"⚠️ Error al dar Me gusta: {e}")

    # Comentarios
    try:
        print("💬 Abriendo sección de comentarios...")
        posibles_botones = ["Comentarios", "Comentar", "Ver comentarios", "Mostrar comentarios"]
        for nombre in posibles_botones:
            btn = page.locator(f"div[aria-label*='{nombre}']").first
            if btn and btn.is_visible():
                btn.click()
                page.wait_for_timeout(3000)
                print(f"🪟 Panel abierto con '{nombre}'.")
                break

        # Buscar campo de comentario
        for intento in range(10):
            comment_box = page.locator(
                "div[contenteditable='true'], textarea, div[aria-label*='Escribe un comentario']"
            ).first
            if comment_box and comment_box.is_visible():
                print("✅ Campo de texto encontrado.")
                for i, mensaje in enumerate(comentarios, 1):
                    comment_box.click()
                    comment_box.type(mensaje)
                    comment_box.press("Enter")
                    print(f"💬 Comentario {i}/{len(comentarios)}: {mensaje}")
                    time.sleep(random.uniform(4, 8))  # pausa entre comentarios
                break
            else:
                print("🔄 Buscando campo de comentario...")
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(2000)
        else:
            print("❌ No se encontró el cuadro de comentarios visible.")
    except Exception as e:
        print(f"⚠️ Error al comentar: {e}")

    guardar_ultimo_id(reel_id)
    print("✅ Reel procesado correctamente.\n")

def main():
    comentarios = cargar_comentarios()
    if not comentarios:
        print("❌ No hay comentarios disponibles.")
        return

    print("🚀 Iniciando navegador Brave...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            executable_path=BRAVE_PATH,
        )
        page = browser.new_page()
        page.goto(PERFIL_URL)

        input("🔑 Inicia sesión en Facebook y presiona Enter para comenzar la vigilancia...")

        print("👀 Iniciando monitoreo automático de reels...")
        ultimo_id = leer_ultimo_id()

        while True:
            try:
                page.goto(PERFIL_URL)
                page.wait_for_timeout(5000)

                link = page.locator("a[href*='/reel/']").first
                if link:
                    reel_url = link.get_attribute("href")
                    reel_id = limpiar_id(reel_url)
                    if reel_id != ultimo_id:
                        procesar_reel(page, reel_id, comentarios)
                        ultimo_id = reel_id
                    else:
                        print(f"⏳ Sin nuevos reels. Revisando otra vez en {INTERVALO_SEGUNDOS}s...")
                else:
                    print("⚠️ No se encontró ningún reel visible.")

                time.sleep(INTERVALO_SEGUNDOS)
            except KeyboardInterrupt:
                print("\n🛑 Proceso detenido manualmente.")
                break
            except Exception as e:
                print(f"⚠️ Error en el ciclo principal: {e}")
                time.sleep(INTERVALO_SEGUNDOS)

        browser.close()

if __name__ == "__main__":
    main()
