// Cloudflare Worker: handle Codegen webhook callbacks at /webhook
// Deploy with Wrangler or Cloudflare dashboard. No external deps.
// Optionally set CODEGEN_WEBHOOK_SECRET in Worker secrets to verify HMAC.

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname !== '/webhook')
      return new Response('Not Found', { status: 404 });

    if (request.method !== 'POST')
      return new Response('Method Not Allowed', { status: 405 });

    // Read body
    const bodyText = await request.text();

    // Optional signature check
    const sig = request.headers.get('X-Codegen-Signature');
    const secret = env.CODEGEN_WEBHOOK_SECRET || '';
    if (secret) {
      const encoder = new TextEncoder();
      const key = await crypto.subtle.importKey(
        'raw', encoder.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
      );
      const mac = await crypto.subtle.sign('HMAC', key, encoder.encode(bodyText));
      const expected = [...new Uint8Array(mac)].map(b => b.toString(16).padStart(2,'0')).join('');
      if (!sig || sig !== expected) {
        return new Response('Invalid signature', { status: 401 });
      }
    }

    // Persist minimal event in KV (optional) or forward to your backend
    // Here, we simply log and return 200.
    console.log('Codegen webhook:', bodyText.slice(0, 500));

    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }
};

