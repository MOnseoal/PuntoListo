/* Service worker mínimo de PuntoListo.
   Permite instalar la app en el teléfono. No guarda páginas en caché
   (los datos siempre vienen frescos de Supabase); si no hay internet,
   muestra un aviso claro en lugar del error del navegador. */
self.addEventListener("install", function () { self.skipWaiting(); });
self.addEventListener("activate", function (e) { e.waitUntil(self.clients.claim()); });

self.addEventListener("fetch", function (evento) {
  if (evento.request.mode !== "navigate") return;   // solo páginas, lo demás va directo
  evento.respondWith(
    fetch(evento.request).catch(function () {
      return new Response(
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
        '<title>Sin conexión · PuntoListo</title>' +
        '<body style="font-family:system-ui;padding:2rem;text-align:center;color:#374151">' +
        '<h1 style="font-size:1.3rem">Sin conexión</h1>' +
        '<p>PuntoListo necesita internet para guardar tus órdenes.<br>Revisa tu WiFi o datos y vuelve a intentar.</p>' +
        '<button onclick="location.reload()" style="padding:.7rem 1.2rem;border-radius:.4rem;border:0;background:#1f2937;color:#fff">Reintentar</button>',
        { headers: { "Content-Type": "text/html; charset=utf-8" } }
      );
    })
  );
});
