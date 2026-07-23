const puppeteerExtra = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

puppeteerExtra.use(StealthPlugin());

const TARGET_URL = 'https://charhub.ai/characters/30795';
const HEADLESS = false; // Kept false as requested for manual inspection
const CLOSE_BROWSER = false;

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

function getExecutablePath() {
  if (fs.existsSync(CHROME_PATH)) return CHROME_PATH;
  if (fs.existsSync(EDGE_PATH)) return EDGE_PATH;
  return undefined;
}

(async () => {
  console.log('[START] Launching Puppeteer...');
  
  const executablePath = getExecutablePath();
  console.log(`[INFO] Using executable: ${executablePath || 'default puppeteer bundle'}`);

  let browser;
  try {
    browser = await puppeteerExtra.launch({
      executablePath,
      headless: HEADLESS,
      defaultViewport: null,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--start-maximized',
      ],
    });

    console.log('[INFO] Browser window opened. Navigating to page...');
    const pages = await browser.pages();
    const page = pages.length > 0 ? pages[0] : await browser.newPage();

    await page.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );

    console.log(`[INFO] Navigating to ${TARGET_URL}...`);
    await page.goto(TARGET_URL, {
      waitUntil: 'domcontentloaded',
      timeout: 90000,
    });

    console.log('[INFO] Waiting for page content...');
    
    // Poll until character page is loaded and "aboutMe" is extracted
    let data = null;
    const maxAttempts = 60; // wait up to 60s
    for (let i = 1; i <= maxAttempts; i++) {
      data = await page.evaluate(() => {
        const h2 = document.querySelector('h2');
        if (!h2) return null;
        const text = h2.innerText.trim();
        if (
          text.toLowerCase().includes('security') ||
          text.toLowerCase().includes('segurança') ||
          text.toLowerCase().includes('just a moment')
        ) {
          return null;
        }

        // 1. Character Name
        const name = text;

        // 2. Character Image
        const imgEl = document.querySelector('div.aspect-w-1 img, img.object-cover, img[src*="active_storage"]');
        const image = imgEl ? imgEl.src : null;

        // 3. Character "About Me" / Description
        let aboutMe = null;
        const creatorLink = Array.from(document.querySelectorAll('a[href^="/users/"]')).find((a) => {
          const parentDiv = a.closest('div');
          return parentDiv && parentDiv.textContent.includes('Creator:');
        });

        if (creatorLink) {
          const creatorDiv = creatorLink.closest('div');
          if (creatorDiv && creatorDiv.nextElementSibling) {
            aboutMe = creatorDiv.nextElementSibling.innerText.trim();
          }
        }

        return { name, image, aboutMe };
      });

      if (data && data.name && data.aboutMe) {
        console.log(`[SUCCESS] Character page data scraped on attempt #${i}!`);
        break;
      }

      await new Promise((r) => setTimeout(r, 1000));
    }

    if (data) {
      console.log('\n================ SCRAPED DATA ================');
      console.log('Name:', data.name);
      console.log('Image:', data.image);
      console.log('About Me:', data.aboutMe);
      console.log('==============================================\n');
    } else {
      console.log('[WARN] Could not locate complete character data after wait period.');
    }

  } catch (error) {
    console.error('[ERROR] Scraping failed:', error);
  } finally {
    if (CLOSE_BROWSER && browser) {
      await browser.close();
      console.log('[FINISH] Browser closed.');
    } else {
      console.log('[INFO] Browser left open for your manual inspection.');
    }
  }
})();