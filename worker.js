class RiseLooterHead {
  element(element) {
    element.append('<link rel="stylesheet" href="/creator-hd.css?v=2">', { html: true });
    element.append('<script src="/creator-safe-runtime.js?v=1" defer></script>', { html: true });
    element.append('<script src="/silhouette-fix.js?v=1" defer></script>', { html: true });
  }
}

export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('text/html')) return response;

    const headers = new Headers(response.headers);
    headers.set('x-riselooter-creator-source', 'reviewed-source-runtime-v1');
    headers.set('x-riselooter-silhouettes', 'exact-master-v1');

    const html = new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });

    return new HTMLRewriter()
      .on('head', new RiseLooterHead())
      .transform(html);
  },
};
