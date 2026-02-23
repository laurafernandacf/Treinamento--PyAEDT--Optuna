
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
import os
import time

from pyaedt import generate_unique_name
from ansys.aedt.core import Hfss
from ansys.aedt.core.modeler.advanced_cad.stackup_3d import Stackup3D


tmpfold = tempfile.gettempdir()
temp_folder = os.path.join(tmpfold, generate_unique_name("Antenna"))
os.makedirs(temp_folder, exist_ok=True)

hfss = Hfss(
    version="2025.2",
    project="Patch_Optuna_Teste.aedt",
    solution_type="Modal",
    new_desktop_session=True,
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
    sweep_type="Discrete",
    name="Sweep",
    save_fields=True,
    save_rad_fields=True
)

# Função com o objetivo de salvar o projeto e realizar a sua análise
def SaveAnalyseSetup(nameFolder = "AntennaPatch_Atividade05.aedt",setup = "MySetup"):
    hfss.save_project(os.path.join(temp_folder, nameFolder))
    hfss.analyze_setup(setup)

setup.update()

SaveAnalyseSetup("AntennaPatch_Atividade05.aedt")

# Plots

# Plots - Z_in
solutions = hfss.post.get_solution_data(
    expressions=hfss.get_traces_for_plot(category="Z"),
)
Data = solutions._init_solution_data_real()
index = 0
real1 = Data[list(Data.keys())[index]]

lista_freq = []
lista_reZ = []
dfVazioZGap = pd.DataFrame()

for row in real1:
    f = row[0]   # Frequência
    z = row[1]   # Parte real de Z
    lista_freq.append(f)
    lista_reZ.append(z)
dfVazioZGap.insert(0, "Frequency [GHz]", lista_freq, True)
dfVazioZGap.insert(1, "Re $Z_{in}$ (ohm)", lista_reZ, True)
print(dfVazioZGap)
dfVazioZGap.to_csv("Z_Real_Gap.csv", index=False)

# Extração do S11 (em dB)

solutions = hfss.post.get_solution_data(
    expressions=hfss.get_traces_for_plot(category="dB(S"),
)
solutions.enable_pandas_output = True
S_Real = solutions._init_solution_data_real()
index = 0
S_real1 = S_Real[list(S_Real.keys())[index]]

lista_freq_S = []
lista_S11 = []
dfRealGap = pd.DataFrame()

for row in S_real1:
    f = row[0]   # Frequência
    s = row[1]   # |S11| em dB
    lista_freq_S.append(f)
    lista_S11.append(s)

dfRealGap.insert(0, "Frequency [GHz]", lista_freq_S, True)
dfRealGap.insert(1, "|$S_{11}$| [dB]", lista_S11, True)
print(dfRealGap)
dfRealGap.to_csv("S11_Gap.csv", index=False)

indexValueMin = dfRealGap["|$S_{11}$| [dB]"].idxmin()
print(dfRealGap.loc[indexValueMin])

def Grafico(df, title, nameX="Frequency [GHz]", nameY="Result", colorGraf="red"):
    valorEixoY = df[nameY].to_numpy()
    valorEixoX = df[nameX].to_numpy()
    fig, ax = plt.subplots()
    ax.plot(valorEixoX, valorEixoY, color="red", linewidth = 2)
    ax.set_xlabel(nameX, fontsize = 10)
    ax.set_ylabel(nameY, fontsize = 10)
    plt.tick_params(axis="both", which="major", labelsize=10)
    plt.title(title, fontsize = 12)
    plt.show()

# Plotando impedância
Grafico(dfVazioZGap,"Impedância de entrada","Frequency [GHz]","Re $Z_{in}$ (ohm)")

# Plotando S11
Grafico(dfRealGap,"Coeficiente de reflexão","Frequency [GHz]","|$S_{11}$| [dB]")

def print_tempo_execucao(start, mensagem="Tempo total"):
    elapsed = time.time() - start
    minutos, segundos = divmod(elapsed, 60)
    print(f"{mensagem}: {int(minutos)} min {segundos:.2f} s")
