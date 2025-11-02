const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// Helper function to sanitize folder names removing invalid characters
function sanitizeFolderName(name) {
  return name.replace(/[<>:"\/\\|?*\x00-\x1F]/g, '').replace(/\s+/g, '_');
}

// Download image function
function downloadImage(url, filepath) {
  const client = url.startsWith('https') ? https : http;
  return new Promise((resolve, reject) => {
    client.get(url, (res) => {
      if (res.statusCode === 200) {
        const fileStream = fs.createWriteStream(filepath);
        res.pipe(fileStream);
        fileStream.on('finish', () => fileStream.close(resolve));
      } else {
        reject(`Failed to get image: ${url} Status: ${res.statusCode}`);
      }
    }).on('error', reject);
  });
}

async function saveProductsImages() {
  try {
    // Read products.json file
    const data = fs.readFileSync(path.join(__dirname, 'chairs.json'), 'utf-8');
    const products = JSON.parse(data);

    for (const product of products) {
      const folderName = sanitizeFolderName(`${product.title}_${product.variant}`);
      const folderPath = path.join(__dirname, folderName);

      // Create folder if not exists
      if (!fs.existsSync(folderPath)) {
        fs.mkdirSync(folderPath);
      }

      // Extract image filename from URL
      const urlParts = product.image.split('/');
      let imageFilename = urlParts[urlParts.length - 1].split('?')[0];
      const savePath = path.join(folderPath, imageFilename);

      try {
        await downloadImage(product.image, savePath);
        console.log(`Saved image for ${folderName} -> ${imageFilename}`);
      } catch (err) {
        console.error(`Error saving image for ${folderName}:`, err);
      }
    }
  } catch (err) {
    console.error('Error reading products.json or parsing JSON', err);
  }
}

// Run the script
saveProductsImages();
