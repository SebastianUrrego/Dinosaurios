# Dinosaurios generados con la app

Dinosaurios creados con el botón **Nuevo Dinosaurio** en http://52.207.10.151. Cada carpeta de datos de la
EC2 (`app/web/datos/<id>/`) se copió aquí con lo que devuelve `GET /api/dinosaurio` y su imagen.

| Dinosaurio | Creado | Archivos |
|---|---|---|
| Cryptoceratops | 2026-10-20 01:14 | `cryptoceratops.json`, `cryptoceratops.png`, `cryptoceratops_chat.webp` |
| Balamoceratops | 2026-10-20 01:20 | `balamoceratops.json`, `balamoceratops.png` |

## Cryptoceratops

![Cryptoceratops en la app](cryptoceratops_chat.webp)

| | |
|---|---|
| **Significado** | "Ceratopsio oculto" o "cuerno secreto", por su naturaleza camuflada y sus estructuras óseas |
| **Periodo** | Cretácico Superior |
| **Apariencia** | ~8 m y ~4 t; cuerpo robusto; piel escamosa color tierra y gris oscuro para mimetizarse; cuernos pequeños y curvados |
| **Hábitat** | Pantanos y bosques densos de tierras bajas, con mucha humedad y vegetación |
| **Alimentación** | Herbívoro selectivo: helechos y plantas acuáticas; mandíbula fuerte y dientes planos |
| **Comportamiento** | Esquivo y solitario; se queda inmóvil para no ser detectado; se defiende con camuflaje y enterrándose en el barro |
| **Rasgo distintivo** | Capa de queratina bioluminiscente que emite un patrón de luz tenue para desorientar depredadores |
| **Imagen** | SD-Turbo, 4 pasos, semilla 1388 |

**Prompt de la imagen:** *Cryptoceratops, a dinosaur. A large, low-slung herbivore with mottled brown and grey skin,
hidden among dense swamp foliage. Small, curved horns. Bioluminescent skin pattern faintly glowing in dim light.
Detailed scales, realistic nature documentary illustration*

**Observaciones:**
- El nombre (*crypto-* "oculto" + *-ceratops* "cara con cuernos") se interpretó con raíces reales, y toda la identidad
  gira en torno a esa idea: camuflaje, vida esquiva y cuernos pequeños.
- La imagen acierta en el entorno (pantano), el color tierra y el cuerpo robusto, pero lo dibuja con cuello largo,
  como un saurópodo, y no se ven los cuernos ni la bioluminiscencia: SD-Turbo sigue mejor el entorno y el color
  que los detalles anatómicos.

## Balamoceratops

![Balamoceratops](balamoceratops.png)

| | |
|---|---|
| **Significado** | Combina "gran lagarto" con "cabeza con cuernos": un gran herbívoro con armadura facial |
| **Periodo** | Cretácico Superior |
| **Apariencia** | ~12 m y ~4 t; cuerpo robusto; piel escamosa verde oliva oscuro; grandes cornetes óseos en el cráneo |
| **Hábitat** | Pantanos y sabanas boscosas del sur de América del Norte |
| **Alimentación** | Herbívoro voraz: raspa corteza, helechos y plantas acuáticas, con dientes robustos |
| **Comportamiento** | Territorial y social, en grupos pequeños; se defiende intimidando con los cuernos |
| **Rasgo distintivo** | Placa ósea en la base del cuello que ancla sus cuernos, excepcionalmente pesados |
| **Imagen** | SD-Turbo, 4 pasos, semilla 9478 |

La imagen corresponde bien: un cuadrúpedo pesado, verde oliva, con cuernos cortos en la cabeza, cruzando un pantano.

## Comparación

| | Aborosaurus | Eospechopheosaurus | Cryptoceratops | Balamoceratops |
|---|---|---|---|---|
| Origen | Laboratorio (notebook) | App | App | App |
| Interpretación del nombre | *arbor-* + *-saurus*: "lagarto del árbol" | "lagarto del tiempo" | *crypto-* + *-ceratops*: "ceratopsio oculto" | "gran lagarto" + "cabeza con cuernos" |
| Periodo | Cretácico Medio | Jurásico Superior | Cretácico Superior | Cretácico Superior |
| Tipo | Herbívoro arborícola, esbelto (6 m) | Saurópodo robusto | Herbívoro robusto (8 m) | Herbívoro acorazado (12 m) |
| Hábitat | Copas de árboles, bosque húmedo | Pantanos | Pantanos y bosques densos | Pantanos y sabanas boscosas |
| Defensa | Esconderse en el follaje | — | Camuflaje e inmovilidad | Intimidación con cuernos |
| Rasgo distintivo | Membranas para adherirse a ramas | — | Piel bioluminiscente | Placa ósea que ancla los cuernos |

**Conclusión:**
- **Cada dinosaurio es distinto:** el nombre cambia siempre y gemma4 construye la identidad a partir de sus raíces,
  así que el tamaño, el comportamiento, la defensa y el rasgo distintivo cambian con él.
- **Pero hay un "aire de familia":** tres de los cuatro son herbívoros de pantano, tres del Cretácico, y los dos
  *-ceratops* comparten dieta (helechos, plantas acuáticas, raspar corteza) y peso (~4 t). Influyen el mismo prompt
  para todos, la temperatura baja (0.4, elegida para que la identidad sea coherente) y que el sufijo del nombre
  pesa mucho en la interpretación.
- **Una vez creada, la identidad no cambia:** se guarda con su imagen y su presentación, y el chat la respeta.
