export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const contentType = response.headers.get('content-type') || '';

    if (!contentType.includes('text/html')) return response;

    // Creator routing and fallbacks are validated directly in index.html.
    // The Worker must remain a transparent transport layer so production can
    // never diverge from the reviewed source through hidden HTML rewrites.
    const headers = new Headers(response.headers);
    headers.set('x-riselooter-creator-source', 'validated');

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};
