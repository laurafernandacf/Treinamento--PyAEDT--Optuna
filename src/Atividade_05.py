import optuna
import pandas as pd
import numpy as np
import tempfile
import os
import time
import sqlite3

from pyaedt import generate_unique_name
from ansys.aedt.core import Hfss

start_time = time.time()

tmpfold = tempfile.gettempdir()
temp_folder = os.path.join(tmpfold, generate_unique_name("Antenna"))
os.makedirs(temp_folder, exist_ok=True)

hfss = Hfss(
    version="2025.2",
    project="Patch_Optuna_Teste.aedt",
    solution_type="Modal",
    new_desktop_session=False,
    student_version=True
)

hfss.modeler.model_units = "mm"
p = hfss.modeler.primitives

hfss["Wpatch"] = "27.66mm"
hfss["Wsub"] = "Wpatch*1.5"
hfss["Lpatch"] = "19.6mm"
hfss["Lsub"] = "Lpatch*1.5"
hfss["Hsub"] = "1.65mm"
hfss["Slot"] = "1mm"
hfss["Yo"] = "5.3mm"
hfss["Wfeed"] = "2.4mm"

substract = p.create_box(
    ["-Wsub/2", "-Lsub/2", "0"],
    ["Wsub", "Lsub", "Hsub"],
    material="FR4_epoxy",
    name="Substract"
)

air_box = p.create_box(
    ["-Wpatch", "-Lpatch", "-Hsub-20mm"],
    ["2*Wpatch", "2*Lpatch", "Hsub+40mm"],
    material="vacuum",
    name="AirBox"
)
hfss.assign_radiation_boundary_to_objects("AirBox")

gnd = p.create_rectangle(
    orientation="XY",
    origin=["-Wsub/2", "-Lsub/2", "0"],
    sizes=["Wsub", "Lsub"],
    name="GND"
)
hfss.assign_finite_conductivity("GND")

patch = p.create_rectangle(
    orientation="XY",
    origin=["-Wpatch/2", "-Lpatch/2", "Hsub"],
    sizes=["Wpatch", "Lpatch"],
    name="Patch"
)

feed = p.create_rectangle(
    orientation="XY",
    origin=["-Wfeed/2", "-Lsub/2", "Hsub"],
    sizes=["Wfeed", "Lsub/2 - Lpatch/2"],
    name="Feed"
)

hfss.modeler.unite(["Patch", "Feed"])

slot1 = p.create_rectangle(
    orientation="XY",
    origin=["-Wfeed/2 - Slot", "-Lpatch/2", "Hsub"],
    sizes=["Slot", "Yo"],
    name="Slot1"
)

slot2 = p.create_rectangle(
    orientation="XY",
    origin=["Wfeed/2", "-Lpatch/2", "Hsub"],
    sizes=["Slot", "Yo"],
    name="Slot2"
)

hfss.modeler.subtract(
    blank_list=["Patch"],
    tool_list=["Slot1", "Slot2"],
    keep_originals=False
)

lumped = p.create_rectangle(
    orientation="XZ",
    origin=["-Wfeed/2", "-Lsub/2", "0"],
    sizes=["Hsub", "Wfeed"],
    name="Lumped"
)

hfss.lumped_port(
    assignment="Lumped",
    reference="GND",
    integration_line=hfss.AxisDir.ZNeg,
    impedance=50,
    name="Lumped_Port1"
)

hfss.assign_finite_conductivity("Patch")


setup = hfss.create_setup("MySetup")
setup.props["Frequency"] = "3.5GHz"
setup.update()

hfss.create_linear_step_sweep(
    setup="MySetup",
    unit="GHz",
    start_frequency=2,
    stop_frequency=4,
    step_size=0.02,
    sweep_type="Interpolating",
    name="Sweep",
    save_fields=True,
    save_rad_fields=True
)

# Função para calcular largura de banda de operação -10 db
def calcular_banda(solution_data, limite_db=-10):

    freq, s11 = solution_data.get_expression_data()

    freq = np.array(freq)
    s11 = np.array(s11)

    df = pd.DataFrame({
        "Frequency": freq,
        "S11": s11
    })

    df = df[(df["Frequency"] >= 2) & (df["Frequency"] <= 4)]

    if df.empty:
        return 0.0, 0.0

    # Frequência de ressonância (mínimo S11)
    idx_min = df["S11"].idxmin()
    f_res = df.loc[idx_min, "Frequency"]

    faixa = df[df["S11"] <= limite_db]

    if faixa.empty:
        bw = 0.0
    else:
        bw = float(faixa["Frequency"].max() - faixa["Frequency"].min())

    return bw, f_res


def objective(trial):

    Wpatch = trial.suggest_float("Wpatch", 26, 28)
    Lpatch = trial.suggest_float("Lpatch", 18, 21)
    Yo = trial.suggest_float("Yo", 5, 6)
    Wfeed = trial.suggest_float("Wfeed", 2, 3)

    hfss["Wpatch"] = f"{Wpatch}mm"
    hfss["Lpatch"] = f"{Lpatch}mm"
    hfss["Yo"] = f"{Yo}mm"
    hfss["Wfeed"] = f"{Wfeed}mm"

    hfss.modeler.refresh_all_ids()
    hfss.analyze_setup("MySetup")

    solution_data = hfss.post.get_solution_data(
        expressions=["dB(S(1,1))"],
        setup_sweep_name="MySetup : Sweep"
    )

    if solution_data is None:
        return 0.0

    bw, f_res = calcular_banda(solution_data)
    
    trial.set_user_attr("bw", bw)
    trial.set_user_attr("f_res", f_res)     
    
    f_target = 3.5
    delta = abs(f_res - f_target)

    tolerancia = 0.03 

    if delta > 0.15: # O casamento deve estar em uma frequência a 0.15 GHz de distância de 3.5 GHz, ou seja, de 3.35 até 3.65
        return -9999

    penalty = (delta / tolerancia)**2

    score = bw - 2.0 * penalty

    print(
        f"Trial {trial.number} → "
        f"BW={bw:.4f} GHz | "
        f"f_res={f_res:.3f} GHz | "
        f"Score={score:.4f}"
    )

    return score


study = optuna.create_study(study_name="patch_optimization", direction="maximize", storage="sqlite:///patch_optimization.db", 
                            load_if_exists=True)
study.optimize(objective, n_trials=10)

hfss.save_project()
hfss.release_desktop() 

elapsed = time.time() - start_time
print("Tempo total:", elapsed, "segundos")

best_trial = study.best_trial
best_score = study.best_value
best_params = study.best_params
best_bw = best_trial.user_attrs["bw"]
best_f_res = best_trial.user_attrs["f_res"]

print("RESULTADO FINAL DA OTIMIZAÇÃO\n")

print(f"Frequência de Ressonância: {best_f_res:.4f} GHz")
print(f"Melhor Bandwidth: {best_bw*1000:.2f} MHz")

fc = 3.5
bw_frac = best_bw / fc

print(f"Largura de Banda: {bw_frac*100:.2f} %")

print("\nDimensões da Melhor Antena:")
print(f"Wpatch = {best_params['Wpatch']:.4f} mm")
print(f"Lpatch = {best_params['Lpatch']:.4f} mm")
print(f"Yo     = {best_params['Yo']:.4f} mm")
print(f"Wfeed  = {best_params['Wfeed']:.4f} mm")


conn = sqlite3.connect("patch_optimization.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS best_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    best_bw REAL,
    best_bw_mhz REAL,
    fractional_bw REAL,
    Wpatch REAL,
    Lpatch REAL,
    Yo REAL,
    Wfeed REAL
)
""")

cursor.execute("""
INSERT INTO best_result (
    best_bw,
    best_bw_mhz,
    fractional_bw,
    Wpatch,
    Lpatch,
    Yo,
    Wfeed
) VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    best_bw,
    best_bw * 1000,
    best_bw / 3.5,
    best_params['Wpatch'],
    best_params['Lpatch'],
    best_params['Yo'],
    best_params['Wfeed']
))

conn.commit()
conn.close()

print("\nResultados salvos no SQLite com sucesso.")