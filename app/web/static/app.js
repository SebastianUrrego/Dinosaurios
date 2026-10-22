const $ = (id) => document.getElementById(id);
const CAMPOS = [
  ["periodo", "Periodo"],
  ["apariencia", "Apariencia"],
  ["habitat", "Hábitat"],
  ["alimentacion", "Alimentación"],
  ["comportamiento", "Comportamiento"],
  ["rasgo_distintivo", "Rasgo distintivo"],
];
let mensajes = [];   // historial que se envía al chat: [{role, content}]
let ocupado = false;
let actualId = null; // dinosaurio que se muestra y con el que se conversa

async function api(ruta, opciones = {}, segundos = 30) {
  const corte = new AbortController();
  const reloj = setTimeout(() => corte.abort(), segundos * 1000);
  try {
    const r = await fetch(ruta, {
      headers: { "Content-Type": "application/json" },
      signal: corte.signal,
      ...opciones,
    });
    const datos = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(datos.detail || `Error ${r.status}`);
    return datos;
  } catch (e) {
    if (e.name === "AbortError") throw new Error("el dinosaurio tardó demasiado en responder; inténtalo de nuevo");
    throw e;
  } finally {
    clearTimeout(reloj);
  }
}

function lista(dl, pares) {
  dl.replaceChildren();
  for (const [titulo, valor] of pares) {
    if (!valor) continue;
    const dt = document.createElement("dt");
    dt.textContent = titulo;
    const dd = document.createElement("dd");
    dd.textContent = valor;
    dl.append(dt, dd);
  }
}

let infoModelo = null;

function mostrarFicha(dino) {
  const id = dino.identidad;
  $("nombre").textContent = dino.nombre;
  $("significado").textContent = id.significado || "";
  $("imagen").src = dino.imagen_url;
  $("imagen").alt = `Ilustración de ${dino.nombre}`;
  lista($("rasgos"), CAMPOS.map(([k, t]) => [t, id[k]]));
  const m = infoModelo;
  lista($("origen"), [
    ["Nombre", m && `${m.arquitectura} ${m.capas}×${m.oculto} (${m.parametros.toLocaleString("es")} parámetros), `
      + `entrenada con ${m.nombres_entrenamiento} nombres; mejor época ${m.mejor_epoca}, `
      + `pérdida de validación ${m.perdida_validacion}; muestreo ${m.muestreo}`],
    ["Identidad", `Ollama ${dino.modelo_ollama} en SageMaker`],
    ["Rasgos sorteados", dino.pistas && Object.values(dino.pistas).join(" · ")],
    ["Imagen", dino.imagen && `${dino.imagen.modelo}, ${dino.imagen.pasos} pasos, semilla ${dino.imagen.semilla}`],
  ]);
  document.title = `${dino.nombre} · Isla de los Dinosaurios`;
}

function burbuja(clase, texto, imagen) {
  const div = document.createElement("div");
  div.className = `msg ${clase}`;
  if (imagen) {
    const img = document.createElement("img");
    img.src = imagen;
    img.alt = $("imagen").alt;
    div.append(img);
  }
  div.append(document.createTextNode(texto));
  $("mensajes").append(div);
  $("mensajes").scrollTop = $("mensajes").scrollHeight;
  return div;
}

function bloquear(si) {
  ocupado = si;
  $("texto").disabled = si;
  $("formulario").querySelector("button").disabled = si;
  for (const b of $("galeria").querySelectorAll("button")) b.disabled = si;
}

// ---------- Galería ----------

async function cargarGaleria() {
  const dinos = await api("/api/dinosaurios");
  $("galeria").replaceChildren(...dinos.map((d) => {
    const b = document.createElement("button");
    b.className = "tarjeta";
    b.dataset.id = d.id;
    const img = document.createElement("img");
    img.src = d.imagen_url;
    img.alt = "";
    b.append(img, document.createTextNode(d.nombre));
    if (d.principal) {
      const e = document.createElement("span");
      e.className = "etiqueta";
      e.textContent = "laboratorio";
      b.append(e);
    }
    b.addEventListener("click", () => abrir(d.id));
    return b;
  }));
  return dinos;
}

async function abrir(id) {
  if (ocupado || id === actualId) return;
  actualId = id;
  for (const b of $("galeria").querySelectorAll("button")) {
    b.classList.toggle("activa", b.dataset.id === id);
    if (b.dataset.id === id) b.setAttribute("aria-current", "true"); else b.removeAttribute("aria-current");
  }
  mostrarFicha(await api(`/api/dinosaurios/${id}`));
  await presentar();
}

async function presentar() {
  $("mensajes").replaceChildren();
  mensajes = [];
  bloquear(true);
  const espera = burbuja("dino escribiendo", "Despertando al dinosaurio…");
  try {
    const r = await api(`/api/presentacion/${actualId}`, {}, 240);
    espera.remove();
    burbuja("dino", r.respuesta, r.imagen_url);
    mensajes.push({ role: "assistant", content: r.respuesta });
  } catch (e) {
    espera.remove();
    burbuja("sistema", `No se pudo contactar al dinosaurio: ${e.message}`);
  }
  bloquear(false);
}

$("formulario").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const texto = $("texto").value.trim();
  if (!texto || ocupado) return;
  $("texto").value = "";
  burbuja("yo", texto);
  mensajes.push({ role: "user", content: texto });
  bloquear(true);
  const espera = burbuja("dino escribiendo", "Escribiendo…");
  try {
    const r = await api("/api/chat", { method: "POST", body: JSON.stringify({ id: actualId, mensajes }) }, 240);
    espera.remove();
    burbuja("dino", r.respuesta, r.imagen_url);
    mensajes.push({ role: "assistant", content: r.respuesta });
  } catch (e) {
    espera.remove();
    mensajes.pop();
    burbuja("sistema", `Sin respuesta: ${e.message}`);
  }
  bloquear(false);
  $("texto").focus();
});

// ---------- Nuevo Dinosaurio ----------

function pintarPasos(pasos, actual, estado, nombre) {
  $("pasos").replaceChildren(...pasos.map((p, i) => {
    const li = document.createElement("li");
    li.textContent = p;
    if (estado === "listo" || i < actual) li.className = "hecho";
    else if (i === actual && estado === "en_curso") li.className = "activo";
    if (i === 0 && nombre) {
      const d = document.createElement("span");
      d.className = "detalle";
      d.textContent = ` → ${nombre}`;
      li.append(d);
    }
    return li;
  }));
}

$("nuevo").addEventListener("click", async () => {
  $("nuevo").disabled = true;
  $("error").hidden = true;
  $("cerrar").hidden = true;
  $("progreso").showModal();
  try {
    const { trabajo, pasos } = await api("/api/nuevo", { method: "POST" });
    pintarPasos(pasos, 0, "en_curso");
    while (true) {
      await new Promise((r) => setTimeout(r, 2000));
      const t = await api(`/api/trabajos/${trabajo}`);
      pintarPasos(t.pasos, t.paso, t.estado, t.nombre);
      $("reloj").textContent = `${t.segundos} s`;
      if (t.estado === "listo") {
        $("progreso").close();
        await cargarGaleria();
        await abrir(t.dino.id);
        break;
      }
      if (t.estado === "error") throw new Error(t.error);
    }
  } catch (e) {
    $("error").textContent = e.message;
    $("error").hidden = false;
    $("cerrar").hidden = false;
  }
  $("nuevo").disabled = false;
});

$("cerrar").addEventListener("click", () => $("progreso").close());

// ---------- Inicio ----------

async function revisarEstado() {
  const e = await api("/api/estado").catch(() => ({ sagemaker: false }));
  const ok = e.sagemaker && e.modelo_disponible;
  const calentando = ok && (e.modelo_cargado === false || !e.imagen_cargada);
  $("estado").textContent = !ok ? "SageMaker desconectado"
    : calentando ? "SageMaker calentando los modelos…" : `SageMaker conectado · ${e.modelo_ollama}`;
  $("estado").className = `estado ${!ok ? "mal" : calentando ? "medio" : "ok"}`;
  $("estado").title = e.detalle || "Conexión con el notebook de SageMaker";
  if (calentando) setTimeout(revisarEstado, 15000);
}

(async () => {
  infoModelo = await api("/api/modelo").catch(() => null);
  const dinos = await cargarGaleria();
  revisarEstado();
  await abrir(dinos[0].id);  // siempre empieza por Aborosaurus, el dinosaurio del laboratorio
})();
