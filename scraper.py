import asyncio
from playwright.async_api import async_playwright
import json

async def intercept_georss_response(page):
    last_data = None

    async def handle_response(response):
        if '/api/georss' in response.url:
            try:
                json_data = await response.json()
                print("Datos de tráfico capturados:")
                print(json.dumps(json_data, indent=2, ensure_ascii=False))
                nonlocal last_data
                last_data = json_data
            except Exception as e:
                print(f"Error al procesar JSON de {response.url}: {e}")

    page.on("response", handle_response)

    #Esperar para que aparezcan peticiones
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

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.waze.com/es-419/live-map", wait_until="load", timeout=0)

        await interact_with_page(page)
        data = await intercept_georss_response(page)

        if data:
            with open("eventos.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Datos guardados en eventos.json")

        await browser.close()

asyncio.run(main())
