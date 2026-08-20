class RiseLooterHead {
  element(element) {
    element.append('<link rel="stylesheet" href="/creator-hd.css?v=22">', { html: true });
    element.append('<script src="/creator-cache-v23.js?v=23" defer></script>', { html: true });
    // Deterministic one-shot bootstrap only: no MutationObserver, no render loop.
    element.append('<script src="/safe-ui-bootstrap.js?v=9" defer></script>', { html: true });
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
    headers.set('x-riselooter-runtime-hotfixes', 'safe-bootstrap-v9');
    return new HTMLRewriter().on('head', new RiseLooterHead()).transform(new Response(response.body,{status:response.status,statusText:response.statusText,headers}));
  }
};
