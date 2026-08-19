class RiseLooterHead {
  element(element) {
    element.append('<link rel="stylesheet" href="/creator-hd.css?v=1">', { html: true });
  }
}

export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const contentType = response.headers.get('content-type') || '';

    if (!contentType.includes('text/html')) return response;

    // The authoritative creator presentation lives in creator-hd.css in the
    // repository. Inject only that source-owned stylesheet so every deployed
    // page uses the same canonical 1728x910 preview geometry.
    const headers = new Headers(response.headers);
    headers.set('x-riselooter-creator-source', 'validated');

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
