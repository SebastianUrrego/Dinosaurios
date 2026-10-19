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

async function api(ruta, opciones = {}) {
  const r = await fetch(ruta, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(datos.detail || `Error ${r.status}`);
  return datos;
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
}

async function presentar() {
  $("mensajes").replaceChildren();
  mensajes = [];
  bloquear(true);
  const espera = burbuja("dino escribiendo", "Despertando al dinosaurio…");
  try {
    const r = await api("/api/presentacion");
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
    const r = await api("/api/chat", { method: "POST", body: JSON.stringify({ mensajes }) });
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
        mostrarFicha(t.dino);
        $("progreso").close();
        await presentar();
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
  $("estado").textContent = ok ? `SageMaker conectado · ${e.modelo_ollama}` : "SageMaker desconectado";
  $("estado").className = `estado ${ok ? "ok" : "mal"}`;
  $("estado").title = e.detalle || "Conexión con el notebook de SageMaker";
}

(async () => {
  infoModelo = await api("/api/modelo").catch(() => null);
  mostrarFicha(await api("/api/dinosaurio"));
  revisarEstado();
  presentar();
})();
