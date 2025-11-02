import asyncio
import os
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re


LOG_FILE = 'errors.txt'  # Used for both logs and errors


async def log_message(message):
    print(message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(message + '\n')


async def scrape_product(page, product):
    folder_name = f"{product['title'].replace(' ', '_')}_{product['variant'].replace(' ', '_')}"
    os.makedirs(folder_name, exist_ok=True)

    await log_message(f"Opening URL for product {folder_name}: {product['url']}")
    try:
        await page.goto(product['url'], wait_until='domcontentloaded', timeout=60000)

        # Try to detect images, but don't fail if none found
        try:
            await page.wait_for_selector("div.o-media-gallery__grid picture source", state='attached', timeout=10000)
            await log_message(f"Images detected on page for {folder_name}, scrolling to load them...")

            # Scroll down to trigger lazy loading
            await page.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 200;
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
        except Exception:
            await log_message(f"[Info] No images detected for product {folder_name}, skipping image extraction step.")

        await log_message(f"Successfully opened URL for product {folder_name}")
    except Exception as e:
        await log_message(f"[Navigation] Failed to open URL {product['url']} for product {folder_name}: {e}")
        return

    # Step 1: Download images if available
    try:
        await log_message(f"Extracting images for product {folder_name}...")

        # ✅ Improved: pick highest-resolution image from each srcset
        img_sources = await page.eval_on_selector_all(
            "div.o-media-gallery__grid picture source",
            """
            elements => elements.map(e => {
                if (!e.srcset) return null;
                const parts = e.srcset.split(',').map(s => s.trim());
                const last = parts[parts.length - 1]; // usually highest resolution
                return last.split(' ')[0]; // remove width descriptor
            }).filter(src => src)
            """
        )

        if not img_sources:
            await log_message(f"[Info] No images found for product {folder_name}, skipping download step.")
        else:
            await log_message(f"Found {len(img_sources)} image(s) for product {folder_name}")

            for i, img_url in enumerate(img_sources):
                img_path = os.path.join(folder_name, f"image_{i + 1}.jpg")
                try:
                    await log_message(f"Starting download with Playwright: {img_url}")
                    response = await page.request.get(img_url)
                    if response.ok:
                        content = await response.body()
                        with open(img_path, 'wb') as f:
                            f.write(content)
                        await log_message(f"Finished download: {img_url} -> {img_path}")
                    else:
                        raise Exception(f"HTTP status {response.status}")
                except Exception as e:
                    await log_message(f"[Image Download] Failed image {img_url} for product {folder_name}: {e}")

            await log_message(f"Completed image downloads for product {folder_name}")
    except Exception as e:
        await log_message(f"[Images Extraction] Failed for product {folder_name}: {e}")

    # Step 2: Extract Features
    try:
        await log_message(f"Extracting features for product {folder_name}...")
        features_html = await page.inner_html('#tab-0 > div > div > div:nth-child(1)')
        with open(os.path.join(folder_name, 'features.txt'), 'w', encoding='utf-8') as f:
            f.write(features_html)
        await log_message(f"Features saved for product {folder_name}")
    except Exception as e:
        await log_message(f"[Features Extraction] Failed for product {folder_name}: {e}")

    # Step 3: Download product sheet PDF
    try:
        await log_message(f"Attempting to access Downloads tab for product {folder_name}...")

        # Click Downloads tab via script
        await page.evaluate("""
            () => {
                const buttons = Array.from(document.querySelectorAll('button.o-tabbed-content__item-trigger'));
                for (const btn of buttons) {
                    if (btn.textContent.trim().includes('Downloads')) {
                        btn.click();
                        break;
                    }
                }
            }
        """)

        # Wait for potential PDF link
        await page.wait_for_selector('#tab-3 > div > div > div:nth-child(1) ul li a span span span', state='visible', timeout=15000)

        pdf_url = await page.get_attribute('#tab-3 > div > div > div:nth-child(1) ul li a', 'href')
        if pdf_url:
            pdf_path = os.path.join(folder_name, 'product_sheet.pdf')
            try:
                await log_message(f"Starting download of PDF: {pdf_url}")
                response = await page.request.get(pdf_url)
                if response.ok:
                    content = await response.body()
                    with open(pdf_path, 'wb') as f:
                        f.write(content)
                    await log_message(f"Downloaded product_sheet.pdf for product {folder_name}")
                else:
                    raise Exception(f"HTTP status {response.status}")
            except Exception as e:
                await log_message(f"[PDF Download] Failed for product {folder_name}: {e}")
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
