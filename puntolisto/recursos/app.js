/* PuntoListo · mejoras de uso. La app funciona igual sin JavaScript;
   esto solo la hace más rápida y evita errores con internet lento. */
(function () {
  "use strict";

  // 1. Respuesta inmediata: al enviar un formulario, el botón muestra "Guardando…"
  //    y se bloquea para evitar órdenes duplicadas por doble toque.
  document.addEventListener("submit", function (evento) {
    var formulario = evento.target;
    var boton = evento.submitter || formulario.querySelector("button[type=submit], button:not([type])");
    if (!boton || formulario.method.toLowerCase() !== "post") return;
    if (formulario.dataset.enviando === "1") { evento.preventDefault(); return; }
    formulario.dataset.enviando = "1";
    boton.setAttribute("aria-busy", "true");
    boton.dataset.textoOriginal = boton.textContent;
    if (!boton.classList.contains("accion")) boton.textContent = "Guardando…";
    setTimeout(function () { boton.disabled = true; }, 0);  // después de que el navegador tome el envío
  });

  // Al regresar con el botón "atrás" del teléfono, reactivar los botones.
  window.addEventListener("pageshow", function () {
    document.querySelectorAll("form[data-enviando='1']").forEach(function (f) {
      f.dataset.enviando = "";
      f.querySelectorAll("[aria-busy='true']").forEach(function (b) {
        b.removeAttribute("aria-busy"); b.disabled = false;
        if (b.dataset.textoOriginal) b.textContent = b.dataset.textoOriginal;
      });
    });
  });

  // 2. Botones − / + de cantidad (nueva orden)
  document.addEventListener("click", function (evento) {
    var boton = evento.target.closest("[data-paso]");
    if (!boton) return;
    var campo = document.getElementById(boton.dataset.campo);
    var paso = parseFloat(boton.dataset.paso);
    var actual = parseFloat((campo.value || "0").replace(",", ".")) || 0;
    var nuevo = Math.max(0, Math.round((actual + paso) * 100) / 100);
    campo.value = nuevo === 0 ? "" : String(nuevo);
    campo.dispatchEvent(new Event("input", { bubbles: true }));
  });

  // 3. Elegir cliente escribiendo (nueva orden)
  var buscador = document.getElementById("buscar-cliente");
  if (buscador) {
    var opciones = Array.prototype.slice.call(document.querySelectorAll(".selector-cliente .opcion"));
    var sinResultados = document.getElementById("sin-clientes");
    var normalizar = function (texto) {
      return texto.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    };
    var filtrar = function () {
      var consulta = normalizar(buscador.value.trim());
      var digitos = consulta.replace(/\D/g, "");
      var visibles = 0;
      opciones.forEach(function (opcion) {
        var nombre = normalizar(opcion.dataset.nombre);
        var coincide = !consulta || nombre.indexOf(consulta) !== -1 ||
                       (digitos.length >= 3 && opcion.dataset.telefono.indexOf(digitos) !== -1);
        var elegida = opcion.querySelector("input").checked;
        opcion.classList.toggle("oculto", !(coincide || elegida));
        if (coincide) visibles++;
      });
      if (sinResultados) sinResultados.classList.toggle("oculto", visibles > 0);
    };
    buscador.addEventListener("input", filtrar);
    filtrar();
  }

  // 4. Tema: Automático (según el teléfono), Claro u Oscuro. Se guarda en este teléfono.
  var botonesTema = document.querySelectorAll("[data-tema-opcion]");
  if (botonesTema.length) {
    var raiz = document.documentElement;
    var marcar = function () {
      var actual = raiz.getAttribute("data-theme") || "auto";
      botonesTema.forEach(function (b) {
        b.setAttribute("aria-pressed", b.dataset.temaOpcion === actual ? "true" : "false");
      });
    };
    botonesTema.forEach(function (boton) {
      boton.addEventListener("click", function () {
        var opcion = boton.dataset.temaOpcion;
        try {
          if (opcion === "auto") { localStorage.removeItem("pl-tema"); }
          else { localStorage.setItem("pl-tema", opcion); }
        } catch (e) { /* almacenamiento no disponible: el cambio dura solo esta visita */ }
        if (opcion === "auto") { raiz.removeAttribute("data-theme"); }
        else { raiz.setAttribute("data-theme", opcion); }
        marcar();
      });
    });
    marcar();
  }

  // 5. Registrar el service worker para que se pueda instalar como app
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () {});
    });
  }
})();
