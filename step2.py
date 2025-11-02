import asyncio
import os
import json
import aiohttp
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

LOG_FILE = 'errors.txt'  # Used for both logs and errors here

async def log_message(message):
    print(message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

async def download_file(session, url, path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
                      "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Referer": "https://brunner-group.com/",  # Set to site domain to satisfy anti-hotlinking
    }
    try:
        await log_message(f"Starting download: {url}")
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                with open(path, 'wb') as f:
                    f.write(await resp.read())
                await log_message(f"Finished download: {url} -> {path}")
            else:
                raise Exception(f'HTTP status {resp.status}')
    except Exception as e:
        raise Exception(f'Download failed: {e}')


async def scrape_product(page, product):
    folder_name = f"{product['title'].replace(' ', '_')}_{product['variant'].replace(' ', '_')}"
    os.makedirs(folder_name, exist_ok=True)

    await log_message(f"Opening URL for product {folder_name}: {product['url']}")
    try:
        await page.goto(product['url'], wait_until='load', timeout=60000)
        await log_message(f"Successfully opened URL for product {folder_name}")
    except Exception as e:
        await log_message(f"[Navigation] Failed to open URL {product['url']} for product {folder_name}: {e}")
        return

    # Step 1: Download images
    try:
        await log_message(f"Extracting images for product {folder_name}...")
        await page.wait_for_selector("div.o-media-gallery__grid picture source", state='attached', timeout=30000)

        # Scroll down slowly to trigger lazy loading
        await page.evaluate("""
            async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 100;
                    const timer = setInterval(() => {
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if (totalHeight >= document.body.scrollHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 100);
                });
            }
        """)
        # img_sources = await page.eval_on_selector_all(
        #     "div.o-media-gallery__grid picture source",
        #     "elements => elements.map(e => e.srcset.split(',')[0].trim())"
        # )
        # await log_message(f"Found {len(img_sources)} images for product {folder_name}")

        raw_srcsets = await page.eval_on_selector_all(
            "div.o-media-gallery__grid picture source",
            "elements => elements.map(e => e.srcset)"
        )
        await log_message(f"Raw srcset values: {raw_srcsets}")

        # Then continue extracting first image URL safely if srcset exists
        img_sources = []
        for srcset in raw_srcsets:
            if srcset:
                first_url = srcset.split(',')[0].strip()
                img_sources.append(first_url)

        await log_message(f"Processed image URLs: {img_sources}")


        async with aiohttp.ClientSession() as session:
            for i, img_url in enumerate(img_sources):
                img_path = os.path.join(folder_name, f"image_{i + 1}.jpg")
                try:
                    await download_file(session, img_url, img_path)
                except Exception as e:
                    await log_message(f"[Image Download] Failed image {img_url} for product {folder_name}: {e}")
        await log_message(f"Completed image downloads for product {folder_name}")
    except Exception as e:
        await log_message(f"[Images Extraction] Failed for product {folder_name}: {e}")

    # Step 2: Extract Features
    try:
        features_html = await page.inner_html('#tab-0 > div > div > div:nth-child(1)')
        with open(os.path.join(folder_name, 'features.txt'), 'w', encoding='utf-8') as f:
            f.write(features_html)
    except Exception as e:
        await log_error(f"[Features Extraction] Failed for product {folder_name}: {e}")

    # Step 3: Download product sheet PDF
    try:
        await log_message(f"Downloading product sheet PDF for product {folder_name}...")
        await page.click('#tab-3 > button > span')
        await page.wait_for_selector('#tab-3 > div > div > div:nth-child(1) ul li a span span span', state='visible')
        pdf_url = await page.get_attribute('#tab-3 > div > div > div:nth-child(1) ul li a', 'href')
        if pdf_url:
            pdf_path = os.path.join(folder_name, 'product_sheet.pdf')
            async with aiohttp.ClientSession() as session:
                try:
                    await download_file(session, pdf_url, pdf_path)
                except Exception as e:
                    await log_message(f"[PDF Download] Failed for product {folder_name}: {e}")
            await log_message(f"Downloaded product_sheet.pdf for product {folder_name}")
        else:
            await log_message(f"[PDF Download] Product sheet link not found for product {folder_name}")
    except Exception as e:
        await log_message(f"[PDF Extraction] Failed for product {folder_name}: {e}")

async def main():
    # Clear log file before starting
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    with open('products.json', 'r', encoding='utf-8') as f:
        products = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        for product in products:
            await scrape_product(page, product)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
