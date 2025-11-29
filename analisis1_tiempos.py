import pandas as pd

# -------------------------------------------------
# OPCIÓN 1: partir de un archivo ya mergeado
# -------------------------------------------------
# Si tu archivo se llama distinto, cámbialo aquí:
RUTA_MERGE = "merge_total.xlsx"

def cargar_df_merge(ruta: str = RUTA_MERGE) -> pd.DataFrame:
    """Carga el archivo ya mergeado."""
    df = pd.read_excel(ruta)
    return df

# -------------------------------------------------
# ANÁLISIS DE TIEMPOS DE TRÁMITE
# -------------------------------------------------

def analizar_tiempos_tramite(df: pd.DataFrame) -> pd.DataFrame:
    """
    Toma el DataFrame ya mergeado y:
      - asegura que las fechas sean datetime
      - calcula tiempos entre etapas (en días)
      - imprime estadísticas descriptivas
      - devuelve el DataFrame con las nuevas columnas
    """

    # 1. Asegurar tipos datetime en las columnas relevantes
    columnas_fecha = [
        "fecha_presentacion",
        "fecha_registro",
        "fecha_informacion",
        "fecha_email",
    ]

    for col in columnas_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # 2. Calcular tiempos entre etapas (en días)
    df["tiempo_presentacion_a_registro"] = (
        df["fecha_registro"] - df["fecha_presentacion"]
    ).dt.days

    df["tiempo_registro_a_informacion"] = (
        df["fecha_informacion"] - df["fecha_registro"]
    ).dt.days

    df["tiempo_informacion_a_email"] = (
        df["fecha_email"] - df["fecha_informacion"]
    ).dt.days

    df["tiempo_total"] = (
        df["fecha_email"] - df["fecha_presentacion"]
    ).dt.days

    # 3. Resumen estadístico de los tiempos
    columnas_tiempo = [
        "tiempo_presentacion_a_registro",
        "tiempo_registro_a_informacion",
        "tiempo_informacion_a_email",
        "tiempo_total",
    ]

    print("\n=== RESUMEN ESTADÍSTICO DE TIEMPOS (días) ===\n")
    resumen = df[columnas_tiempo].describe()
    print(resumen)

    # 4. Algunos indicadores útiles adicionales
    print("\n=== KPIs RÁPIDOS ===")

    # Solo casos con tiempo_total válido
    completadas = df[df["tiempo_total"].notna()]

    if not completadas.empty:
        prom = completadas["tiempo_total"].mean()
        mediana = completadas["tiempo_total"].median()
        maximo = completadas["tiempo_total"].max()
        minimo = completadas["tiempo_total"].min()

        print(f"\nSolicitudes con trámite completo: {len(completadas)}")
        print(f"Tiempo total promedio: {prom:.2f} días")
        print(f"Tiempo total mediano: {mediana:.2f} días")
        print(f"Tiempo total mínimo: {minimo:.0f} días")
        print(f"Tiempo total máximo: {maximo:.0f} días")
    else:
        print("\nNo hay solicitudes con 'tiempo_total' calculado (todas tienen fechas incompletas).")

    # 5. Mostrar algunos ejemplos
    print("\n=== EJEMPLOS DE SOLICITUDES CON TIEMPOS CALCULADOS ===\n")
    columnas_mostrar = ["codigo_solicitud"] + columnas_tiempo
    columnas_mostrar = [c for c in columnas_mostrar if c in df.columns]
    print(df[columnas_mostrar].head(10))

    return df


if __name__ == "__main__":
    # OPCIÓN 1: partir de archivo mergeado
    df_merge = cargar_df_merge(RUTA_MERGE)
    df_con_tiempos = analizar_tiempos_tramite(df_merge)

    # Si quieres, puedes guardar el resultado:
    df_con_tiempos.to_excel("merge_con_tiempos.xlsx", index=False)
