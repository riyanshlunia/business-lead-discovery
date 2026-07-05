import asyncio
from playwright.async_api import async_playwright
import re

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # Navigate to a known business on Google Maps
        await page.goto("https://www.google.com/maps/place/Digital+Marketing+Agency/@51.5072178,-0.1275862,15z/data=!3m1!4b1!4m6!3m5!1s0x487604ce32b00001:0x5e0f7e9154a43d9b!8m2!3d51.507218!4d-0.127586!16s%2Fg%2F11b6x_y9_y?entry=ttu", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        for label in ["Accept all", "I agree", "Reject all"]:
            loc = page.get_by_role("button", name=label)
            if await loc.count():
                await loc.first.click()
                break
                
        await page.wait_for_timeout(2000)
        
        panel = page.locator('div[role="main"]').first
        if await panel.count() == 0:
            panel = page.locator('div[class*="m6QErb"], div[class*="widget-pane"]').first
        
        text = await panel.inner_text()
        print("--- PANEL TEXT ---")
        print(text[:1000])
        
        # Rating extraction
        match = re.search(r'(\d[\.,]\d)\s*\((\d[\d,]*)\)', text)
        print("Rating:", match)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
