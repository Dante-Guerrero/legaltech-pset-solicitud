import pandas as pd
import numpy as np

# Archivo combinado existente (ya mergeado)
RUTA_ENTRADA = "merge_total.xlsx"
RUTA_SALIDA = "merge_con_fases_tiempo_seg.xlsx"

# Fecha de corte para pendientes
FECHA_CORTE = pd.Timestamp("2025-01-06 23:59:59")  # 6 de enero de 2025


def agregar_fases_tiempo_segundos(ruta_entrada: str, ruta_salida: str):
    # 1. Cargar el archivo combinado
    df = pd.read_excel(ruta_entrada)

    # 2. Asegurar conversión a datetime en columnas de fecha relevantes
    columnas_fecha = [
        "fecha_presentacion",
        "fecha_evaluacion",   # evaluación
        "fecha_registro",
        "fecha_informacion",
        "fecha_email",
    ]

    for col in columnas_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # -------------------------------------------------------------------------
    # 1) Tiempo: presentación → evaluación
    #    - Si hay fecha_evaluacion: evaluacion - presentacion
    #    - Si no hay fecha_evaluacion: FECHA_CORTE - presentacion
    # -------------------------------------------------------------------------
    df["tiempo_presentacion_a_evaluacion_seg"] = np.where(
        df["fecha_presentacion"].notna(),
        np.where(
            df["fecha_evaluacion"].notna(),
            (df["fecha_evaluacion"] - df["fecha_presentacion"]).dt.total_seconds(),
            (FECHA_CORTE - df["fecha_presentacion"]).dt.total_seconds()
        ),
        np.nan
    )

    # -------------------------------------------------------------------------
    # 2) Tiempo: evaluación → registro (solo cuando pasa evaluación)
    #    - Solo aplica si resultado_evaluacion == "sí_cumple" y hay fecha_evaluacion
    #    - Si hay registro: registro - evaluacion
    #    - Si no hay registro: FECHA_CORTE - evaluacion
    # -------------------------------------------------------------------------
    col_cumple = "resultado_evaluacion"
    if col_cumple not in df.columns:
        df[col_cumple] = np.nan  # por si acaso

    mask_eval_pasa = df["fecha_evaluacion"].notna() & (df[col_cumple] == "sí_cumple")

    df["tiempo_evaluacion_a_registro_seg"] = np.where(
        mask_eval_pasa,
        np.where(
            df["fecha_registro"].notna(),
            (df["fecha_registro"] - df["fecha_evaluacion"]).dt.total_seconds(),
            (FECHA_CORTE - df["fecha_evaluacion"]).dt.total_seconds()
        ),
        np.nan
    )

    # -------------------------------------------------------------------------
    # 3) Tiempo: registro → información
    #    - Si hay registro e informacion: informacion - registro
    #    - Si hay registro pero no informacion: FECHA_CORTE - registro
    #    - Si no hay registro: NaN
    # -------------------------------------------------------------------------
    mask_registro = df["fecha_registro"].notna()

    df["tiempo_registro_a_informacion_seg"] = np.where(
        mask_registro,
        np.where(
            df["fecha_informacion"].notna(),
            (df["fecha_informacion"] - df["fecha_registro"]).dt.total_seconds(),
            (FECHA_CORTE - df["fecha_registro"]).dt.total_seconds()
        ),
        np.nan
    )

    # -------------------------------------------------------------------------
    # 4) Tiempo: información → email
    #    - Si hay informacion y email: email - informacion
    #    - Si hay informacion pero no email: FECHA_CORTE - informacion
    #    - Si no hay informacion: NaN
    # -------------------------------------------------------------------------
    mask_info = df["fecha_informacion"].notna()

    df["tiempo_informacion_a_email_seg"] = np.where(
        mask_info,
        np.where(
            df["fecha_email"].notna(),
            (df["fecha_email"] - df["fecha_informacion"]).dt.total_seconds(),
            (FECHA_CORTE - df["fecha_informacion"]).dt.total_seconds()
        ),
        np.nan
    )

    # -------------------------------------------------------------------------
    # 5) Tiempo: presentación → cierre REAL
    #
    # Reglas de cierre real:
    #   - Cierra en evaluación si: resultado_evaluacion == "no_cumple" y hay fecha_evaluacion
    #   - Si no cerró en evaluación pero tiene fecha_email: cierra en fecha_email
    #   - Si no tiene ninguna de esas: no ha cerrado (NaT)
    # -------------------------------------------------------------------------
    cerrado_en_eval = (
        df["fecha_evaluacion"].notna() & (df[col_cumple] == "no_cumple")
    )

    cerrado_en_email = df["fecha_email"].notna() & ~cerrado_en_eval

    fecha_cierre_real = np.where(
        cerrado_en_eval,
        df["fecha_evaluacion"],
        np.where(
            cerrado_en_email,
            df["fecha_email"],
            pd.NaT
        )
    )

    fecha_cierre_real = pd.to_datetime(fecha_cierre_real, errors="coerce")
    df["fecha_cierre_real"] = fecha_cierre_real

    df["tiempo_presentacion_a_cierre_real_seg"] = np.where(
        df["fecha_presentacion"].notna() & df["fecha_cierre_real"].notna(),
        (df["fecha_cierre_real"] - df["fecha_presentacion"]).dt.total_seconds(),
        np.nan
    )

    # -------------------------------------------------------------------------
    # 6) Tiempo total de trámite
    #    - Si ha cerrado (fecha_cierre_real): usa ese cierre
    #    - Si NO ha cerrado: cuenta hasta FECHA_CORTE
    # -------------------------------------------------------------------------
    fecha_cierre_total = df["fecha_cierre_real"].copy()
    fecha_cierre_total = fecha_cierre_total.fillna(FECHA_CORTE)

    df["tiempo_total_tramite_seg"] = np.where(
        df["fecha_presentacion"].notna(),
        (fecha_cierre_total - df["fecha_presentacion"]).dt.total_seconds(),
        np.nan
    )

    # Marcar estado de cierre
    df["estado_cierre"] = np.where(
        cerrado_en_eval,
        "cerrado_en_evaluacion",
        np.where(
            cerrado_en_email,
            "cerrado_en_email",
            "pendiente_al_corte"
        )
    )

    # 7. Guardar archivo nuevo
    df.to_excel(ruta_salida, index=False)

    print(f"\nArchivo actualizado con fases de tiempo en segundos: {ruta_salida}\n")
    cols_demo = [
        "codigo_solicitud",
        "estado_cierre",
        "tiempo_presentacion_a_evaluacion_seg",
        "tiempo_evaluacion_a_registro_seg",
        "tiempo_registro_a_informacion_seg",
        "tiempo_informacion_a_email_seg",
        "tiempo_presentacion_a_cierre_real_seg",
        "tiempo_total_tramite_seg",
    ]
    cols_demo = [c for c in cols_demo if c in df.columns]
    print(df[cols_demo].head())


if __name__ == "__main__":
    agregar_fases_tiempo_segundos(RUTA_ENTRADA, RUTA_SALIDA)


