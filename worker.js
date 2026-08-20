class RiseLooterHead {
  element(element) {
    // Keep only the validated creator assets. Runtime DOM hotfixes are disabled
    // because their MutationObservers can fight the page renderer and freeze UI.
    element.append('<link rel="stylesheet" href="/creator-hd.css?v=22">', { html: true });
    element.append('<script src="/creator-cache-v23.js?v=23" defer></script>', { html: true });
  }
}

export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('text/html')) return response;
    const headers = new Headers(response.headers);
    headers.set('x-riselooter-creator-source', 'validated');
    headers.set('x-riselooter-creator-version', 'dedicated-fullbody-v23');
    headers.set('x-riselooter-runtime-hotfixes', 'disabled');
    return new HTMLRewriter().on('head', new RiseLooterHead()).transform(new Response(response.body,{status:response.status,statusText:response.statusText,headers}));
  }
};
