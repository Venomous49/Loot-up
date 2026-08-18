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

async function assertSingleSelected(groupSelector, expectedValue, context) {
  const selected = page.locator(`${groupSelector} .choice.selected`);
  const count = await selected.count();
  if (count !== 1) {
    failures.push(`${context}: expected exactly one selected control in ${groupSelector}, got ${count}`);
    return;
  }
  const value = await selected.first().getAttribute('data-value');
  if (value !== expectedValue) {
    failures.push(`${context}: selected ${groupSelector} value is ${value}, expected ${expectedValue}`);
  }
}

try {
  await page.goto(baseURL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('#creatorModal.show', { timeout: 15000 });
  await waitForLoadedImage('#creatorPreview img.creator-real-preview');

  await assertSingleSelected('#genderChoices', 'male', 'initial creator state');
  await assertSingleSelected('#skinChoices', 'medium', 'initial creator state');
  await assertSingleSelected('#hairColorChoices', 'brown', 'initial creator state');
  await assertSingleSelected('#hairStyleChoices', 'male_textured', 'initial creator state');

  for (const [gender, styles] of Object.entries(genders)) {
    await page.locator(`#genderChoices [data-value="${gender}"]`).click();
    await assertSingleSelected('#genderChoices', gender, `${gender}: gender click`);
    await assertSingleSelected('#hairStyleChoices', styles[0], `${gender}: gender resets hairstyle`);

    for (const skin of skins) {
      await page.locator(`#skinChoices [data-value="${skin}"]`).click();
      await assertSingleSelected('#skinChoices', skin, `${gender}/${skin}: skin click`);

      for (const colour of colours) {
        await page.locator(`#hairColorChoices [data-value="${colour}"]`).click();
        await assertSingleSelected('#hairColorChoices', colour, `${gender}/${skin}/${colour}: hair-colour click`);

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
          await assertSingleSelected('#hairStyleChoices', style, `${gender}/${skin}/${colour}/${style}: hairstyle click`);
          await waitForLoadedImage('#creatorPreview img.creator-real-preview');

          const src = await previewPath();
          const expected = `assets/creator/${gender}/${skin}/${colour}/${style}.webp`;
          if (!src || !src.includes(expected)) failures.push(`${expected}: preview routed to ${src}`);

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

  const missingThumbs = await page.locator('#hairStyleChoices .hair-thumb-missing').count();
  if (missingThumbs !== 0) failures.push(`creator contains ${missingThumbs} missing hairstyle thumbnails after traversal`);

  const missingPreviewVisible = await page.locator('#creatorPreview .creator-asset-missing:visible').count();
  if (missingPreviewVisible !== 0) failures.push('creator fallback placeholder became visible during valid preset traversal');

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

console.log('Creator runtime smoke passed: all 250 combinations route through real loaded preview/thumbnail assets with coherent selected controls, working buttons, clean fallbacks and no overlays.');
