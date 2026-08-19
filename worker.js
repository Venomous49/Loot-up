const CREATOR_FALLBACK_NEW = `function creatorFallbackPath(gender=avatarDraft.gender,skin=avatarDraft.skin,hairColor=avatarDraft.hairColor){
  const style = gender === "female" ? "female_long" : "male_textured";
  return creatorAssetPath({gender,skin,hairColor,hairStyle:style});
}`;

const CHARACTER_FALLBACK_NEW = `const fallback=stage===0
  ? creatorFallbackPath(gender, profile?.avatar_skin || "medium", profile?.avatar_hair_color || "brown")
  : fallbackAssetPath(stage);`;

const PREVIEW_ONLOAD_NEW = `onload="document.getElementById('saveAvatar').disabled=this.dataset.triedFallback==='1'"`;

function hardenCreatorHtml(html) {
  let hardened = html;

  // Keep the selected gender, skin tone and hair colour if only the hairstyle
  // asset needs to fall back. The regexp intentionally tolerates whitespace and
  // formatting changes in index.html so edge hardening cannot silently vanish
  // after a harmless reformat.
  if (!/function\s+creatorFallbackPath\([^)]*skin=avatarDraft\.skin[^)]*hairColor=avatarDraft\.hairColor/.test(hardened)) {
    hardened = hardened.replace(
      /function\s+creatorFallbackPath\(gender\s*=\s*avatarDraft\.gender\)\s*\{\s*const\s+style\s*=\s*gender\s*===\s*["']female["']\s*\?\s*["']female_long["']\s*:\s*["']male_textured["']\s*;\s*return\s+creatorAssetPath\(\{\s*gender\s*,\s*skin\s*:\s*["']medium["']\s*,\s*hairColor\s*:\s*["']brown["']\s*,\s*hairStyle\s*:\s*style\s*\}\)\s*;\s*\}/m,
      CREATOR_FALLBACK_NEW,
    );
  }

  if (!/creatorFallbackPath\(gender\s*,\s*profile\?\.avatar_skin/.test(hardened)) {
    hardened = hardened.replace(
      /const\s+fallback\s*=\s*stage\s*===\s*0\s*\?\s*creatorFallbackPath\(gender\)\s*:\s*fallbackAssetPath\(stage\)\s*;/m,
      CHARACTER_FALLBACK_NEW,
    );
  }

  if (!/disabled\s*=\s*this\.dataset\.triedFallback\s*===\s*["']1["']/.test(hardened)) {
    hardened = hardened.replace(
      /onload\s*=\s*["']document\.getElementById\(["']saveAvatar["']\)\.disabled\s*=\s*false["']/m,
      PREVIEW_ONLOAD_NEW,
    );
  }

  return hardened;
}

export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    if (request.method === 'HEAD') return response;

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('text/html')) return response;

    const html = await response.text();
    const hardened = hardenCreatorHtml(html);
    const headers = new Headers(response.headers);
    headers.delete('content-length');
    headers.set('x-riselooter-creator-hardening', '1');

    return new Response(hardened, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};
