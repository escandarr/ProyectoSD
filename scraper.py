import asyncio
from playwright.async_api import async_playwright
import json
import os

EVENTOS_FILE = "eventos2.jsonl"
MAX_EVENTOS = 10000
PAUSA_SEGUNDOS = 20

# Set para evitar duplicados en memoria temporal
eventos_guardados = set()

def contar_eventos_jsonl():
    if not os.path.exists(EVENTOS_FILE):
        return 0
    with open(EVENTOS_FILE, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)

def generar_id_unico(evento, tipo):
    # Generamos un ID compuesto por tipo, ciudad, calle y timestamp cercano si existe
    return f"{tipo}-{evento.get('city', '')}-{evento.get('street', '')}-{evento.get('pubMillis', '')}"

def guardar_como_jsonl(data):
    nuevos = 0
    jams = 0
    alerts = 0

    with open(EVENTOS_FILE, "a", encoding="utf-8") as f:
        for jam in data.get("jams", []):
            eid = generar_id_unico(jam, "jam")
            if eid not in eventos_guardados:
                f.write(json.dumps({"type": "jam", **jam}, ensure_ascii=False) + "\n")
                eventos_guardados.add(eid)
                nuevos += 1
                jams += 1

        for alert in data.get("alerts", []):
            eid = generar_id_unico(alert, "alert")
            if eid not in eventos_guardados:
                f.write(json.dumps({"type": "alert", **alert}, ensure_ascii=False) + "\n")
                eventos_guardados.add(eid)
                nuevos += 1
                alerts += 1

    print(f"✅ Agregados {nuevos} nuevos eventos ({jams} jams, {alerts} alerts)")
    return nuevos

async def intercept_georss_response(page):
    last_data = None

    async def handle_response(response):
        if '/api/georss' in response.url:
            try:
                json_data = await response.json()
                nonlocal last_data
                last_data = json_data
            except Exception as e:
                print(f"Error al procesar JSON: {e}")

    page.on("response", handle_response)
    await asyncio.sleep(10)
    return last_data

async def interact_with_page(page):
    try:
        await page.click(".waze-tour-tooltip__acknowledge", timeout=5000)
    except:
        pass

    try:
        for _ in range(3):
            await page.click(".leaflet-control-zoom-out")
            await asyncio.sleep(1)
    except:
        pass

async def run_scraper(playwright):
    browser = await playwright.firefox.launch(headless=False)
    page = await browser.new_page()
    await page.goto("https://www.waze.com/es-419/live-map", wait_until="load", timeout=0)
    await interact_with_page(page)

    data = await intercept_georss_response(page)
    await browser.close()

    if data:
        nuevos = guardar_como_jsonl(data)
        return nuevos
    else:
        print("⚠️ No se obtuvieron datos esta vez.")
        return 0

async def main():
    total_eventos = contar_eventos_jsonl()
    print(f"📊 Eventos actuales: {total_eventos}/{MAX_EVENTOS}")

    # Inicializar set de eventos ya guardados
    if os.path.exists(EVENTOS_FILE):
        with open(EVENTOS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    evento = json.loads(line)
                    eid = generar_id_unico(evento, evento.get("type", ""))
                    eventos_guardados.add(eid)
                except:
                    continue

    async with async_playwright() as playwright:
        while total_eventos < MAX_EVENTOS:
            nuevos = await run_scraper(playwright)
            total_eventos += nuevos
            print(f"📈 Total acumulado: {total_eventos}/{MAX_EVENTOS}")

            if total_eventos < MAX_EVENTOS:
                print(f"⏳ Esperando {PAUSA_SEGUNDOS} segundos...")
                await asyncio.sleep(PAUSA_SEGUNDOS)

    print("🎉 ¡Meta alcanzada! 10.000 eventos capturados.")

asyncio.run(main())
