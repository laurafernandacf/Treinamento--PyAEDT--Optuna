
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


hfss["Wpatch"] = "27.6056mm"
hfss["Wsub"] = "Wpatch*1.5"
hfss["Lpatch"] = "19.2896mm"
hfss["Lsub"] = "Lpatch*1.5"
hfss["Hsub"] = "1.65mm"
hfss["Slot"] = "1mm"
hfss["Yo"] = "5.9733mm"
hfss["Wfeed"] = "2.1000mm"


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

def print_tempo_execucao(start, mensagem="Tempo total"):
    elapsed = time.time() - start
    minutos, segundos = divmod(elapsed, 60)
    print(f"{mensagem}: {int(minutos)} min {segundos:.2f} s")
