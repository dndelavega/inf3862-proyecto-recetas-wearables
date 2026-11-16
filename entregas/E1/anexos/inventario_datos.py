"""Inventario de los datos del proyecto INF3862 (Entrega 1).

Reproduce todas las cifras de los datos citadas en el informe de la E1:
volumen, duplicados, atrasos de recepción, faltantes, referencias
inexistentes y la verificación de que Calories de Food.com es por porción.

Uso:
    python inventario_datos.py <ruta a datos_proyecto_INF3862>

Requiere: duckdb (pip install duckdb). Tarda menos de un minuto y usa
unos pocos GB de RAM; las mediciones se leen con un esquema explícito
porque la inferencia automática sobre los 1.450 archivos agota la memoria.
"""

import sys
from pathlib import Path

import duckdb


def tamano_mb(ruta: Path) -> float:
    """Tamaño real en MB (10^6 bytes); en carpetas, solo los .jsonl.gz."""
    if ruta.is_file():
        return ruta.stat().st_size / 1e6
    return sum(p.stat().st_size for p in ruta.rglob("*.jsonl.gz")) / 1e6


def main(base: Path) -> None:
    w = base / "wearable"
    f = base / "foodcom"
    con = duckdb.connect()
    con.sql("SET threads = 4; SET preserve_insertion_order = false;")

    def mostrar(titulo: str, sql: str) -> None:
        print(f"\n## {titulo}")
        print(con.sql(sql))

    # ---------------------------------------------------------------
    # Volumen entregado
    # ---------------------------------------------------------------
    archivos = sorted((w / "mediciones").glob("*/*.jsonl.gz"))
    dias = sorted({a.parent.name for a in archivos})
    print("## Volumen en disco")
    for nombre in ["recipes.parquet", "reviews.parquet"]:
        print(f"{nombre:22s} {tamano_mb(f / nombre):9.2f} MB")
    for nombre in ["dispositivos.csv", "comidas.csv", "sesiones.jsonl", "mediciones"]:
        print(f"{nombre:22s} {tamano_mb(w / nombre):9.2f} MB")
    print(f"Archivos de mediciones: {len(archivos)} .jsonl.gz en {len(dias)} días "
          f"de recepción ({dias[0]} a {dias[-1]})")
    total = sum(tamano_mb(f / n) for n in ["recipes.parquet", "reviews.parquet"]) + sum(
        tamano_mb(w / n) for n in ["dispositivos.csv", "comidas.csv", "sesiones.jsonl", "mediciones"])
    print(f"Total: {total:.0f} MB")

    mostrar("Food.com", f"""
        SELECT (SELECT count(*) FROM '{f}/recipes.parquet') AS recetas,
               (SELECT count(*) FROM '{f}/reviews.parquet') AS resenas,
               (SELECT count(DISTINCT AuthorId) FROM '{f}/reviews.parquet') AS usuarios_resenas
    """)
    mostrar("Relojes", f"""
        SELECT count(*) AS relojes,
               count(DISTINCT device_id) AS device_id_distintos,
               count(DISTINCT AuthorId) AS usuarios,
               count(fecha_desvinculacion) AS desvinculados,
               sum((modelo = 'Pulso S')::INT) AS pulso_s,
               sum((modelo = 'FitBand 2')::INT) AS fitband_2
        FROM read_csv_auto('{w}/dispositivos.csv')
    """)
    mostrar("Usuarios con más de un reloj (total / activos a la vez)", f"""
        SELECT
          (SELECT count(*) FROM (SELECT AuthorId FROM read_csv_auto('{w}/dispositivos.csv')
                                 GROUP BY 1 HAVING count(*) > 1)) AS cambiaron_de_reloj,
          (SELECT count(*) FROM (SELECT AuthorId FROM read_csv_auto('{w}/dispositivos.csv')
                                 WHERE fecha_desvinculacion IS NULL
                                 GROUP BY 1 HAVING count(*) > 1)) AS con_dos_activos
    """)

    # ---------------------------------------------------------------
    # Mediciones: unificar los dos formatos de reloj
    # ---------------------------------------------------------------
    con.sql(f"""
        CREATE TABLE m AS
        SELECT coalesce(device_id, dev) AS device_id,
               coalesce(ts_medicion::TIMESTAMPTZ,
                        make_timestamp("timestamp" * 1000)::TIMESTAMPTZ) AS ts_medicion,
               coalesce(ts_recepcion, received_at)::TIMESTAMPTZ AS ts_recepcion,
               coalesce(frecuencia_cardiaca, fc) AS fc,
               coalesce(pasos, steps) AS pasos,
               coalesce(calorias, kcal) AS calorias,
               dev IS NOT NULL AS es_fitband
        FROM read_json('{w}/mediciones/*/*.jsonl.gz',
                       format = 'newline_delimited',
                       columns = {{device_id: 'VARCHAR', ts_medicion: 'VARCHAR',
                                   ts_recepcion: 'VARCHAR', frecuencia_cardiaca: 'DOUBLE',
                                   pasos: 'DOUBLE', calorias: 'DOUBLE',
                                   dev: 'VARCHAR', "timestamp": 'BIGINT',
                                   received_at: 'VARCHAR', fc: 'DOUBLE',
                                   steps: 'DOUBLE', kcal: 'DOUBLE'}})
    """)
    mostrar("Mediciones", """
        SELECT count(*) AS filas,
               sum(es_fitband::INT) AS filas_fitband,
               round(100 * avg(es_fitband::INT), 1) AS pct_fitband,
               count(DISTINCT device_id) AS relojes,
               sum((fc IS NULL)::INT) AS fc_nula,
               round(100 * avg((fc IS NULL)::INT), 1) AS pct_fc_nula,
               sum((pasos < 0 OR calorias < 0)::INT) AS negativos
        FROM m
    """)
    mostrar("Duplicados: clave lógica vs fila completa", """
        SELECT (SELECT count(*) FROM m) AS filas,
               (SELECT count(*) FROM (SELECT DISTINCT device_id, ts_medicion FROM m)) AS claves_unicas,
               (SELECT count(*) FROM m)
                 - (SELECT count(*) FROM (SELECT DISTINCT device_id, ts_medicion FROM m)) AS sobran_por_clave,
               (SELECT count(*) FROM m)
                 - (SELECT count(*) FROM (SELECT DISTINCT * FROM m)) AS sobran_por_fila_completa
    """)
    mostrar("Claves repetidas con valores distintos (debe ser 0)", """
        SELECT count(*) AS claves_repetidas,
               sum((n_valores > 1)::INT) AS con_valores_distintos,
               sum((n_recepciones > 1)::INT) AS con_otra_recepcion
        FROM (SELECT device_id, ts_medicion,
                     count(DISTINCT (fc, pasos, calorias)) AS n_valores,
                     count(DISTINCT ts_recepcion) AS n_recepciones
              FROM m GROUP BY ALL HAVING count(*) > 1)
    """)
    mostrar("Efecto de no deduplicar sobre los pasos", """
        WITH crudo AS (SELECT sum(pasos) AS pasos_crudos FROM m),
             dedup AS (SELECT sum(p) AS pasos_dedup
                       FROM (SELECT any_value(pasos) AS p FROM m
                             GROUP BY device_id, ts_medicion))
        SELECT pasos_crudos, pasos_dedup,
               round(100 * (pasos_crudos / pasos_dedup - 1), 1) AS pct_inflado
        FROM crudo, dedup
    """)
    mostrar("Atraso entre medición y recepción (horas)", """
        SELECT round(quantile_cont(h, 0.5), 1) AS mediana,
               round(quantile_cont(h, 0.9), 1) AS p90,
               round(quantile_cont(h, 0.99), 1) AS p99,
               round(max(h), 1) AS maximo,
               round(100 * avg((date_trunc('day', ts_recepcion)
                                > date_trunc('day', ts_medicion))::INT), 1) AS pct_otro_dia
        FROM (SELECT epoch(ts_recepcion - ts_medicion) / 3600 AS h,
                     ts_recepcion, ts_medicion FROM m)
    """)

    # ---------------------------------------------------------------
    # Sesiones, comidas y referencias
    # ---------------------------------------------------------------
    mostrar("Sesiones", f"""
        SELECT count(*) AS filas,
               count(*) - count(DISTINCT session_id) AS session_id_repetidos,
               count(*) - (SELECT count(*) FROM (SELECT DISTINCT *
                           FROM read_json_auto('{w}/sesiones.jsonl'))) AS duplicados_exactos,
               sum((distancia_km IS NULL)::INT) AS distancia_nula
        FROM read_json_auto('{w}/sesiones.jsonl')
    """)
    mostrar("Comidas", f"""
        SELECT count(*) AS filas,
               count(*) FILTER (WHERE RecipeId NOT IN
                   (SELECT RecipeId::BIGINT FROM '{f}/recipes.parquet')) AS receta_inexistente,
               count(*) FILTER (WHERE AuthorId NOT IN
                   (SELECT AuthorId FROM read_csv_auto('{w}/dispositivos.csv'))) AS usuario_sin_reloj
        FROM read_csv_auto('{w}/comidas.csv')
    """)

    # ---------------------------------------------------------------
    # Calories de Food.com: ¿por porción o por receta?
    # Si fuera por receta, la mediana crecería con RecipeServings.
    # ---------------------------------------------------------------
    mostrar("Calories según número de porciones", f"""
        SELECT RecipeServings AS porciones, count(*) AS recetas,
               median(Calories) AS calories_mediana
        FROM '{f}/recipes.parquet'
        WHERE RecipeServings IN (1, 2, 4, 6, 8, 12, 24)
        GROUP BY 1 ORDER BY 1
    """)
    mostrar("Correlación Calories–RecipeServings (1 a 50 porciones)", f"""
        SELECT round(corr(Calories, RecipeServings), 2) AS correlacion
        FROM '{f}/recipes.parquet' WHERE RecipeServings BETWEEN 1 AND 50
    """)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
