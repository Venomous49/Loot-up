class RiseLooterHead {
  element(element) {
    element.append('<link rel="stylesheet" href="/creator-hd.css?v=22">', { html: true });
    element.append('<script src="/creator-cache-v23.js?v=25" defer></script>', { html: true });
    // Independent creator-test fallback: must keep working even if the main app runtime fails.
    element.append('<script src="/safe-ui-bootstrap.js?v=11" defer></script>', { html: true });
  }
}

export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('text/html')) return response;
    const headers = new Headers(response.headers);
    headers.set('cache-control', 'no-store, no-cache, must-revalidate, max-age=0');
    headers.set('pragma', 'no-cache');
    headers.set('expires', '0');
    headers.set('x-riselooter-creator-source', 'validated');
    headers.set('x-riselooter-creator-version', 'dedicated-fullbody-v23');
    headers.set('x-riselooter-runtime-hotfixes', 'safe-bootstrap-v11-cache-loop-fix-v25');
    return new HTMLRewriter().on('head', new RiseLooterHead()).transform(new Response(response.body,{status:response.status,statusText:response.statusText,headers}));
  }
};
