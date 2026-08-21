class RiseLooterHead {
  element(element) {
    element.append('<link rel="stylesheet" href="/creator-hd.css?v=23">', { html: true });
    element.append('<script src="/creator-cache-v23.js?v=27" defer></script>', { html: true });
    element.append('<script src="/safe-ui-bootstrap.js?v=layered-v4-fit1" defer></script>', { html: true });
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
    headers.set('x-riselooter-creator-source', 'layered-v4-clean-source');
    headers.set('x-riselooter-creator-version', 'layered-v4-fit1-cachefix27');
    headers.set('x-riselooter-runtime-hotfixes', 'safe-bootstrap-layered-v4-fit1-cachefix27');
    return new HTMLRewriter().on('head', new RiseLooterHead()).transform(new Response(response.body,{status:response.status,statusText:response.statusText,headers}));
  }
};
