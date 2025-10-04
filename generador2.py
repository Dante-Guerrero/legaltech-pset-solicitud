# -*- coding: utf-8 -*-
# Generador PSET LegalTech – versión robusta a fin de año y gaps estrictos
# Requiere: pandas numpy pytz xlsxwriter

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, time, date
import pytz
from collections import Counter

# ===================== Parámetros globales =====================
SEED = 42
OUTPUT_PATH = "legaltech_pset_solicitudes.xlsx"
TZ = pytz.timezone("America/Lima")
random.seed(SEED)
np.random.seed(SEED)

BUSINESS_START = time(8, 30)
BUSINESS_END   = time(17, 30)

# ===================== Listas embebidas =====================
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
assert len(nombres_m)==90 and len(nombres_f)==90 and len(nombres_neutros)==20 and len(apellidos)==100

# ===================== Utilidades de fechas =====================
def previous_year() -> int:
    return datetime.now(TZ).date().year - 1

def fixed_holidays_peru(year:int):
    fixed = [(1,1),(5,1),(6,29),(7,28),(7,29),(8,30),(10,8),(11,1),(12,8),(12,25)]
    return {date(year,m,d) for m,d in fixed}

def business_days_of_year(year:int):
    start = date(year,1,1)
    end   = date(year,12,31)
    holidays = fixed_holidays_peru(year)
    d = start
    days = []
    while d <= end:
        if d.weekday() < 5 and d not in holidays:
            days.append(d)
        d += timedelta(days=1)
    return days

def business_days_after(base_date:date, year:int):
    """Lista de días hábiles estrictamente posteriores a base_date dentro del año."""
    days = business_days_of_year(year)
    return [d for d in days if d > base_date]

def sample_time_business():
    start_seconds = BUSINESS_START.hour*3600 + BUSINESS_START.minute*60
    end_seconds   = BUSINESS_END.hour*3600   + BUSINESS_END.minute*60
    mu = 11*3600
    sigma = int(1.5*3600)
    for _ in range(1000):
        s = int(np.random.normal(mu, sigma))
        if start_seconds <= s <= end_seconds:
            h = s//3600; m=(s%3600)//60; st=s%60
            return time(h,m,st)
    s = random.randint(start_seconds, end_seconds)
    h = s//3600; m=(s%3600)//60; st=s%60
    return time(h,m,st)

def combine_local(d:date, t:time):
    return TZ.localize(datetime(d.year,d.month,d.day,t.hour,t.minute,t.second))

def pick_business_dt_within_gap(base_dt:datetime, min_days:int, max_days:int):
    """Devuelve una fecha-hora hábil posterior respetando el gap.
       Si no hay suficientes días hábiles, devuelve None."""
    year = base_dt.astimezone(TZ).date().year
    base_date = base_dt.astimezone(TZ).date()
    after = business_days_after(base_date, year)
    if not after:
        return None
    # días hábiles disponibles
    avail = len(after)
    # si no alcanza ni para min_days, no es posible
    if avail < min_days:
        return None
    # elegir gap factible
    hi = min(max_days, avail)
    gap = random.randint(min_days, hi)
    target_date = after[gap-1]  # gap=1 -> primer día hábil posterior
    return combine_local(target_date, sample_time_business())

def last_k_business_days_set(year:int, k:int):
    days = business_days_of_year(year)
    return set(days[-k:])

# ===================== Solicitantes =====================
def generar_solicitantes():
    n = random.randint(4000, 8000)
    codigos = [f"P{str(i).zfill(4)}" for i in range(1, n+1)]
    sexos = np.random.choice(["masculino","femenino","no_indico"], size=n, p=[0.49,0.49,0.02])

    today = datetime.now(TZ).date()
    min_birth = date(today.year-70, today.month, today.day)
    max_birth = date(today.year-18, today.month, today.day)
    delta_days = (max_birth - min_birth).days
    fnac = [min_birth + timedelta(days=int(random.random()*delta_days)) for _ in range(n)]
    edades = np.array([(today - f).days // 365 for f in fnac])

    # Nombres
    nombres = []
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
            nombres.append(f"{a} {b}")
        else:
            nombres.append(np.random.choice(fuente))

    # Apellidos
    apes = []
    for _ in range(n):
        a, b = np.random.choice(apellidos, size=2, replace=False)
        apes.append(f"{a} {b}")

    # Nivel de estudios
    def nivel_estudios(e):
        if e <= 21:
            base = ["sin_estudios","primaria","secundaria"]
            if random.random() < 0.05:
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

    nivel = [nivel_estudios(e) for e in edades]

    # Ocupación
    ocup = []
    for e in edades:
        if e <= 20:
            opciones = ["estudiante","trabajador","sin_empleo"]
            probs = [0.70,0.20,0.10]
        elif 21 <= e < 65:
            opciones = ["trabajador","sin_empleo"]
            probs = [0.82,0.18]
            if random.random() < 0.02:
                opciones.append("estudiante"); probs.append(0.02)
        else:
            opciones = ["jubilado","trabajador","sin_empleo"]
            probs = [0.80,0.15,0.05]
        ocup.append(np.random.choice(opciones, p=np.array(probs)/np.sum(probs)))

    return pd.DataFrame({
        "codigo_solicitante": codigos,
        "nombre": nombres,
        "apellido": apes,
        "sexo": sexos,
        "fecha_nacimiento": fnac,
        "nivel_de_estudios": nivel,
        "ocupacion": ocup
    })

# ===================== Fechas de presentación =====================
def generar_fechas_presentacion(n:int, year:int):
    days = business_days_of_year(year)
    meses = list(range(1,13))
    pico1, pico2 = np.random.choice(meses, size=2, replace=False)
    pesos = np.array([2.5 if d.month in (pico1,pico2) else 1.0 for d in days], dtype=float)
    pesos = pesos / pesos.sum()
    counts = np.random.multinomial(n, pesos)
    stamps = []
    for d, c in zip(days, counts):
        for _ in range(c):
            stamps.append(combine_local(d, sample_time_business()))
    stamps = sorted(stamps)[:n]
    return stamps, (pico1, pico2)

# ===================== SolicitudesRecibidas =====================
def generar_solicitudes(df_solicitantes: pd.DataFrame):
    year = previous_year()
    n_sol = max(random.randint(8000, 9999), len(df_solicitantes))

    fechas, meses_pico = generar_fechas_presentacion(n_sol, year)

    codigos = [f"S{str(i).zfill(4)}" for i in range(1, n_sol+1)]
    cod_solicitantes = df_solicitantes["codigo_solicitante"].tolist()
    asignados = cod_solicitantes + list(np.random.choice(cod_solicitantes, size=n_sol - len(cod_solicitantes), replace=True))

    df = pd.DataFrame({
        "codigo_solicitud": codigos,
        "codigo_solicitante": asignados,
        "fecha_presentacion": fechas
    }).sort_values("fecha_presentacion").reset_index(drop=True)

    df["codigo_solicitud"] = [f"S{str(i).zfill(4)}" for i in range(1, n_sol+1)]

    # Objetivo evaluadas
    p_eval_obj = random.uniform(0.75, 0.90)
    n_eval_obj = int(round(p_eval_obj * n_sol))

    # Empezamos todo como pendiente, y promoveremos solo casos viables
    estados = np.array(["pendiente"]*n_sol)

    # indices ordenados por fecha (ya está ordenado), probaremos promover respetando viabilidad
    viable_idx = []
    for i, row in df.iterrows():
        # ¿hay entre 1 y 3 días hábiles disponibles después de presentación?
        target = pick_business_dt_within_gap(row["fecha_presentacion"], 1, 3)
        if target is not None:
            viable_idx.append(i)

    if len(viable_idx) < n_eval_obj:
        # si no hay suficientes viables, nos quedamos con los que hay (mejor eso que inventar fechas)
        n_eval = len(viable_idx)
    else:
        n_eval = n_eval_obj

    # Elegir aleatoriamente n_eval viables y promoverlos
    chosen = set(np.random.choice(viable_idx, size=n_eval, replace=False))
    for i in chosen:
        estados[i] = "evaluado"

    df["estado"] = estados

    # Fecha de evaluación y resultado
    fevals = []
    resultados = []
    evaluados_idx = df.index[df["estado"]=="evaluado"].tolist()
    p_si = random.uniform(0.45, 0.75)
    n_si = int(round(p_si * len(evaluados_idx)))
    si_pick = set(np.random.choice(evaluados_idx, size=n_si, replace=False))

    for i, row in df.iterrows():
        if row["estado"] == "pendiente":
            fevals.append(pd.NaT)
            resultados.append("")
        else:
            fe = pick_business_dt_within_gap(row["fecha_presentacion"], 1, 3)
            # por construcción no debería ser None, pero doble seguro:
            if fe is None:
                df.at[i,"estado"] = "pendiente"
                fevals.append(pd.NaT)
                resultados.append("")
            else:
                fevals.append(fe)
                resultados.append("sí_cumple" if i in si_pick else "no_cumple")

    df["fecha_evaluacion"] = fevals
    df["resultado_evaluacion"] = resultados

    # Reordenar por fecha y reenumerar códigos para cumplir regla
    df = df.sort_values("fecha_presentacion").reset_index(drop=True)
    df["codigo_solicitud"] = [f"S{str(i).zfill(4)}" for i in range(1, len(df)+1)]

    return df, meses_pico

# ===================== Trámite (solo sí_cumple) =====================
def generar_tramite(df_solicitudes: pd.DataFrame):
    year = previous_year()
    base = df_solicitudes[df_solicitudes["resultado_evaluacion"]=="sí_cumple"][["codigo_solicitud","fecha_presentacion"]].reset_index(drop=True)
    n = len(base)
    if n == 0:
        return pd.DataFrame(columns=["codigo_solicitud","estado_registro","fecha_registro","estado_informacion","fecha_informacion","estado_email","fecha_email"])

    # Para cada fila decidimos estados solo si las fechas posteriores son viables
    estados_reg = np.empty(n, dtype=object)
    fechas_reg  = [pd.NaT]*n
    for i in range(n):
        fe = pick_business_dt_within_gap(base.loc[i,"fecha_presentacion"], 1, 5)
        if fe is None:
            estados_reg[i] = "pendiente"
        else:
            estados_reg[i] = "registrado"
            fechas_reg[i]  = fe

    # Ajustar porcentaje objetivo de registrado (90–95%) sin romper viabilidad
    p_reg_obj = random.uniform(0.90, 0.95)
    n_reg_obj = int(round(p_reg_obj*n))
    idx_reg = np.where(estados_reg=="registrado")[0]
    idx_pend = np.where(estados_reg=="pendiente")[0]
    if len(idx_reg) > n_reg_obj:
        # bajar algunos a pendiente (los que tengan fechas más pegadas al final preferentemente)
        drop = len(idx_reg) - n_reg_obj
        drop_idx = np.random.choice(idx_reg, size=drop, replace=False)
        estados_reg[drop_idx] = "pendiente"
        for j in drop_idx:
            fechas_reg[j] = pd.NaT
    elif len(idx_reg) < n_reg_obj:
        # subir algunos pendientes que sean viables
        need = n_reg_obj - len(idx_reg)
        # reintentar viabilidad por si acaso
        viables = []
        for j in idx_pend:
            fe = pick_business_dt_within_gap(base.loc[j,"fecha_presentacion"], 1, 5)
            if fe is not None:
                viables.append((j, fe))
        if len(viables) > 0:
            choose = [v[0] for v in viables[:need]]
            for j in choose:
                estados_reg[j] = "registrado"
                fechas_reg[j]  = pick_business_dt_within_gap(base.loc[j,"fecha_presentacion"], 1, 5)

    # Información
    estados_info = np.empty(n, dtype=object)
    fechas_info  = [pd.NaT]*n
    for i in range(n):
        if estados_reg[i] != "registrado":
            estados_info[i] = ""
            fechas_info[i]  = pd.NaT
            continue
        fi = pick_business_dt_within_gap(fechas_reg[i], 3, 10)
        if fi is None:
            estados_info[i] = "pendiente"
        else:
            # prob objetivo 70–90% recibida, pero si no hay fecha viable, se queda pendiente
            if random.random() < random.uniform(0.70, 0.90):
                estados_info[i] = "recibida"
                fechas_info[i]  = fi
            else:
                estados_info[i] = "pendiente"

    # Email
    estados_email = np.empty(n, dtype=object)
    fechas_email  = [pd.NaT]*n
    for i in range(n):
        if estados_info[i] != "recibida":
            estados_email[i] = ""
            fechas_email[i]  = pd.NaT
            continue
        fe = pick_business_dt_within_gap(fechas_info[i], 7, 15)
        if fe is None:
            estados_email[i] = "pendiente"
        else:
            if random.random() < random.uniform(0.75, 0.90):
                estados_email[i] = "enviado"
                fechas_email[i]  = fe
            else:
                estados_email[i] = "pendiente"

    df_tr = pd.DataFrame({
        "codigo_solicitud": base["codigo_solicitud"],
        "estado_registro": estados_reg,
        "fecha_registro": fechas_reg,
        "estado_informacion": estados_info,
        "fecha_informacion": fechas_info,
        "estado_email": estados_email,
        "fecha_email": fechas_email
    })

    # Limpieza (columna por columna, sin warnings)
    mask_reg_pend = df_tr["estado_registro"]=="pendiente"
    df_tr.loc[mask_reg_pend, "estado_informacion"] = ""
    df_tr.loc[mask_reg_pend, "fecha_informacion"]  = pd.NaT
    df_tr.loc[mask_reg_pend, "estado_email"]       = ""
    df_tr.loc[mask_reg_pend, "fecha_email"]        = pd.NaT

    mask_info_no_rec = df_tr["estado_informacion"]!="recibida"
    df_tr.loc[mask_info_no_rec, "estado_email"] = ""
    df_tr.loc[mask_info_no_rec, "fecha_email"]  = pd.NaT

    return df_tr

# ===================== Helper: quitar tz para Excel =====================
def strip_tz(df: pd.DataFrame):
    from pandas.api.types import is_datetime64_any_dtype
    for col in df.columns:
        if is_datetime64_any_dtype(df[col]):
            try:
                if getattr(df[col].dtype, "tz", None) is not None:
                    df[col] = df[col].dt.tz_convert(None)
                df[col] = df[col].dt.tz_localize(None)
            except Exception:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.tz_localize(None)
    return df

# ===================== Validaciones fuertes =====================
def validar_coherencia(df_solicitantes, df_solicitudes, df_tramite):
    # Unicidad y cobertura
    assert df_solicitantes["codigo_solicitante"].is_unique
    assert df_solicitudes["codigo_solicitud"].is_unique
    assert set(df_solicitantes["codigo_solicitante"]).issubset(set(df_solicitudes["codigo_solicitante"]))

    # Pendientes limpios
    mask_pend = df_solicitudes["estado"]=="pendiente"
    assert df_solicitudes.loc[mask_pend,"fecha_evaluacion"].isna().all()
    assert (df_solicitudes.loc[mask_pend,"resultado_evaluacion"]=="").all()

    # Horarios 08:30–17:30
    def in_hours(dt):
        if pd.isna(dt): return True
        t = dt.time()
        return BUSINESS_START <= t <= BUSINESS_END

    assert df_solicitudes["fecha_presentacion"].map(in_hours).all()
    assert df_solicitudes["fecha_evaluacion"].map(in_hours).all()

    if len(df_tramite) > 0:
        for c in ["fecha_registro","fecha_informacion","fecha_email"]:
            assert df_tramite[c].map(in_hours).all()

    # Gaps exactos
    def days_diff(a,b):
        if pd.isna(a) or pd.isna(b): return None
        return (b.date() - a.date()).days

    m_eval = df_solicitudes["estado"]=="evaluado"
    dif_eval = df_solicitudes.loc[m_eval].apply(lambda r: days_diff(r["fecha_presentacion"], r["fecha_evaluacion"]), axis=1)
    assert dif_eval.dropna().between(1,3).all()

    if len(df_tramite) > 0:
        pres_por_s = df_solicitudes.set_index("codigo_solicitud")["fecha_presentacion"]
        dif_reg = df_tramite.apply(lambda r: days_diff(pres_por_s[r["codigo_solicitud"]], r["fecha_registro"]), axis=1)
        ok_reg = dif_reg.dropna(); assert (ok_reg >= 1).all() and (ok_reg <= 5).all()

        dif_info = df_tramite.apply(lambda r: days_diff(r["fecha_registro"], r["fecha_informacion"]), axis=1)
        ok_info = dif_info.dropna(); assert (ok_info >= 3).all() and (ok_info <= 10).all()

        dif_email = df_tramite.apply(lambda r: days_diff(r["fecha_informacion"], r["fecha_email"]), axis=1)
        ok_email = dif_email.dropna(); assert (ok_email >= 7).all() and (ok_email <= 15).all()

# ===================== Main =====================
def main():
    df_solicitantes = generar_solicitantes()
    df_solicitudes, meses_pico = generar_solicitudes(df_solicitantes)
    df_tramite = generar_tramite(df_solicitudes)

    validar_coherencia(df_solicitantes, df_solicitudes, df_tramite)

    with pd.ExcelWriter(OUTPUT_PATH, engine="xlsxwriter", datetime_format="yyyy-mm-dd hh:mm") as writer:
        df_solicitantes.to_excel(writer, sheet_name="Solicitantes", index=False)
        strip_tz(df_solicitudes).to_excel(writer, sheet_name="SolicitudesRecibidas", index=False)
        strip_tz(df_tramite).to_excel(writer, sheet_name="TramiteSolicitudes", index=False)

    total_sol = len(df_solicitudes)
    evaluadas = (df_solicitudes["estado"]=="evaluado").sum()
    pendientes = (df_solicitudes["estado"]=="pendiente").sum()
    si = (df_solicitudes["resultado_evaluacion"]=="sí_cumple").sum()
    no = (df_solicitudes["resultado_evaluacion"]=="no_cumple").sum()
    meses = pd.to_datetime(df_solicitudes["fecha_presentacion"]).dt.month
    top2 = Counter(meses).most_common(2)

    print("Archivo generado:", OUTPUT_PATH)
    print("Solicitantes:", len(df_solicitantes))
    print("SolicitudesRecibidas:", total_sol, "| evaluadas:", evaluadas, "| pendientes:", pendientes)
    print("Resultado evaluadas -> sí_cumple:", si, "| no_cumple:", no)
    print("Meses pico (param):", meses_pico)
    print("Meses con más presentaciones (real):", top2)
    print("TramiteSolicitudes (sí_cumple):", len(df_tramite))

if __name__ == "__main__":
    main()