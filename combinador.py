import pandas as pd

# Cargar el archivo
file_path = "legaltech_pset_solicitudes.xlsx"

solicitantes = pd.read_excel(file_path, sheet_name="Solicitantes")
solicitudes = pd.read_excel(file_path, sheet_name="SolicitudesRecibidas")
tramite = pd.read_excel(file_path, sheet_name="TramiteSolicitudes")

# Merge 1: solicitantes + solicitudes
df = solicitudes.merge(
    solicitantes,
    on="codigo_solicitante",
    how="left"
)

# Merge 2: lo anterior + trámite
df_total = df.merge(
    tramite,
    on="codigo_solicitud",
    how="left"
)

print(df_total.head())
# Si quieres guardarlo en un archivo nuevo
df_total.to_excel("merge_total.xlsx", index=False)
