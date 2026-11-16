# Predicción del nivel de actividad física diaria

Proyecto individual del curso **INF3862 – Plataformas Big Data para Data Science**
(Magíster en Inteligencia Artificial, Pontificia Universidad Católica de Chile, cuarto bimestre 2026).

**Autor:** Diego De la Vega

## Caso de uso

Una aplicación de recetas basada en Food.com se integra con relojes inteligentes. El objetivo
de este proyecto es diseñar la plataforma de datos que permite **predecir los pasos que dará
cada usuario el día siguiente**, usando solo información recibida antes del inicio de ese día.
Si la predicción queda bajo la meta personal del usuario, la aplicación le envía un recordatorio
matinal con una actividad o receta sugerida.

El caso combina los datos del wearable (mediciones, sesiones y relojes) con las comidas
registradas y el catálogo de recetas de Food.com.

## Entregables

| Entrega | Fecha | Contenido | Archivos |
|---|---|---|---|
| E1 · Diseño de datos | 16-11-2026 | Objetivo, fuentes, modelos OLTP/OLAP, consultas y arquitectura inicial | [`entregas/E1/informe.pdf`](entregas/E1/informe.pdf), fuente LaTeX en [`entregas/E1/anexos/`](entregas/E1/anexos/) |
| E2 · Ingesta y procesamiento | 30-11-2026 | Pendiente | `entregas/E2/` |
| E3 · Datos para ML y arquitectura final | 14-12-2026 | Pendiente | `entregas/E3/` |

- Registro de decisiones: [`decisiones.md`](decisiones.md)
- Cómo obtener los datos: [`datos/README.md`](datos/README.md)

## Estructura

```
.
├── README.md
├── decisiones.md
├── datos/
│   └── README.md        instrucciones para obtener los datos (no se versionan)
└── entregas/
    └── E1/
        ├── informe.pdf
        └── anexos/      fuente LaTeX del informe y script de inventario de datos
```

A partir de la E2 se agregarán `pyproject.toml` y `uv.lock`, junto con el notebook en
`entregas/E2/src/`. El entorno se preparará con `uv sync` y se ejecutará con `uv run`.

## Reproducir las cifras de datos de la E1

Todas las cifras de volumen y calidad de datos del informe salen de
[`entregas/E1/anexos/inventario_datos.py`](entregas/E1/anexos/inventario_datos.py),
que requiere `duckdb`:

```bash
python entregas/E1/anexos/inventario_datos.py datos/datos_proyecto_INF3862
```

## Compilar el informe de la E1

El informe se compila con pdfLaTeX desde `entregas/E1/anexos/`:

```bash
pdflatex Entrega1_INF3862.tex && pdflatex Entrega1_INF3862.tex
```
