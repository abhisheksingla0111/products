from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv
import time

URL = "https://brunner-group.com/en/products/chairs-and-seating-furniture"
LOAD_MORE_SELECTOR = "#__nuxt > div.l-default.l-app > div > main > section.section--default.section--spacing.section > div > div > div > div.container.o-product-grid__footer > div > div:nth-child(1) > button > span > span"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, timeout=0)
    page.wait_for_selector(".grid.o-product-grid__grid .column")

    print("🟢 Page loaded, starting to click 'Load more'...")

    # Keep clicking "Load more" until it's gone
    while True:
        try:
            button = page.locator(LOAD_MORE_SELECTOR)
            if button.is_visible():
                button.scroll_into_view_if_needed()
                button.click()
                print("🔁 Clicked 'Load more'... waiting for new items.")
                time.sleep(3)  # wait for new products to load
            else:
                print("✅ No more 'Load more' button.")
                break
        except Exception as e:
            print(f"⚠️ Error or no button found: {e}")
            break

    html = page.content()
    browser.close()

print("📄 Extracting product data...")

soup = BeautifulSoup(html, "html.parser")

products = []
for column in soup.select('.grid.o-product-grid__grid .column'):
    a_tag = column.find('a', class_='m-card-sm')
    if not a_tag:
        continue

    product = {
        "name": a_tag.select_one('.h-link__text-line').get_text(strip=True),
        "description": a_tag.select_one('.h-mini').get_text(strip=True),
        "url": a_tag['href'],
        "image": a_tag.select_one('img.a-image__tag')['src']
    }
    products.append(product)

# Save to CSV
with open("products.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "description", "url", "image"])
    writer.writeheader()
    writer.writerows(products)

print(f"✅ Done! Saved {len(products)} products to products.csv")
