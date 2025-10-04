# -*- coding: utf-8 -*-
# Generador de dataset para PSET LegalTech – Proceso de solicitudes
# Reglas: ver especificación de Dante. Zona horaria America/Lima. Feriados fijos incluidos.
# Dependencias: pandas, numpy, pytz, xlsxwriter
# pip install pandas numpy pytz xlsxwriter

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, time, date
import pytz
from collections import Counter

# ============ Parámetros ============
SEED = 42
OUTPUT_PATH = "legaltech_pset_solicitudes.xlsx"
TZ = pytz.timezone("America/Lima")

random.seed(SEED)
np.random.seed(SEED)

# ============ Listas embebidas ============
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

# ============ Utilidades de fechas ============

def previous_year():
    return datetime.now(TZ).date().year - 1

def fixed_holidays_peru(year:int):
    # Feriados fijos no movibles
    fixed = [
        (1,1),(5,1),(6,29),(7,28),(7,29),(8,30),(10,8),(11,1),(12,8),(12,25)
    ]
    return {date(year,m,d) for m,d in fixed}

def business_days_of_year(year:int, exclude_holidays=True):
    start = date(year,1,1)
    end = date(year,12,31)
    holidays = fixed_holidays_peru(year) if exclude_holidays else set()
    d = start
    days = []
    while d <= end:
        if d.weekday() < 5 and d not in holidays:
            days.append(d)
        d += timedelta(days=1)
    return days

def sample_time_business():
    # 08:30–17:30 con campana centrada ~11:00, sd 1.5h
    start_seconds = 8*3600 + 30*60
    end_seconds   = 17*3600 + 30*60
    mu = 11*3600
    sigma = int(1.5*3600)
    for _ in range(1000):
        s = int(np.random.normal(mu, sigma))
        if start_seconds <= s <= end_seconds:
            h = s//3600; m=(s%3600)//60; st=s%60
            return time(h,m,st)
    # fallback
    s = random.randint(start_seconds, end_seconds)
    h = s//3600; m=(s%3600)//60; st=s%60
    return time(h,m,st)

def combine_local(d:date, t:time):
    return TZ.localize(datetime(d.year,d.month,d.day,t.hour,t.minute,t.second))

def next_business_datetime(after_dt:datetime, year:int):
    # Siguiente timestamp hábil posterior a after_dt, en jornada 08:30–17:30
    d = after_dt.astimezone(TZ).date()
    days = business_days_of_year(year, exclude_holidays=True)

    # Intentar mismo día
    if d in days and after_dt.time() < time(17,30):
        min_dt = max(after_dt + timedelta(minutes=30), combine_local(d, time(8,30)))
        end_dt = combine_local(d, time(17,30))
        if min_dt < end_dt:
            for _ in range(200):
                t = sample_time_business()
                cand = combine_local(d, t)
                if min_dt < cand <= end_dt:
                    return cand
    # Día hábil siguiente
    days_after = [x for x in days if x > d]
    target = days_after[0] if days_after else days[-1]
    return combine_local(target, sample_time_business())

# ============ Generación de Solicitantes ============

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

    # Nombres (1 o 2 palabras). Si 2, no repetir dentro del mismo nombre.
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

    # Apellidos: dos palabras distintas
    apes = []
    for _ in range(n):
        a, b = np.random.choice(apellidos, size=2, replace=False)
        apes.append(f"{a} {b}")

    # Nivel de estudios por edad, con casos marginales
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
        probs = np.array(probs)/np.sum(probs)
        return np.random.choice(base, p=probs)

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
            if random.random() < 0.02:  # casos marginales estudiante >20
                opciones.append("estudiante"); probs.append(0.02)
        else:
            opciones = ["jubilado","trabajador","sin_empleo"]  # jubilado habilitado, otros con baja prob.
            probs = [0.80,0.15,0.05]
        p = np.array(probs)/np.sum(probs)
        ocup.append(np.random.choice(opciones, p=p))

    df = pd.DataFrame({
        "codigo_solicitante": codigos,
        "nombre": nombres,
        "apellido": apes,
        "sexo": sexos,
        "fecha_nacimiento": fnac,
        "nivel_de_estudios": nivel,
        "ocupacion": ocup
    })
    return df

# ============ Fechas de presentación y meses pico ============

def generar_fechas_presentacion(n:int, year:int):
    days = business_days_of_year(year, exclude_holidays=True)
    meses = list(range(1,13))
    pico1, pico2 = np.random.choice(meses, size=2, replace=False)
    pesos = np.array([2.5 if d.month in (pico1,pico2) else 1.0 for d in days], dtype=float)
    pesos = pesos / pesos.sum()
    counts = np.random.multinomial(n, pesos)
    stamps = []
    for d, c in zip(days, counts):
        for _ in range(c):
            t = sample_time_business()
            stamps.append(combine_local(d, t))
    stamps = sorted(stamps)[:n]
    return stamps, (pico1, pico2)

# ============ SolicitudesRecibidas ============

def generar_solicitudes(df_solicitantes: pd.DataFrame):
    year = previous_year()
    n_sol = max(random.randint(8000, 9999), len(df_solicitantes))

    # Timestamps + meses pico
    fechas, meses_pico = generar_fechas_presentacion(n_sol, year)

    # Códigos correlativos y asignación de solicitantes (cobertura 1-1 y resto aleatorio)
    codigos = [f"S{str(i).zfill(4)}" for i in range(1, n_sol+1)]
    cod_solicitantes = df_solicitantes["codigo_solicitante"].tolist()
    asignados = cod_solicitantes + list(np.random.choice(cod_solicitantes, size=n_sol - len(cod_solicitantes), replace=True))

    df = pd.DataFrame({
        "codigo_solicitud": codigos,
        "codigo_solicitante": asignados,
        "fecha_presentacion": fechas
    }).sort_values("fecha_presentacion").reset_index(drop=True)

    # Reescribir códigos en orden temporal para cumplir “código mayor => fecha no menor”
    df["codigo_solicitud"] = [f"S{str(i).zfill(4)}" for i in range(1, n_sol+1)]

    # Estados: evaluado 75–90%, pendientes concentrados al final 85–95%
    p_eval = random.uniform(0.75, 0.90)
    n_eval = int(round(p_eval * n_sol))
    n_pend = n_sol - n_eval
    estados = np.array(["evaluado"]*n_sol)
    pct_final = random.uniform(0.85, 0.95)
    n_final = int(pct_final * n_pend)
    estados[-n_final:] = "pendiente"
    pend_rest = n_pend - n_final
    if pend_rest > 0:
        idx_candidates = list(range(n_sol - n_final))
        idx_sel = np.random.choice(idx_candidates, size=pend_rest, replace=False)
        estados[idx_sel] = "pendiente"
    df["estado"] = estados

    # Fechas de evaluación
    fevals = []
    for i, row in df.iterrows():
        if row["estado"] == "pendiente":
            fevals.append(pd.NaT)
        else:
            fevals.append(next_business_datetime(row["fecha_presentacion"], year))
    df["fecha_evaluacion"] = fevals

    # Resultados: sí_cumple 45–75% de evaluados; no_cumple repartidos
    evaluados_idx = df.index[df["estado"]=="evaluado"].tolist()
    n_eval_ef = len(evaluados_idx)
    p_si = random.uniform(0.45, 0.75)
    n_si = int(round(p_si * n_eval_ef))
    si_idx = set(np.random.choice(evaluados_idx, size=n_si, replace=False))
    resultado = [""]*n_sol
    for idx in evaluados_idx:
        resultado[idx] = "sí_cumple" if idx in si_idx else "no_cumple"
    df["resultado_evaluacion"] = resultado

    return df, meses_pico

# ============ Trámite de solicitudes sí_cumple ============

def generar_tramite(df_solicitudes: pd.DataFrame):
    year = previous_year()
    base = df_solicitudes[df_solicitudes["resultado_evaluacion"]=="sí_cumple"][["codigo_solicitud","fecha_presentacion"]].reset_index(drop=True)
    n = len(base)
    if n == 0:
        return pd.DataFrame(columns=["codigo_solicitud","estado_registro","fecha_registro","estado_informacion","fecha_informacion","estado_email","fecha_email"])

    # Registro 90–95% “registrado”
    p_reg = random.uniform(0.90, 0.95)
    n_reg = int(round(p_reg*n))
    estados_reg = np.array(["registrado"]*n_reg + ["pendiente"]*(n-n_reg))
    np.random.shuffle(estados_reg)

    fechas_reg = []
    for i in range(n):
        if estados_reg[i] == "pendiente":
            fechas_reg.append(pd.NaT)
        else:
            fechas_reg.append(next_business_datetime(base.loc[i,"fecha_presentacion"], year))

    # Información 70–90% “recibida” solo si registrado
    estados_info, fechas_info = [], []
    for i in range(n):
        if estados_reg[i] != "registrado":
            estados_info.append(""); fechas_info.append(pd.NaT)
        else:
            if random.random() < random.uniform(0.70,0.90):
                estados_info.append("recibida")
                fechas_info.append(next_business_datetime(fechas_reg[i], year))
            else:
                estados_info.append("pendiente"); fechas_info.append(pd.NaT)

    # Email 75–90% “enviado” solo si info recibida
    estados_email, fechas_email = [], []
    for i in range(n):
        if estados_info[i] != "recibida":
            estados_email.append(""); fechas_email.append(pd.NaT)
        else:
            if random.random() < random.uniform(0.75,0.90):
                estados_email.append("enviado")
                fechas_email.append(next_business_datetime(fechas_info[i], year))
            else:
                estados_email.append("pendiente"); fechas_email.append(pd.NaT)

    return pd.DataFrame({
        "codigo_solicitud": base["codigo_solicitud"],
        "estado_registro": estados_reg,
        "fecha_registro": fechas_reg,
        "estado_informacion": estados_info,
        "fecha_informacion": fechas_info,
        "estado_email": estados_email,
        "fecha_email": fechas_email
    })

# ============ Helper: quitar tz para Excel ============
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

# ============ Run ============

def main():
    df_solicitantes = generar_solicitantes()
    df_solicitudes, meses_pico = generar_solicitudes(df_solicitantes)
    df_tramite = generar_tramite(df_solicitudes)

    # Validaciones duras
    assert df_solicitantes["codigo_solicitante"].is_unique
    assert df_solicitudes["codigo_solicitud"].is_unique
    assert set(df_solicitantes["codigo_solicitante"]).issubset(set(df_solicitudes["codigo_solicitante"]))

    # Exportar (datetimes naive para Excel)
    with pd.ExcelWriter(OUTPUT_PATH, engine="xlsxwriter", datetime_format="yyyy-mm-dd hh:mm") as writer:
        df_solicitantes.to_excel(writer, sheet_name="Solicitantes", index=False)
        strip_tz(df_solicitudes).to_excel(writer, sheet_name="SolicitudesRecibidas", index=False)
        strip_tz(df_tramite).to_excel(writer, sheet_name="TramiteSolicitudes", index=False)

    # Resumen de control
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
    print("Meses pico (aleatorios definidos):", meses_pico)
    print("Meses con más presentaciones (conteo real):", top2)
    print("TramiteSolicitudes (sí_cumple):", len(df_tramite))

if __name__ == "__main__":
    main()