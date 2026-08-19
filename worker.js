class RiseLooterHead {
  element(element) {
    element.append('<link rel="stylesheet" href="/creator-hd.css?v=2">', { html: true });
    element.append('<script src="/creator-safe-runtime.js?v=6" defer></script>', { html: true });
    element.append('<script src="/silhouette-fix.js?v=2" defer></script>', { html: true });
  }
}
export default {
  async fetch(request, env) {
    const response=await env.ASSETS.fetch(request);
    const contentType=response.headers.get('content-type')||'';
    if(!contentType.includes('text/html')) return response;
    const headers=new Headers(response.headers);
    headers.set('x-riselooter-creator-source','validated');
    headers.set('x-riselooter-creator-runtime','webp-matrix-runtime-v6');
    headers.set('x-riselooter-silhouettes','exact-master-v2');
    return new HTMLRewriter().on('head',new RiseLooterHead()).transform(new Response(response.body,{status:response.status,statusText:response.statusText,headers}));
  }
};
