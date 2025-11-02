I ran this code in chrome devtools on all products page (loaded al chairs by scrolling page)
[...document.querySelectorAll('.column .m-card-sm.h-link')].map(card => ({
  url: card.href,
  image: card.querySelector('img.a-image__tag')?.src,
  title: card.querySelector('.h-link__text-line')?.textContent?.trim(),
  variant: card.querySelector('h4.h-mini')?.textContent?.trim()
}))

this gives an json. (chairs.json)

Step2: creating script to create folders and download image for each product
downloadImages.js

Step3: downloading other images for product, saving features and download product sheet.
Prompt to AI:
I have products array like below:
{
        "url": "https://brunner-group.com/en/products/window-reclining-chair/?variant=3456",
        "image": "https://live-brunner.pantheonsite.io/sites/default/files/styles/sm/public/oldImages/63574_lm_product_grid_0010_window_3456V_XL.jpg.webp?itok=aJWQuKwO",
        "title": "window",
        "variant": "reclining chair 3456"
    }

I want a script to iterate and open all urls one by one and copy/extract the following details.
1. download images present as part of selector "//div[contains(@class, 'o-media-gallery__grid')]//picture/source[1]". There can be multiple images downloadd all and save it to folders in the workspace. Folder name is title_variant from the json object.
2. Copy the features from the website under selector "//*[@id="tab-0"]/div/div/div[1]". There will be some headers,paragraphs, ul under this copy and save those in a features.txt file under foldername for that product. Folder name is title_variant from the json object.
3. We hae to download product sheet for this product. Click on button with selector "#tab-3 > button > span". There will be a pdf file named Product data sheet. download this file to the same products folder. Folder name is title_variant from the json object.
Usually the selector for this file to be downloaded would be "#tab-3 > div > div > div:nth-child(1) > ul > li:nth-child(1) > a > span > span > span"




Final Steps:
Step 1: I ran this code in chrome devtools on all products page (loaded al chairs by scrolling page)
[...document.querySelectorAll('.column .m-card-sm.h-link')].map(card => ({
  url: card.href,
  image: card.querySelector('img.a-image__tag')?.src,
  title: card.querySelector('.h-link__text-line')?.textContent?.trim(),
  variant: card.querySelector('h4.h-mini')?.textContent?.trim()
}))
this gives an json. (chairs.json)

Step 2: D:\Palak\step2-v1.py
Run this script
this script will open all products one by one from above chairs.json file
create folder, download all images and product sheet, and save features.txt file
features.txt are saved as html elementsonly for now.

Step 3: D:\Palak\convertFeatureText.py
Run this to convert all features to text format

Step 4: D:\Palak\moveProductSheetsTosinglefolder.py
Move pdf files and features.txt to another folder for notebook llm to process and create markdown files

```
Notebook LLM prompt:
this product sheet has details about a product. A product can have multiple models. I want you to extract the following details for me for each subtype and create a markdown file for me.
Also there is a productname.txt file that has features listed for each product. Can you add that along with data from product sheet as well.


Product name/type
Model no
Features (from txt file)
Seat/Seat shell
frame
standard finish
options and accessories
upholestry
colours
dimensions


if you find any other useful info, extract that as well under suitable heading
```

errors.txt -> has logging details incase there are any failures

TODO/Enhancements:
Currently script fails if there are no images on website. We should be able to skip downloading images in that case.


pip install playwright
python -m playwright install
pip install beautifulsoup4

Occasional/Tables script has these versions:
one has optional check for gallery to continue if there are no images on website
other has check to see if there are also high quality images