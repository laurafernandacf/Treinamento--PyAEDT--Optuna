# Fase 02 - Integração Python + HFSS - Microlinha de Fita (Atividade 02)
# Laura

# Bibliotecas
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
import os
import time

from pyaedt import generate_unique_name
from ansys.aedt.core import Hfss
from ansys.aedt.core.modeler.advanced_cad.stackup_3d import Stackup3D
from win32com.client import constants

# Iniciando o contador de tempo
start_time = time.time()

# Parte do código para iniciar e encerrar o HFSS
tmpfold = tempfile.gettempdir()
temp_folder = os.path.join(tmpfold, generate_unique_name("Antenna"))
if not os.path.exists(temp_folder):
    os.mkdir(temp_folder)
non_graphical = os.getenv("PYAEDT_NON_GRAPHICAL","False").lower() in ("true", "1", "t")

# Criação da Estrutura

# Variáveis
Wpatch = 27.66
Wsub = Wpatch*1.5
Lpatch = 19.6
Lsub = Lpatch*1.5
Hsub = 1.65
Slot = 1
Yo = 5.3
Wfeed = 2.4
lambda_2 = 42.86


# Solution Type - Modal
hfss = Hfss(version="2025.2", project="Patch_Laura_Script.aedt", student_version=True, solution_type="Modal", non_graphical=non_graphical, new_desktop_session=True)

hfss.modeler.model_units = "mm" # Unidade de Medida

# Iniciando a montagem da estrutura da Patch
p = hfss.modeler.primitives

# Criação do substrato - "Substract"
substract = p.create_box([-Wsub/2, -Lsub/2, 0], [Wsub, Lsub, Hsub], material="FR4_epoxy", name="Substract") # Criando a box que representa o subtrato

# Criação da caixa de ar - "AirBox"
air_box = p.create_box([-lambda_2/2, -lambda_2/2, -lambda_2/2], [lambda_2, lambda_2, lambda_2], material="vacuum", name="AirBox") # Criando a box que representa a caixa de ar
hfss.assign_radiation_boundary_to_objects("AirBox") # Atribuindo radiação à caixa de ar - "Radiation"

# Criação do ground "GND"
gnd = p.create_rectangle(orientation="XY", origin=[-Wsub/2, -Lsub/2, 0], sizes=[Wsub, Lsub], name="GND") # Criando o retângulo que representa o GND
hfss.assign_finite_conductivity("GND") # Atribuindo condutividade finita ao GND - "Finite Conductivity"

# Criação da "Lumped Port"
lumped_port1 = p.create_rectangle(orientation="XZ", origin=[(-Wfeed/2)+Slot, -Lsub/2, 0], sizes=[Hsub, Wfeed], name="Lumped") # Criando o retângulo que representa a lumped port
integration_line1 = [[Slot, -Lsub/2, 0], [Slot, -Lsub/2, Hsub]] # Definindo a linha de integração da lumped port - "Integration Line"
port1 = hfss.lumped_port("Lumped", "GND", False, True, integration_line1, 50,"Lumped_Port1", False, False, True) # Atribuindo a excitação ao retângulo criado anteriormente (linha 60)


# Recortando a estrutura da Patch
patch = p.create_rectangle(
    orientation="XY",
    origin=[-Wpatch/2, -Lpatch/2, Hsub],
    sizes=[Wpatch, Lpatch],
    name="Patch"
) # Criação de um primeiro retângulo maior
ret2 = p.create_rectangle(
    orientation="XY", 
    origin=[(-Wfeed/2)+Slot, -Lsub/2, Hsub], 
    sizes=[Wfeed, Lsub/2-Lpatch/2], 
    name="Rectangle2"
) # Criação de um segundo retângulo, menor, que será a parte responsável por ligar a Patch à Lumped Port
hfss.modeler.unite([patch, ret2]) # Unindo o primeiro e o segundo retângulo criados
slot = p.create_rectangle(
    orientation="XY",
    origin=[-Wfeed/2, -Lpatch/2, Hsub],
    sizes=[Slot, Yo],
    name="Slot1"
) # Criação do primeiro slot que representa um dos furos da Patch
slot2 = p.create_rectangle(
    orientation="XY",
    origin=[Slot + Wfeed/2, -Lpatch/2, Hsub],
    sizes=[Slot, Yo],
    name="Slot2"
) # Criação do segundo slot que representa um dos furos da Patch
hfss.modeler.subtract(
    blank_list=["Patch"],
    tool_list=["Slot1", "Slot2"],
    keep_originals=False
) # Selecionando os slots e recortando-os da estrutura da Patch, gerando assim uma estrutura final

# MATERIAL
hfss.assign_finite_conductivity("Patch")

# Setup
setup = hfss.create_setup("MySetup")

def SingleFrequency(freq, convPasses, minPasses, maxPasses, maxDeltaS = 0.01, name="MySetup"):
    setup.props["Frequency"] = freq
    setup.props["MinimumConvergedPasses"] = convPasses
    setup.props["MinimumPasses"] = minPasses
    setup.props["MaximumPasses"] = maxPasses
    setup.props["MaxDeltaS"] = maxDeltaS
    setup.props["BasisOrder"] = -1 # Ativa o Mixed Order
    setup.props["EnableSmartInitialMesh"] = True
    setup.props["UseIterativeSolver"] = False # Ativa o Direct Solver
    setup.props["SaveRadFieldsOnly"] = True

def LinearStepSweep(fStart,fStop,stepSize=0.001, units="GHz",saveFields=True,saveRadFields=True):
    hfss.create_linear_step_sweep(
        setup=setup.name,
        unit=units,
        start_frequency=fStart,
        stop_frequency=fStop,
        step_size = stepSize,
        name = "Sweep",
        sweep_type = "Interpolating",
        save_fields = saveFields,
        save_rad_fields = saveRadFields
    )

# Função com o objetivo de salvar o projeto e realizar a sua análise
def SaveAnalyseSetup(nameFolder = "AntennaPatch.aedt",setup = "MySetup"):
    hfss.save_project(os.path.join(temp_folder, nameFolder))
    hfss.analyze_setup(setup)

# Chamando as funções

# SETUP:

# General
SingleFrequency("3.5GHz", 2, 2, 30, 0.01)

# Atualizando o Setup
setup.update()

# Sweep:
LinearStepSweep(1.5, 4.5)
# Save e executa:
SaveAnalyseSetup("Resultados_Patch_Com_Ajuste.aedt")

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
    
# Plotando comparação - manual x script

# Função para achar a coluna de S11 (robusta para HFSS)
def col_startswith(df, text):
    for col in df.columns:
        if col.startswith(text):
            return col
    raise ValueError(f"Coluna iniciando com '{text}' não encontrada")

# Leitura dos arquivos
df_manual = pd.read_csv("manual.csv")
df_script = pd.read_csv("script.csv")

# Frequência
freq_manual = df_manual["Freq [GHz]"]
freq_script = df_script["Freq [GHz]"]

# S11
s11_manual = df_manual[col_startswith(df_manual, "dB(S")]
s11_script = df_script[col_startswith(df_script, "dB(S")]

# Plot único com duas curvas
plt.figure(figsize=(8, 5))

plt.plot(freq_manual, s11_manual, label="S11 Manual")
plt.plot(freq_script, s11_script, label="S11 Script")

plt.xlabel("Frequência (GHz)")
plt.ylabel("S11 (dB)")
plt.title("Comparação S11 – Manual x Script")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.show()

print_tempo_execucao(start_time)