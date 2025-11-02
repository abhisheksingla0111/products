const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');
const axios = require('axios');

const productsFilePath = path.join(__dirname, 'chairs.json');

// Read and parse products array from JSON file
const products = JSON.parse(fs.readFileSync(productsFilePath, 'utf-8'));

async function downloadFile(fileUrl, outputLocationPath) {
  const writer = fs.createWriteStream(outputLocationPath);
  const response = await axios({
    url: fileUrl,
    method: 'GET',
    responseType: 'stream'
  });
  response.data.pipe(writer);
  return new Promise((resolve, reject) => {
    writer.on('finish', resolve);
    writer.on('error', reject);
  });
}

(async () => {
  const browser = await puppeteer.launch({ headless: false });

  for (let product of products) {
    const folderName = `${product.title.replace(/ /g, '_')}_${product.variant.replace(/ /g, '_')}`;
    fs.mkdirSync(folderName, { recursive: true });

    const page = await browser.newPage();
    await page.goto(product.url, { waitUntil: 'networkidle2' });

    // 1. Download all images from selector
    const imgSources = await page.$$eval(
      "div.o-media-gallery__grid picture source",
      sources => sources.map(src => src.srcset.split(',')[0])
    );
    for (let [i, imgUrl] of imgSources.entries()) {
      const imgPath = path.join(folderName, `image_${i + 1}.jpg`);
      await downloadFile(imgUrl, imgPath);
    }

    // 2. Copy features content
    const featuresHtml = await page.$eval(
      '#tab-0 > div > div > div:nth-child(1)',
      el => el.innerHTML
    );
    fs.writeFileSync(path.join(folderName, 'features.txt'), featuresHtml);

    // 3. Download Product Sheet PDF
    await page.click('#tab-3 > button > span');
    await page.waitForSelector('#tab-3 > div > div > div:nth-child(1) ul li a span span span', { visible: true });
    const pdfUrl = await page.$eval(
      '#tab-3 > div > div > div:nth-child(1) ul li a',
      el => el.href
    );
    const pdfPath = path.join(folderName, 'product_sheet.pdf');
    await downloadFile(pdfUrl, pdfPath);

    await page.close();
  }

  await browser.close();
})();
