import { chromium } from 'playwright';

const baseURL = process.env.CREATOR_SMOKE_URL || 'http://127.0.0.1:4173/index.html?creatorTest=1';
const genders = {
  male: ['male_textured','male_short','male_medium','male_undercut','male_slick'],
  female: ['female_long','female_wavy','female_bob','female_ponytail','female_short'],
};
const skins = ['light','warm','medium','deep','dark'];
const colours = ['black','brown','blond','red','purple'];

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const failures = [];

page.on('pageerror', error => {
  // Supabase/network errors unrelated to the creator are ignored only when the
  // creator UI remains usable. Any creator assertion below will still fail.
  console.error('[pageerror]', error.message);
});

async function waitForLoadedImage(selector) {
  await page.waitForFunction(sel => {
    const img = document.querySelector(sel);
    return !!img && img.complete && img.naturalWidth > 0 && img.naturalHeight > 0;
  }, selector, { timeout: 15000 });
}

async function previewPath() {
  return page.locator('#creatorPreview img.creator-real-preview').getAttribute('src');
}

try {
  await page.goto(baseURL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('#creatorModal.show', { timeout: 15000 });
  await waitForLoadedImage('#creatorPreview img.creator-real-preview');

  for (const [gender, styles] of Object.entries(genders)) {
    await page.locator(`#genderChoices [data-value="${gender}"]`).click();

    for (const skin of skins) {
      await page.locator(`#skinChoices [data-value="${skin}"]`).click();

      for (const colour of colours) {
        await page.locator(`#hairColorChoices [data-value="${colour}"]`).click();

        const thumbs = page.locator('#hairStyleChoices .hair-choice');
        const count = await thumbs.count();
        if (count !== 5) failures.push(`${gender}/${skin}/${colour}: expected 5 hairstyle buttons, got ${count}`);

        for (const style of styles) {
          const button = page.locator(`#hairStyleChoices [data-value="${style}"]`);
          if (await button.count() !== 1) {
            failures.push(`${gender}/${skin}/${colour}: missing hairstyle button ${style}`);
            continue;
          }

          await button.click();
          await waitForLoadedImage('#creatorPreview img.creator-real-preview');

          const src = await previewPath();
          const expected = `assets/creator/${gender}/${skin}/${colour}/${style}.webp`;
          if (!src || !src.includes(expected)) failures.push(`${expected}: preview routed to ${src}`);

          const selected = await button.evaluate(el => el.classList.contains('selected'));
          if (!selected) failures.push(`${expected}: clicked hairstyle is not selected`);

          const thumb = button.locator('img');
          if (await thumb.count() !== 1) {
            failures.push(`${expected}: real thumbnail image missing`);
          } else {
            const thumbSrc = await thumb.getAttribute('src');
            if (!thumbSrc || !thumbSrc.includes(expected)) failures.push(`${expected}: thumbnail routed to ${thumbSrc}`);
            await page.waitForFunction(el => el.complete && el.naturalWidth > 0, await thumb.elementHandle(), { timeout: 15000 });
          }
        }
      }
    }
  }

  const overlayCount = await page.locator('.creator-skin-overlay,.creator-hair-overlay').count();
  if (overlayCount !== 0) failures.push(`legacy creator overlays present in DOM: ${overlayCount}`);

  const saveDisabled = await page.locator('#saveAvatar').isDisabled();
  if (saveDisabled) failures.push('saveAvatar remains disabled after valid preset loads');
} catch (error) {
  failures.push(error.stack || String(error));
} finally {
  await browser.close();
}

if (failures.length) {
  console.error('CREATOR RUNTIME SMOKE FAILED');
  for (const failure of failures) console.error(' -', failure);
  process.exit(1);
}

console.log('Creator runtime smoke passed: all 250 combinations route through real loaded preview/thumbnail assets with working controls and no overlays.');
