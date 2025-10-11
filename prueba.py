import pandas as pd

# Ruta del archivo Excel
ruta_excel = "dataset.xlsx"  # cámbiala por la ubicación real

# Leer la hoja 'TramiteSolicitudes'
df = pd.read_excel(ruta_excel, sheet_name="TramiteSolicitudes")

# Definir la función equivalente a la fórmula de Excel
def calcular_estado_total(row):
    if row["estado_registro"] == "pendiente":
        return "en proceso en registro"
    elif row["estado_informacion"] == "pendiente":
        return "en proceso en información"
    elif row["estado_email"] == "pendiente":
        return "en proceso en email"
    else:
        return "finalizado"

# Crear nueva columna aplicando la lógica
df["estado_total_calculado"] = df.apply(calcular_estado_total, axis=1)

# Mostrar los primeros registros para verificar
print(df.head())

# (Opcional) Guardar el resultado en un nuevo archivo
df.to_excel("TramiteSolicitudes_actualizado.xlsx", index=False)

