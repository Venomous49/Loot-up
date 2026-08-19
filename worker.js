const CREATOR_FALLBACK_OLD = `function creatorFallbackPath(gender=avatarDraft.gender){
  const style = gender === "female" ? "female_long" : "male_textured";
  return creatorAssetPath({gender,skin:"medium",hairColor:"brown",hairStyle:style});
}`;

const CREATOR_FALLBACK_NEW = `function creatorFallbackPath(gender=avatarDraft.gender,skin=avatarDraft.skin,hairColor=avatarDraft.hairColor){
  const style = gender === "female" ? "female_long" : "male_textured";
  return creatorAssetPath({gender,skin,hairColor,hairStyle:style});
}`;

const CHARACTER_FALLBACK_OLD = `const fallback=stage===0
  ? creatorFallbackPath(gender)
  : fallbackAssetPath(stage);`;

const CHARACTER_FALLBACK_NEW = `const fallback=stage===0
  ? creatorFallbackPath(gender, profile?.avatar_skin || "medium", profile?.avatar_hair_color || "brown")
  : fallbackAssetPath(stage);`;

const PREVIEW_ONLOAD_OLD = `onload="document.getElementById('saveAvatar').disabled=false"`;
const PREVIEW_ONLOAD_NEW = `onload="document.getElementById('saveAvatar').disabled=this.dataset.triedFallback==='1'"`;

function hardenCreatorHtml(html) {
  return html
    .replace(CREATOR_FALLBACK_OLD, CREATOR_FALLBACK_NEW)
    .replace(CHARACTER_FALLBACK_OLD, CHARACTER_FALLBACK_NEW)
    .replace(PREVIEW_ONLOAD_OLD, PREVIEW_ONLOAD_NEW);
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

    return new Response(hardened, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};
