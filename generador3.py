# -*- coding: utf-8 -*-
"""
Generador de dataset LegalTech PSET - Solicitudes
Versión robusta con reglas de negocio y calendario

Produce tres tablas coherentes:
  1. Solicitantes
  2. SolicitudesRecibidas
  3. TramiteSolicitudes

Reglas clave:
- Zona horaria: America/Lima
- Jornada: 08:30–17:30, con ligera campana centrada ~11:00
- Feriados fijos (Perú) excluidos
- Meses pico (2) aleatorios
- Última semana de diciembre (desde 25/12): solicitudes quedan "pendiente"
- Gaps:
   * fecha_evaluacion = presentacion + [1..3] días hábiles
   * fecha_registro   = presentacion + [1..5] días hábiles
   * fecha_informacion= registro    + [3..10] días hábiles
   * fecha_email      = informacion + [7..15] días hábiles
- Porcentajes objetivo (respetados en lo posible sin violar calendario):
   * evaluado: 75%–90% del total
   * registrado: 90%–95% de sí_cumple
   * info recibida: 70%–90% de registrados
   * email enviado: 75%–90% de info recibida
- Cobertura: todo solicitante aparece al menos una vez en SolicitudesRecibidas
- Códigos: P####, S#### (4 dígitos)

Salida: legaltech_pset_solicitudes.xlsx
Requiere: pandas, numpy, pytz, xlsxwriter

SEED=42 para reproducibilidad.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, date, timedelta, time
import pytz
from collections import Counter

# ==============================
# CONFIGURACIÓN GENERAL
# ==============================
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

TZ = pytz.timezone("America/Lima")
OUTPUT_PATH = "legaltech_pset_solicitudes.xlsx"

BUSINESS_START = time(8,30)
BUSINESS_END   = time(17,30)

# ==============================
# UTILIDADES DE FECHAS
# ==============================
def previous_year() -> int:
    return datetime.now(TZ).date().year - 1

def fixed_holidays_peru(year:int):
    """
    Feriados fijos de Perú. Tuplas (día, mes).
    Parche aplicado: crear date(year, month, day) en el orden correcto.
    """
    base = [
        (1, 1),   # Año Nuevo
        (1, 5),   # Día del Trabajo
        (29, 6),  # San Pedro y San Pablo
        (28, 7),  # Independencia
        (29, 7),  # Fiestas Patrias
        (30, 8),  # Santa Rosa de Lima
        (8, 10),  # Combate de Angamos
        (1, 11),  # Todos los Santos
        (8, 12),  # Inmaculada Concepción
        (25, 12)  # Navidad
    ]
    return {date(year, month, day) for (day, month) in base}

def business_days_of_year(year:int):
    start = date(year,1,1)
    end   = date(year,12,31)
    holidays = fixed_holidays_peru(year)
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5 and d not in holidays:
            days.append(d)
        d += timedelta(days=1)
    return days

def business_days_after(base_date:date, year:int):
    """Días hábiles estrictamente posteriores a base_date dentro del año."""
    return [d for d in business_days_of_year(year) if d > base_date]

def random_business_time_campana() -> time:
    """Hora 08:30–17:30 con campana centrada ~11:00 (sd ~1.5h), siempre dentro del rango."""
    start_seconds = BUSINESS_START.hour*3600 + BUSINESS_START.minute*60
    end_seconds   = BUSINESS_END.hour*3600   + BUSINESS_END.minute*60
    mu = 11*3600
    sigma = int(1.5 * 3600)
    for _ in range(1000):
        s = int(np.random.normal(mu, sigma))
        if start_seconds <= s <= end_seconds:
            h = s//3600; m=(s%3600)//60; st=s%60
            return time(h,m,st)
    # fallback uniforme si la campana falla
    s = random.randint(start_seconds, end_seconds)
    h = s//3600; m=(s%3600)//60; st=s%60
    return time(h,m,st)

def combine_local(d:date, t:time):
    return TZ.localize(datetime(d.year,d.month,d.day,t.hour,t.minute,t.second))

def pick_business_dt_within_gap(base_dt:datetime, min_days:int, max_days:int):
    """
    Devuelve datetime hábil posterior respetando el gap [min..max] días hábiles.
    Si no hay suficientes días hábiles disponibles dentro del año, devuelve None.
    """
    y = base_dt.astimezone(TZ).date().year
    base_date = base_dt.astimezone(TZ).date()
    after = business_days_after(base_date, y)
    if not after or len(after) < min_days:
        return None
    hi = min(max_days, len(after))
    gap = random.randint(min_days, hi)
    target_date = after[gap-1]  # gap=1 -> primer hábil posterior
    return combine_local(target_date, random_business_time_campana())

def strip_tz(df: pd.DataFrame) -> pd.DataFrame:
    """Quita tz para exportar a Excel sin que pandas/xlsxwriter se queje."""
    from pandas.api.types import is_datetime64_any_dtype
    out = df.copy()
    for col in out.columns:
        if is_datetime64_any_dtype(out[col]):
            try:
                if getattr(out[col].dtype, "tz", None) is not None:
                    out[col] = out[col].dt.tz_convert(None)
                out[col] = out[col].dt.tz_localize(None)
            except Exception:
                out[col] = pd.to_datetime(out[col], errors="coerce").dt.tz_localize(None)
    return out

# ==============================
# LISTAS EMBEBIDAS (nombres/apellidos)
# ==============================
# 90 masculinos, 90 femeninos, 20 neutros; 100 apellidos (comunes en AL)
nombres_m = [
    "Juan","Carlos","Luis","José","Miguel","Jorge","Pedro","Ricardo","Raúl","Fernando",
    "Diego","Andrés","Sergio","Eduardo","Héctor","Manuel","Rubén","Iván","Esteban","Gustavo",
    "Alberto","Óscar","Víctor","Hernán","Felipe","Mauricio","Nicolás","Adrián","Patricio","Agustín",
    "Emilio","Marco","César","Mario","Rafael","Tomás","Mateo","Bruno","Alan","Elías",
    "Cristian","Fabián","Hugo","Joel","Braulio","Camilo","Dante","Ezequiel","Gael","Iker",
    "Kevin","Leonardo","Matías","Pablo","Ramiro","Salvador","Tadeo","Ulises","Bastian","Rodrigo",
    "Sebastián","Thiago","Franco","Benjamín","Ivano","Gonzalo","Renato","Álvaro","Nahuel","Lautaro",
    "Marcelo","Baltasar","Félix","Ismael","Julián","Luciano","Maximiliano","Orlando","Rogelio","Santiago",
    "Teodoro","Vicente","Wilmer","Xavier","Yamil","Zaid","Abel","Borja","Darío","Emanuel"
]
nombres_f = [
    "María","Ana","Lucía","Valentina","Camila","Daniela","Paola","Carla","Mónica","Patricia",
    "Andrea","Gabriela","Silvia","Rocío","Claudia","Laura","Diana","Jessica","Sofía","Isabella",
    "Alejandra","Verónica","Natalia","Carolina","Fernanda","Elena","Irene","Beatriz","Noelia","Vanessa",
    "Cecilia","Jimena","Lorena","Marcela","Pilar","Rosa","Susana","Teresa","Yolanda","Zulema",
    "Agustina","Ariana","Bernarda","Bianca","Brenda","Constanza","Elisa","Fátima","Graciela","Inés",
    "Ivana","Julia","Karen","Liliana","Magdalena","Miranda","Nadia","Olga","Pamela","Queralt",
    "Raquel","Rebeca","Samanta","Tamara","Úrsula","Valeria","Wendy","Ximena","Yamila","Yesenia",
    "Zaira","Alicia","Bárbara","Camila Fernanda","Luz","Micaela","Nora","Ofelia","Paula","Ruth",
    "Selena","Tania","Violeta","Amalia","Catalina","Dominga","Ester","Fiorella","Gema","Helena"
]
nombres_neutros = [
    "Alex","Sam","Isis","Trinidad","Cruz","Franca","Luca","René","Jean","Mar",
    "Noa","Valen","Jordan","Sacha","Ariel","Dana","Eli","Morgan","Robin","Nicol"
]
apellidos = [
    "García","Martínez","López","González","Pérez","Rodríguez","Sánchez","Ramírez","Torres","Flores",
    "Díaz","Vásquez","Castro","Rojas","Morales","Alvarez","Herrera","Medina","Ruiz","Ortiz",
    "Chávez","Mendoza","Guerrero","Vargas","Jiménez","Reyes","Cruz","Moreno","Silva","Romero",
    "Suárez","Navarro","Ibáñez","Aguilar","Núñez","Paredes","Campos","Peña","Ramos","Guzmán",
    "Salazar","Soto","Cabrera","Vega","Fuentes","Carrillo","Montoya","Parra","Contreras","Mejía",
    "Bravo","Molina","Ríos","Cordero","Ibarra","Arroyo","Delgado","Valdez","Figueroa","Ponce",
    "León","Miranda","Calderón","Espinoza","Bautista","Palacios","Tapia","Zamora","Quispe","Huamán",
    "Cáceres","Escobar","Acosta","Bermúdez","Palomino","Barrios","Solano","Camacho","Peralta","Lozano",
    "Cardozo","Tello","Olivares","Cornejo","Benavides","Salinas","Montero","Chaparro","Mori","Arévalo",
    "Luna","Valencia","Terán","Cuenca","Rentería","Valle","Carrera","Becerra","Pizarro","Asmat"
]

# ==============================
# GENERADOR DE SOLICITANTES
# ==============================
def generar_solicitantes():
    n = random.randint(4000, 8000)
    codigos = [f"P{str(i).zfill(4)}" for i in range(1, n+1)]
    sexos = np.random.choice(["masculino","femenino","no_indico"], size=n, p=[0.49,0.49,0.02])

    hoy = datetime.now(TZ).date()
    min_birth = date(hoy.year-70, hoy.month, hoy.day)
    max_birth = date(hoy.year-18, hoy.month, hoy.day)
    delta_days = (max_birth - min_birth).days
    fechas_nac = [min_birth + timedelta(days=int(random.random()*delta_days)) for _ in range(n)]
    edades = np.array([(hoy - f).days // 365 for f in fechas_nac])

    # nombres: 1 o 2 palabras; si 2, distintas y compatibles con sexo/neutro
    nombres_final = []
    for s in sexos:
        if s == "masculino":
            fuente = nombres_m + nombres_neutros
        elif s == "femenino":
            fuente = nombres_f + nombres_neutros
        else:
            fuente = nombres_neutros + nombres_m[:30] + nombres_f[:30]
        if random.random() < 0.3:
            a, b = np.random.choice(fuente, size=2, replace=False)
            while a == b:
                a, b = np.random.choice(fuente, size=2, replace=False)
            nombres_final.append(f"{a} {b}")
        else:
            nombres_final.append(np.random.choice(fuente))

    # apellidos: 2 palabras distintas
    apes = []
    for _ in range(n):
        a, b = np.random.choice(apellidos, size=2, replace=False)
        apes.append(f"{a} {b}")

    # nivel de estudios con casos marginales
    def nivel_estudios(e):
        if e <= 21:
            base = ["sin_estudios","primaria","secundaria"]
            if random.random() < 0.05:  # marginal
                base = base + ["universitaria"]
            probs = [0.05,0.35,0.60] if len(base)==3 else [0.05,0.33,0.57,0.05]
        elif 22 <= e <= 26:
            base = ["primaria","secundaria","universitaria"]
            if random.random() < 0.05:
                base = base + ["post-grado"]
            probs = [0.15,0.50,0.35] if len(base)==3 else [0.14,0.48,0.35,0.03]
        else:
            base = ["primaria","secundaria","universitaria","post-grado"]
            probs = [0.10,0.30,0.45,0.15]
        return np.random.choice(base, p=np.array(probs)/np.sum(probs))

    niveles = [nivel_estudios(e) for e in edades]

    # ocupación
    ocupaciones = []
    for e in edades:
        if e <= 20:
            opciones = ["estudiante","trabajador","sin_empleo"]
            probs = [0.70,0.20,0.10]
        elif 21 <= e < 65:
            opciones = ["trabajador","sin_empleo"]
            probs = [0.82,0.18]
            if random.random() < 0.02:  # marginal estudiante >20
                opciones.append("estudiante"); probs.append(0.02)
        else:
            opciones = ["jubilado","trabajador","sin_empleo"]  # jubilado habilitado, otros baja prob.
            probs = [0.80,0.15,0.05]
        ocupaciones.append(np.random.choice(opciones, p=np.array(probs)/np.sum(probs)))

    return pd.DataFrame({
        "codigo_solicitante": codigos,
        "nombre": nombres_final,
        "apellido": apes,
        "sexo": sexos,
        "fecha_nacimiento": fechas_nac,
        "nivel_de_estudios": niveles,
        "ocupacion": ocupaciones
    })

# ==============================
# GENERADOR DE SOLICITUDES
# ==============================
def generar_solicitudes(df_solicitantes: pd.DataFrame):
    year = previous_year()
    n = max(random.randint(8000, 9999), len(df_solicitantes))

    # Códigos
    codigos = [f"S{str(i).zfill(4)}" for i in range(1, n+1)]

    # Asignar solicitantes: garantizar cobertura 1 vez cada uno, resto aleatorio
    todos = df_solicitantes["codigo_solicitante"].tolist()
    asignados = todos + list(np.random.choice(todos, size=n - len(todos), replace=True))
    random.shuffle(asignados)

    # Fechas de presentación con 2 meses pico
    dias = business_days_of_year(year)
    meses = list(range(1,13))
    pico1, pico2 = np.random.choice(meses, size=2, replace=False)
    pesos = np.array([2.5 if d.month in (pico1,pico2) else 1.0 for d in dias], dtype=float)
    pesos = pesos / pesos.sum()
    counts = np.random.multinomial(n, pesos)
    fechas = []
    for d, c in zip(dias, counts):
        for _ in range(c):
            fechas.append(combine_local(d, random_business_time_campana()))
    fechas = sorted(fechas)[:n]

    df = pd.DataFrame({
        "codigo_solicitud": codigos,
        "codigo_solicitante": asignados,
        "fecha_presentacion": fechas
    }).sort_values("fecha_presentacion").reset_index(drop=True)

    # Reenumerar códigos en estricto orden temporal
    df["codigo_solicitud"] = [f"S{str(i).zfill(4)}" for i in range(1, len(df)+1)]

    # Regla: última semana de diciembre => pendiente
    last_week = pd.Timestamp(year, 12, 25, tz=TZ)
    in_last_week = df["fecha_presentacion"] >= last_week

    # Viabilidad para evaluación (1..3 días hábiles después)
    viable_idx = []
    for i, row in df.iterrows():
        if in_last_week.iat[i]:
            continue
        if pick_business_dt_within_gap(row["fecha_presentacion"], 1, 3) is not None:
            viable_idx.append(i)

    # Objetivo evaluado 75–90%
    p_eval_obj = random.uniform(0.75, 0.90)
    n_eval_obj = int(round(p_eval_obj * len(df)))
    n_eval = min(n_eval_obj, len(viable_idx))

    estados = np.array(["pendiente"]*len(df), dtype=object)
    if n_eval > 0:
        chosen = np.random.choice(viable_idx, size=n_eval, replace=False)
        estados[chosen] = "evaluado"
    # forzar pendientes en última semana
    estados[in_last_week.values] = "pendiente"
    df["estado"] = estados

    # Fechas de evaluación y resultados
    fevals = [pd.NaT]*len(df)
    evaluados_idx = df.index[df["estado"]=="evaluado"].tolist()
    # sí_cumple 45–75% de evaluadas
    p_si = random.uniform(0.45, 0.75)
    n_si = int(round(p_si * len(evaluados_idx)))
    si_idx = set(np.random.choice(evaluados_idx, size=n_si, replace=False)) if n_si>0 else set()

    resultados = [""]*len(df)
    for i in evaluados_idx:
        fe = pick_business_dt_within_gap(df.at[i,"fecha_presentacion"], 1, 3)
        if fe is None:
            # seguridad extra: si ya no hay días hábiles, cae a pendiente
            df.at[i,"estado"] = "pendiente"
            resultados[i] = ""
            fevals[i] = pd.NaT
        else:
            fevals[i] = fe
            resultados[i] = "sí_cumple" if i in si_idx else "no_cumple"

    df["fecha_evaluacion"] = fevals
    df["resultado_evaluacion"] = resultados

    # Limpiar pendientes por si se degradó alguno
    pend_mask = df["estado"]=="pendiente"
    df.loc[pend_mask, "fecha_evaluacion"] = pd.NaT
    df.loc[pend_mask, "resultado_evaluacion"] = ""

    # Reordenar por fecha y reenumerar códigos
    df = df.sort_values("fecha_presentacion").reset_index(drop=True)
    df["codigo_solicitud"] = [f"S{str(i).zfill(4)}" for i in range(1, len(df)+1)]

    meses_pico = (pico1, pico2)
    return df, meses_pico

# ==============================
# GENERADOR DE TRÁMITE (sí_cumple)
# ==============================
def generar_tramite(df_solicitudes: pd.DataFrame):
    base = df_solicitudes[df_solicitudes["resultado_evaluacion"]=="sí_cumple"][["codigo_solicitud","fecha_presentacion"]].reset_index(drop=True)
    n = len(base)
    if n == 0:
        return pd.DataFrame(columns=["codigo_solicitud","estado_registro","fecha_registro","estado_informacion","fecha_informacion","estado_email","fecha_email"])

    # REGISTRO: seleccionar viables, luego aplicar objetivo 90–95%
    viable_reg = []
    for i in range(n):
        dt = pick_business_dt_within_gap(base.loc[i,"fecha_presentacion"], 1, 5)
        if dt is not None:
            viable_reg.append((i, dt))
    p_reg_obj = random.uniform(0.90, 0.95)
    n_reg_obj = int(round(p_reg_obj*n))
    n_reg = min(n_reg_obj, len(viable_reg))
    idx_reg = set()
    fechas_reg = [pd.NaT]*n
    if n_reg>0:
        chosen = np.random.choice(range(len(viable_reg)), size=n_reg, replace=False)
        for j in chosen:
            i, dt = viable_reg[j]
            idx_reg.add(i)
            fechas_reg[i] = dt

    estado_reg = np.array(["registrado" if i in idx_reg else "pendiente" for i in range(n)], dtype=object)

    # INFORMACIÓN: sobre registrados, viables con 3–10 días; objetivo 70–90%
    viable_info = []
    for i in idx_reg:
        dt = pick_business_dt_within_gap(fechas_reg[i], 3, 10)
        if dt is not None:
            viable_info.append((i, dt))
    p_info_obj = random.uniform(0.70, 0.90)
    n_info_obj = int(round(p_info_obj*len(idx_reg)))
    n_info = min(n_info_obj, len(viable_info))
    idx_info = set()
    fechas_info = [pd.NaT]*n
    if n_info>0:
        chosen = np.random.choice(range(len(viable_info)), size=n_info, replace=False)
        for j in chosen:
            i, dt = viable_info[j]
            idx_info.add(i)
            fechas_info[i] = dt
    estado_info = np.array([("recibida" if i in idx_info else ("pendiente" if i in idx_reg else "")) for i in range(n)], dtype=object)

    # EMAIL: sobre info recibida, viables con 7–15 días; objetivo 75–90%
    viable_email = []
    for i in idx_info:
        dt = pick_business_dt_within_gap(fechas_info[i], 7, 15)
        if dt is not None:
            viable_email.append((i, dt))
    p_email_obj = random.uniform(0.75, 0.90)
    n_email_obj = int(round(p_email_obj*len(idx_info)))
    n_email = min(n_email_obj, len(viable_email))
    idx_email = set()
    fechas_email = [pd.NaT]*n
    if n_email>0:
        chosen = np.random.choice(range(len(viable_email)), size=n_email, replace=False)
        for j in chosen:
            i, dt = viable_email[j]
            idx_email.add(i)
            fechas_email[i] = dt
    estado_email = np.array([("enviado" if i in idx_email else ("" if i not in idx_info else "pendiente")) for i in range(n)], dtype=object)

    df_tr = pd.DataFrame({
        "codigo_solicitud": base["codigo_solicitud"],
        "estado_registro": estado_reg,
        "fecha_registro": fechas_reg,
        "estado_informacion": estado_info,
        "fecha_informacion": fechas_info,
        "estado_email": estado_email,
        "fecha_email": fechas_email
    })
    return df_tr

# ==============================
# RESUMEN
# ==============================
def resumen_estadistico(df_sol, df_solic, df_tram, meses_pico):
    print("\n========= RESUMEN DEL DATASET =========")
    print(f"Solicitantes: {len(df_sol)}")
    print(f"SolicitudesRecibidas: {len(df_solic)}")
    print(f"TramiteSolicitudes: {len(df_tram)}")
    print("--------------------------------------")

    evals = df_solic[df_solic["estado"]=="evaluado"]
    pendientes = df_solic[df_solic["estado"]=="pendiente"]
    print(f"Evaluadas: {len(evals)} ({len(evals)/len(df_solic):.2%})")
    print(f"Pendientes: {len(pendientes)} ({len(pendientes)/len(df_solic):.2%})")

    res = Counter(evals["resultado_evaluacion"])
    if res:
        total = sum(res.values())
        if total > 0:
            for k,v in res.items():
                print(f"  {k}: {v} ({v/total:.2%})")

    print("--------------------------------------")
    print(f"Meses pico (aleatorios): {sorted(meses_pico)}")
    meses = pd.to_datetime(df_solic["fecha_presentacion"]).dt.month.value_counts().sort_index()
    print("Distribución mensual de presentaciones:")
    for m,v in meses.items():
        print(f"  Mes {m:02d}: {v}")

    print("--------------------------------------")
    print(f"Trámites (sí_cumple): {len(df_tram)} ({len(df_tram)/len(df_solic):.2%})")
    print("======================================\n")

# ==============================
# MAIN
# ==============================
def main():
    print("Generando dataset...")

    df_solicitantes = generar_solicitantes()
    df_solicitudes, meses_pico = generar_solicitudes(df_solicitantes)
    df_tramite = generar_tramite(df_solicitudes)

    # Exportar a Excel (datetimes sin tz)
    with pd.ExcelWriter(OUTPUT_PATH, engine="xlsxwriter", datetime_format="yyyy-mm-dd hh:mm") as writer:
        df_solicitantes.to_excel(writer, sheet_name="Solicitantes", index=False)
        strip_tz(df_solicitudes).to_excel(writer, sheet_name="SolicitudesRecibidas", index=False)
        strip_tz(df_tramite).to_excel(writer, sheet_name="TramiteSolicitudes", index=False)

    resumen_estadistico(df_solicitantes, df_solicitudes, df_tramite, meses_pico)
    print(f"Archivo Excel generado correctamente: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()