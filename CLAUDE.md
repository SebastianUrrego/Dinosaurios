# CLAUDE.md

Este archivo da contexto a Claude Code sobre este proyecto.

## Contexto

Laboratorio II (2026 S02) de **Procesamiento de Lenguaje Natural**, Universidad Sergio Arboleda:
*Modelos de lenguaje a nivel de caracteres con RNN*. La guía completa está en
`Modelos de Lenguaje - Laboratorio Dinosaurios.pdf`.

Objetivo: una aplicación web que crea un dinosaurio ficticio siguiendo este flujo, donde cada etapa usa el resultado de la anterior:

```
Modelo de caracteres → Nombre → Ollama → Identidad → Imagen → Chat
```

No hay arquitectura obligatoria ni evaluación automática. Idioma del proyecto: español.

## Etapas

### 1. Generador de nombres (RNN de caracteres)
- Datos: `dinos.csv` (lo provee el curso).
- Preprocesamiento, en este orden:
  1. Normalizar el texto (mismo criterio de escritura, p. ej. minúsculas).
  2. Construir el vocabulario carácter ↔ id.
  3. Agregar tokens especiales de inicio y fin de nombre.
  4. Fijar la longitud máxima `T` a partir de las secuencias preparadas.
  5. Rellenar con `<PAD>` hasta longitud `T`.
  6. Entrada/objetivo desplazados un carácter: `X = [x0..x_{T-1}]`, `Y = [x1..x_T]`.
- Modelo: celdas RNN, LSTM o GRU; generación autoregresiva.
- Entrenamiento:
  - Evaluar **dos configuraciones** y registrar: arquitectura, número de capas, tamaño del estado oculto, épocas, función de pérdida y optimizador.
  - **Excluir `<PAD>` de la pérdida** (p. ej. `ignore_index` en `CrossEntropyLoss`).
  - Separar train/validación y graficar las curvas de pérdida de ambos conjuntos.
- Muestreo: comparar **temperatura** (al menos 3 valores, uno = 1.0), **top-k** y **top-p**. No hace falta probar todas las combinaciones.
- Resultado: **10 nombres que no estén en el conjunto de entrenamiento**, una comparación breve y **un nombre seleccionado**.
- Guardar el modelo entrenado: el botón "Nuevo Dinosaurio" lo reutiliza **sin reentrenar**.

### 2. Identidad con Ollama (SageMaker)
- Notebook de SageMaker con instancia `m5.xlarge`; Ollama instalado **con Docker**.
- Descargar un modelo acorde a los recursos y **registrar nombre y versión**.
- Comprobar desde el notebook que el modelo responde a un prompt.
- **No** se permite reemplazarlo por la API de un proveedor externo.
- Prompt: a partir del nombre, pedir apariencia, hábitat, alimentación, comportamiento y una característica distintiva (se pueden dar ejemplos de sufijos: -saurus, -raptor, -odon, -venator). Los rasgos deben ser coherentes entre sí.
- Esa descripción es la **identidad**: se conserva y alimenta las etapas siguientes.
- Persistencia:
  - Archivos en `/home/ec2-user/SageMaker` (espacio persistente).
  - `data-root` de Docker dentro de ese directorio.
  - Lifecycle script **on-start** que aplique la configuración en cada arranque.

### 3. Imagen (text-to-image)
- Google Colab u otro entorno con GPU. Librerías: `diffusers`, `transformers`, `torch`, `accelerate`, `safetensors`.
- Modelo sugerido: `amused/amused-512` (u otro de tamaño similar).
- Prompt conciso con el nombre y los rasgos de Ollama; resolución acorde a los recursos.
- Una sola imagen, solo para el dinosaurio seleccionado.

### 4. Aplicación web y chat
- Mostrar nombre, descripción, imagen e información básica del modelo de caracteres.
- Chat: enviar a Ollama la identidad como contexto en **cada** conversación; las respuestas pueden ampliarla pero no contradecirla.
- Cuando el dinosaurio se presenta o el usuario pide su descripción, el mensaje **incluye la imagen**.
- La imagen se genera **una vez por dinosaurio** y se reutiliza en el chat.
- Botón **Nuevo Dinosaurio**: nuevo nombre con el modelo ya entrenado → nueva identidad → nueva imagen.
- Conexión entre componentes: libre (ngrok hacia SageMaker/Colab/local, AWS Lambda como proxy, etc.). **Documentar qué recibe y devuelve cada componente.**
- Desplegar la web en **AWS**; el generador de imágenes puede quedarse en Colab o local.

## Entregables
- Enlace al sitio web funcionando.
- Repositorio con: generador de nombres, configuración de Ollama, código de generación de imágenes y archivos de la aplicación.
- README con instrucciones breves para identificar y ejecutar los componentes.
- Evidencias experimentales en el repo: arquitectura/configuración del modelo, curvas de pérdida (train y validación), configuraciones de muestreo, 10 nombres y su análisis.

## Evaluación
| Componente | Valor |
|---|---|
| Sustentación (modelo, decisiones, Ollama, imagen, integración) | 1.5 |
| Repositorio y arquitectura completa (flujo nombre → identidad → imagen → chat, organización, instrucciones) | 2.5 |
| Metodología y seguimiento de experimentos (configs, curvas, muestreo, análisis) | 1.0 |
| **Total** | **5.0** |

## Reglas para trabajar en este repo
- **Nunca** subir credenciales, claves de AWS, tokens de ngrok, archivos `.pem` ni otra información sensible. Usar variables de entorno y un `.env` listado en `.gitignore` (con un `.env.example` sin valores reales).
- Mantener cada etapa en su propia carpeta y documentar en el README las entradas/salidas de cada componente.
- Reproducibilidad: fijar semillas y guardar configuraciones, métricas y gráficas de los experimentos.

## Checklist antes de entregar
- [ ] Los 10 nombres no son copias del conjunto de entrenamiento.
- [ ] La identidad del dinosaurio seleccionado es coherente.
- [ ] La imagen corresponde con los rasgos descritos.
- [ ] El chat conserva la identidad durante la conversación.
- [ ] La imagen aparece en el chat al presentar o describir al dinosaurio.
- [ ] "Nuevo Dinosaurio" genera de nuevo sin reentrenar.
- [ ] El sitio web es accesible.
- [ ] El repo tiene las instrucciones y no expone información sensible.
