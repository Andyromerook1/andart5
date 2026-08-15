// ============================================================
// ANDART — lógica de la interfaz de chat
// ============================================================

const chat = document.getElementById("chat");
const form = document.getElementById("form-input");
const campo = document.getElementById("campo-mensaje");
const botonEnviar = document.getElementById("boton-enviar");
const pensando = document.getElementById("pensando");
const estadoConexion = document.getElementById("estado-conexion");
const textoEstado = document.getElementById("texto-estado");
const botonNuevoChat = document.getElementById("boton-nuevo-chat");
const botonHistorial = document.getElementById("boton-historial");
const panelChats = document.getElementById("panel-chats");
const panelFondo = document.getElementById("panel-fondo");
const botonCerrarPanel = document.getElementById("boton-cerrar-panel");
const listaChats = document.getElementById("lista-chats");

let enviando = false;
let chatActualId = null;

// ---------- nuevo chat ----------

botonNuevoChat.addEventListener("click", async () => {
  if (enviando) return;
  if (chat.children.length > 1 && !confirm("¿Empezar un chat nuevo? El actual queda guardado y lo podés retomar desde el historial.")) {
    return;
  }
  try {
    const r = await fetch("/api/nuevo_chat", { method: "POST" });
    const data = await r.json();
    chatActualId = data.chat_id || null;
  } catch (e) {
    // Si falla la llamada igual limpiamos la pantalla; el peor caso es
    // que el backend conserve un historial viejo una request más.
  }
  mostrarPantallaVacia();
  campo.focus();
});

function mostrarPantallaVacia() {
  chat.innerHTML = "";
  const el = document.createElement("div");
  el.className = "mensaje mensaje-sistema";
  const p = document.createElement("p");
  p.textContent = "Chat nuevo. Escribí algo para empezar.";
  el.appendChild(p);
  chat.appendChild(el);
}

// ---------- panel de chats guardados ----------

function abrirPanel() {
  panelChats.hidden = false;
  panelFondo.hidden = false;
  cargarListaChats();
}

function cerrarPanel() {
  panelChats.hidden = true;
  panelFondo.hidden = true;
}

botonHistorial.addEventListener("click", abrirPanel);
botonCerrarPanel.addEventListener("click", cerrarPanel);
panelFondo.addEventListener("click", cerrarPanel);

function formatearFecha(timestampSegundos) {
  if (!timestampSegundos) return "";
  const fecha = new Date(timestampSegundos * 1000);
  const hoy = new Date();
  const esHoy = fecha.toDateString() === hoy.toDateString();
  if (esHoy) {
    return fecha.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" });
  }
  return fecha.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit" });
}

async function cargarListaChats() {
  listaChats.innerHTML = '<li class="lista-chats-vacio">Cargando...</li>';
  try {
    const r = await fetch("/api/chats");
    const data = await r.json();
    chatActualId = data.chat_actual;
    pintarListaChats(data.chats || []);
  } catch (e) {
    listaChats.innerHTML = '<li class="lista-chats-vacio">No se pudo cargar el historial.</li>';
  }
}

function pintarListaChats(listaDeChats) {
  listaChats.innerHTML = "";

  if (listaDeChats.length === 0) {
    listaChats.innerHTML = '<li class="lista-chats-vacio">Todavía no hay chats guardados.</li>';
    return;
  }

  listaDeChats.forEach((c) => {
    const li = document.createElement("li");
    li.className = "item-chat" + (c.id === chatActualId ? " activo" : "");

    const info = document.createElement("div");
    info.className = "item-chat-info";

    const titulo = document.createElement("div");
    titulo.className = "item-chat-titulo";
    titulo.textContent = c.titulo;

    const fecha = document.createElement("div");
    fecha.className = "item-chat-fecha";
    fecha.textContent = formatearFecha(c.actualizado) + " · " + c.mensajes + " mensajes";

    info.appendChild(titulo);
    info.appendChild(fecha);

    const botonBorrar = document.createElement("button");
    botonBorrar.className = "item-chat-borrar";
    botonBorrar.type = "button";
    botonBorrar.setAttribute("aria-label", "Borrar chat");
    botonBorrar.innerHTML =
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>';
    botonBorrar.addEventListener("click", (ev) => {
      ev.stopPropagation();
      borrarChat(c.id);
    });

    li.appendChild(info);
    li.appendChild(botonBorrar);
    li.addEventListener("click", () => cargarChat(c.id));

    listaChats.appendChild(li);
  });
}

async function cargarChat(id) {
  try {
    const r = await fetch(`/api/chats/${id}`);
    const data = await r.json();
    if (!r.ok || data.error) {
      alert(data.error || "No se pudo abrir ese chat.");
      return;
    }
    chatActualId = id;
    pintarHistorialCompleto(data.historial || []);
    cerrarPanel();
  } catch (e) {
    alert("No se pudo conectar con el servidor.");
  }
}

function pintarHistorialCompleto(historial) {
  chat.innerHTML = "";
  historial.forEach((entrada) => {
    if (entrada.usuario) {
      const el = document.createElement("div");
      el.className = "mensaje mensaje-usuario";
      const p = document.createElement("p");
      p.textContent = entrada.usuario;
      el.appendChild(p);
      agregarBotonCopiarMensaje(el, entrada.usuario);
      chat.appendChild(el);
    } else if (entrada.andart) {
      const el = document.createElement("div");
      el.className = "mensaje mensaje-ia";
      renderizarMensajeIA(el, entrada.andart);
      agregarBotonCopiarMensaje(el, entrada.andart);
      chat.appendChild(el);
    }
  });
  desplazarAbajo();
}

async function borrarChat(id) {
  if (!confirm("¿Borrar este chat? No se puede deshacer.")) return;
  try {
    await fetch(`/api/chats/${id}`, { method: "DELETE" });
    if (id === chatActualId) {
      chatActualId = null;
      mostrarPantallaVacia();
    }
    cargarListaChats();
  } catch (e) {
    alert("No se pudo borrar el chat.");
  }
}

// ---------- estado de conexión ----------

async function chequearSalud() {
  try {
    const r = await fetch("/api/salud");
    if (r.ok) {
      estadoConexion.className = "header-estado conectado";
      textoEstado.textContent = "conectado";
      return;
    }
  } catch (e) {
    /* sigue abajo */
  }
  estadoConexion.className = "header-estado error";
  textoEstado.textContent = "sin conexión";
}
chequearSalud();

// ---------- escapado (seguridad básica: nunca insertamos HTML crudo) ----------

function escaparHtml(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

// ---------- parser liviano: fences ``` , código en línea `x` y **negrita** ----------
// No usamos una librería de markdown completa a propósito: así la interfaz
// sigue funcionando aunque el CDN no cargue, y evitamos el riesgo de que
// algún markdown-renderer inserte HTML crudo desde la respuesta del modelo.

function renderizarMensajeIA(contenedor, textoCrudo) {
  const partes = textoCrudo.split(/```(\w*)\n?([\s\S]*?)```/g);
  // split con grupos de captura intercala: [texto, lang, code, texto, lang, code, ...]

  for (let i = 0; i < partes.length; i++) {
    if (i % 3 === 0) {
      // texto normal (puede tener código en línea y párrafos)
      const texto = partes[i];
      if (!texto.trim()) continue;
      texto.split(/\n{2,}/).forEach((parrafo) => {
        if (!parrafo.trim()) return;
        const p = document.createElement("p");
        p.innerHTML = escaparHtml(parrafo)
          .replace(/`([^`]+)`/g, '<code class="codigo-en-linea">$1</code>')
          .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
          .replace(/\n/g, "<br>");
        contenedor.appendChild(p);
      });
    } else if (i % 3 === 1) {
      const lang = partes[i];
      const codigo = partes[i + 1] || "";
      contenedor.appendChild(crearBloqueCodigo(codigo.trim(), lang));
      i++; // ya consumimos el código en este paso
    }
  }
}

function crearBloqueCodigo(codigo, lang) {
  const bloque = document.createElement("div");
  bloque.className = "bloque-codigo";

  const barra = document.createElement("div");
  barra.className = "bloque-codigo-barra";

  const etiqueta = document.createElement("span");
  etiqueta.textContent = lang || "texto";
  barra.appendChild(etiqueta);

  const botonCopiar = document.createElement("button");
  botonCopiar.className = "boton-copiar-codigo";
  botonCopiar.type = "button";
  botonCopiar.textContent = "copiar";
  botonCopiar.addEventListener("click", () => copiarTexto(codigo, botonCopiar));
  barra.appendChild(botonCopiar);

  const pre = document.createElement("pre");
  const codeEl = document.createElement("code");
  if (lang) codeEl.className = `language-${lang}`;
  codeEl.textContent = codigo;
  pre.appendChild(codeEl);

  bloque.appendChild(barra);
  bloque.appendChild(pre);

  // Highlight.js es progresivo: si el CDN no cargó, el código se ve
  // igual (monoespaciado, legible), solo sin colores por tipo de token.
  if (window.hljs) {
    try { window.hljs.highlightElement(codeEl); } catch (e) {}
  }

  return bloque;
}

// ---------- copiar al portapapeles ----------

async function copiarTexto(texto, boton) {
  try {
    await navigator.clipboard.writeText(texto);
  } catch (e) {
    // Fallback para navegadores/webviews sin permiso de clipboard API
    const area = document.createElement("textarea");
    area.value = texto;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    document.body.removeChild(area);
  }
  const textoOriginal = boton.textContent;
  boton.textContent = "✓";
  boton.classList.add("copiado");
  setTimeout(() => {
    boton.textContent = textoOriginal;
    boton.classList.remove("copiado");
  }, 1400);
}

function agregarBotonCopiarMensaje(mensajeEl, textoCrudo) {
  const boton = document.createElement("button");
  boton.className = "boton-copiar-mensaje";
  boton.type = "button";
  boton.setAttribute("aria-label", "Copiar mensaje");
  boton.innerHTML =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
  boton.addEventListener("click", () => copiarTexto(textoCrudo, boton));
  mensajeEl.appendChild(boton);
}

// ---------- mensajes en pantalla ----------

function agregarMensajeUsuario(texto) {
  const el = document.createElement("div");
  el.className = "mensaje mensaje-usuario";
  const p = document.createElement("p");
  p.textContent = texto;
  el.appendChild(p);
  agregarBotonCopiarMensaje(el, texto);
  chat.appendChild(el);
  desplazarAbajo();
}

function agregarMensajeIA(texto) {
  const el = document.createElement("div");
  el.className = "mensaje mensaje-ia";
  renderizarMensajeIA(el, texto);
  agregarBotonCopiarMensaje(el, texto);
  chat.appendChild(el);
  desplazarAbajo();
}

function agregarMensajeError(texto) {
  const el = document.createElement("div");
  el.className = "mensaje mensaje-error";
  const p = document.createElement("p");
  p.textContent = texto;
  el.appendChild(p);
  chat.appendChild(el);
  desplazarAbajo();
}

function desplazarAbajo() {
  requestAnimationFrame(() => {
    chat.scrollTop = chat.scrollHeight;
  });
}

// ---------- envío ----------

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  if (enviando) return;

  const texto = campo.value.trim();
  if (!texto) return;

  agregarMensajeUsuario(texto);
  campo.value = "";
  enviando = true;
  botonEnviar.disabled = true;
  pensando.hidden = false;
  desplazarAbajo();

  try {
    const r = await fetch("/api/mensaje", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensaje: texto }),
    });
    const data = await r.json();

    if (!r.ok || data.error) {
      agregarMensajeError(data.error || "Ocurrió un error inesperado.");
    } else {
      agregarMensajeIA(data.respuesta || "");
    }
    estadoConexion.className = "header-estado conectado";
    textoEstado.textContent = "conectado";
  } catch (e) {
    agregarMensajeError(
      "No se pudo conectar con el servidor. Verificá que servidor.py esté corriendo."
    );
    estadoConexion.className = "header-estado error";
    textoEstado.textContent = "sin conexión";
  } finally {
    enviando = false;
    botonEnviar.disabled = false;
    pensando.hidden = true;
    campo.focus();
  }
});
