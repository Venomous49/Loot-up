class RiseLooterHead {
  element(element) {
    element.append('<link rel="stylesheet" href="/creator-hd.css?v=4">', { html: true });
    element.append('<script src="/creator-safe-runtime.js?v=7" defer></script>', { html: true });
    element.append('<script src="/silhouette-fix.js?v=6" defer></script>', { html: true });
  }
}
export default {
  async fetch(request, env) {
    const response=await env.ASSETS.fetch(request);
    const contentType=response.headers.get('content-type')||'';
    if(!contentType.includes('text/html')) return response;
    const headers=new Headers(response.headers);
    headers.set('x-riselooter-creator-source','clean-source-masters-v7');
    headers.set('x-riselooter-silhouettes','character-cutout-v6');
    return new HTMLRewriter().on('head',new RiseLooterHead()).transform(new Response(response.body,{status:response.status,statusText:response.statusText,headers}));
  }
};
