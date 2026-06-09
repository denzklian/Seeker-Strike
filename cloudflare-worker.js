const TUNNEL_URL = 'https://YOUR_TUNNEL_URL.lhr.life';

const BLOCKED_UA = [
  'zgrab', 'masscan', 'nmap', 'censys', 'shodan',
  'internet-measurement', 'project25499',
];

function extractVisitLink(html) {
  const hrefMatch = html.match(/href\s*=\s*["']([^"']*\?[^"']*)["']/i);
  if (hrefMatch) {
    let href = hrefMatch[1];
    if (href.startsWith('/')) {
      href = new URL(TUNNEL_URL).origin + href;
    }
    return href;
  }
  const btnMatch = html.match(/window\.location\s*=\s*["']([^"']+)["']/);
  if (btnMatch) return btnMatch[1];
  const actionMatch = html.match(/action\s*=\s*["']([^"']+)["']/i);
  if (actionMatch) {
    let action = actionMatch[1];
    if (action.startsWith('/')) {
      action = new URL(TUNNEL_URL).origin + action;
    }
    return action;
  }
  return null;
}

function isHtmlResponse(response) {
  const ct = response.headers.get('Content-Type') || '';
  return ct.includes('text/html') || ct.includes('text/plain');
}

async function handleRequest(request) {
  const url = new URL(request.url);
  const ua = request.headers.get('User-Agent') || '';

  if (BLOCKED_UA.some(b => ua.toLowerCase().includes(b))) {
    return new Response('Not Found', { status: 404 });
  }

  const tunnelHost = new URL(TUNNEL_URL).host;
  const targetUrl = TUNNEL_URL + url.pathname + url.search;

  const proxyHeaders = new Headers(request.headers);
  proxyHeaders.set('Host', tunnelHost);
  proxyHeaders.set('X-Forwarded-For', request.headers.get('CF-Connecting-IP') || '');
  proxyHeaders.set('ngrok-skip-browser-warning', 'true');
  proxyHeaders.delete('cf-ray');
  proxyHeaders.delete('cf-visitor');
  proxyHeaders.delete('cdn-loop');
  proxyHeaders.delete('cf-connecting-ip');
  proxyHeaders.delete('cf-ipcountry');
  proxyHeaders.delete('cf-worker');
  proxyHeaders.delete('true-client-ip');

  const init = {
    method: request.method,
    headers: proxyHeaders,
    redirect: 'manual',
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = await request.clone().arrayBuffer();
  }

  try {
    let response = await fetch(new Request(targetUrl, init));

    if (response.status >= 300 && response.status < 400) {
      const location = response.headers.get('Location');
      if (location) {
        const redirectUrl = location.startsWith('http') ? location : TUNNEL_URL + location;
        response = await fetch(new Request(redirectUrl, { ...init, redirect: 'manual' }));
      }
    }

    if (!isHtmlResponse(response)) {
      const h = new Headers(response.headers);
      h.set('Access-Control-Allow-Origin', '*');
      h.delete('X-Frame-Options');
      h.delete('Content-Security-Policy');
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: h,
      });
    }

    const text = await response.text();

    const isInterstitial = (
      text.includes('<title>ngrok</title>') ||
      text.includes('ngrok.com/tos') ||
      text.includes('skip-browser-warning') ||
      (text.includes('ngrok') && text.includes('Visit Site'))
    );

    if (isInterstitial) {
      const visitLink = extractVisitLink(text);
      if (visitLink) {
        const cookieHeaders = new Headers(proxyHeaders);
        cookieHeaders.set('Cookie', 'ngrok-skip-browser-warning=true');

        const followResp = await fetch(visitLink, {
          method: 'GET',
          headers: cookieHeaders,
          redirect: 'manual',
        });

        let finalText;
        if (followResp.status >= 300 && followResp.status < 400) {
          const loc = followResp.headers.get('Location');
          if (loc) {
            const finalUrl = loc.startsWith('http') ? loc : TUNNEL_URL + loc;
            const finalResp = await fetch(finalUrl, {
              method: 'GET',
              headers: proxyHeaders,
              redirect: 'follow',
            });
            finalText = await finalResp.text();
          } else {
            finalText = await followResp.text();
          }
        } else {
          finalText = await followResp.text();
        }

        const h = new Headers(followResp.headers);
        h.set('Access-Control-Allow-Origin', '*');
        h.delete('X-Frame-Options');
        h.delete('Content-Security-Policy');
        h.delete('server');
        return new Response(finalText, {
          status: 200,
          headers: h,
        });
      }

      return new Response(text, {
        status: 200,
        headers: {
          'Content-Type': 'text/html;charset=UTF-8',
          'Access-Control-Allow-Origin': '*',
        },
      });
    }

    const h = new Headers(response.headers);
    h.set('Access-Control-Allow-Origin', '*');
    h.delete('X-Frame-Options');
    h.delete('Content-Security-Policy');
    h.delete('server');
    return new Response(text, {
      status: response.status,
      statusText: response.statusText,
      headers: h,
    });
  } catch (err) {
    const tunnelHostClean = new URL(TUNNEL_URL).host;
    return new Response(
      `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Connection Error</title>
<style>body{background:#111;color:#eee;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.e{background:#1a1a2e;padding:2rem;border-radius:12px;border:1px solid #333;max-width:420px;text-align:center}
h2{color:#ef4444}p{color:#94a3b8;font-size:14px;margin:8px 0}
pre{background:#0f0f23;padding:8px;border-radius:6px;font-size:11px;color:#a78bfa;text-align:left;overflow-x:auto;max-height:120px}
.tip{margin-top:1rem;padding:.75rem;background:#1e293b;border-radius:8px;font-size:13px;color:#6366f1}
a{color:#818cf8}</style>
</head><body><div class="e"><h2>Server Not Available</h2><p>Ngrok tunnel tidak merespon.</p>
<pre>target: ${tunnelHostClean}</pre>
<pre>error: ${String(err).slice(0, 200)}</pre>
<div class="tip">Pastikan ngrok + PHP server jalan di localhost:8080.<br>Bisa juga tunnel URL berubah (redeploy worker).</div></div></body></html>`,
      {
        status: 502,
        headers: {
          'Content-Type': 'text/html;charset=UTF-8',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  }
}

function handleOptions() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
      'Access-Control-Max-Age': '86400',
    },
  });
}

addEventListener('fetch', event => {
  if (event.request.method === 'OPTIONS') {
    event.respondWith(handleOptions());
  } else {
    event.respondWith(handleRequest(event.request));
  }
});
