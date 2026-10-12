# Isla de los Dinosaurios

Laboratorio II de Procesamiento de Lenguaje Natural (Universidad Sergio Arboleda, 2026 S02). Es una aplicación que crea un dinosaurio ficticio:

```
Modelo de caracteres → Nombre → Ollama → Identidad → Imagen → Chat
```

## Estructura

| Carpeta | Componente |
|---|---|
| `generador_nombres/` | RNN de caracteres: preprocesamiento, entrenamiento, muestreo y evidencias (`data/` para `dinos.csv`) |
| `ollama/` | Configuración de Ollama en SageMaker (Docker y lifecycle script on-start) |
| `imagen/` | Generación de la imagen text-to-image (Colab) |
| `app/` | Aplicación web y chat |
| `docs/` | Entradas y salidas de cada componente, y diagramas |

## Configuración

Copia `.env.example` a `.env` y completa los valores. El archivo `.env` no se versiona.

## Ejecución

_Pendiente: se completará con cada componente._

## Enlaces

- Sitio web: _pendiente_
