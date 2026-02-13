# Atividade 5: Otimização de Antena Patch Impressa com PyAEDT

# Atividade 05 - Otimização de Antena Patch com Optuna + PyAEDT
# Laura

import optuna
import pandas as pd
import tempfile
import os
import time

from pyaedt import generate_unique_name
from ansys.aedt.core import Hfss


# ==========================================
# FUNÇÃO PARA CALCULAR LARGURA DE BANDA
# ==========================================

def calcular_largura_banda(df):

    df_valid = df[df["S11"] <= -10]

    if df_valid.empty:
        return 0

    fmin = df_valid["Freq"].min()
    fmax = df_valid["Freq"].max()

    return fmax - fmin


# ==========================================
# FUNÇÃO OBJETIVO DO OPTUNA
# ==========================================

def objective(trial):

    start_time = time.time()

    # ===============================
    # VARIÁVEIS OTIMIZADAS
    # ===============================

    # Contínuas
    Wpatch = trial.suggest_float("Wpatch", 25, 35)
    Lpatch = trial.suggest_float("Lpatch", 15, 25)
    Yo = trial.suggest_float("Yo", 3, 8)

    # Discreta
    Slot = trial.suggest_int("Slot", 1, 3)

    # Categórica
    material_sub = trial.suggest_categorical(
        "material",
        ["FR4_epoxy", "Rogers5880"]
    )

    # Fixas
    Hsub = 1.65
    Wfeed = 2.4

    Wsub = Wpatch * 1.5
    Lsub = Lpatch * 1.5
    lambda_2 = 42.86

    tmpfold = tempfile.gettempdir()
    temp_folder = os.path.join(tmpfold, generate_unique_name("PatchOpt"))

    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)

    non_graphical = True

    hfss = None

    try:

        # ===============================
        # INICIANDO HFSS
        # ===============================

        hfss = Hfss(
            version="2025.2",
            student_version=True,
            solution_type="Modal",
            non_graphical=non_graphical,
            new_desktop_session=True
        )

        hfss.modeler.model_units = "mm"

        p = hfss.modeler.primitives

        # ===============================
        # GEOMETRIA
        # ===============================

        substract = p.create_box(
            [-Wsub/2, -Lsub/2, 0],
            [Wsub, Lsub, Hsub],
            material=material_sub
        )

        air_box = p.create_box(
            [-lambda_2/2]*3,
            [lambda_2]*3,
            material="vacuum"
        )

        hfss.assign_radiation_boundary_to_objects(air_box)

        gnd = p.create_rectangle(
            orientation="XY",
            origin=[-Wsub/2, -Lsub/2, 0],
            sizes=[Wsub, Lsub]
        )

        hfss.assign_finite_conductivity(gnd)

        lumped = p.create_rectangle(
            orientation="XZ",
            origin=[(-Wfeed/2)+Slot, -Lsub/2, 0],
            sizes=[Hsub, Wfeed]
        )

        integration_line = [
            [Slot, -Lsub/2, 0],
            [Slot, -Lsub/2, Hsub]
        ]

        hfss.lumped_port(
            lumped,
            gnd,
            integration_line=integration_line
        )

        patch = p.create_rectangle(
            orientation="XY",
            origin=[-Wpatch/2, -Lpatch/2, Hsub],
            sizes=[Wpatch, Lpatch]
        )

        slot1 = p.create_rectangle(
            orientation="XY",
            origin=[-Wfeed/2, -Lpatch/2, Hsub],
            sizes=[Slot, Yo]
        )

        slot2 = p.create_rectangle(
            orientation="XY",
            origin=[Slot + Wfeed/2, -Lpatch/2, Hsub],
            sizes=[Slot, Yo]
        )

        hfss.modeler.subtract(patch, [slot1, slot2])

        hfss.assign_finite_conductivity(patch)

        # ===============================
        # SETUP
        # ===============================

        setup = hfss.create_setup("Setup")

        setup.props["Frequency"] = "3.5GHz"
        setup.props["MaximumPasses"] = 10
        setup.update()

        hfss.create_linear_step_sweep(
            setup="Setup",
            start_frequency=2,
            stop_frequency=4,
            step_size=0.02,
            unit="GHz"
        )

        # ===============================
        # SIMULAÇÃO
        # ===============================

        hfss.analyze()

        # ===============================
        # EXTRAIR S11
        # ===============================

        solutions = hfss.post.get_solution_data(
            expressions=["dB(S(1,1))"]
        )

        data = solutions.data_real()

        freq = data.primary_sweep_values
        s11 = data.data_real()

        df = pd.DataFrame({
            "Freq": freq,
            "S11": s11
        })

        largura_banda = calcular_largura_banda(df)

        trial.set_user_attr("bandwidth", largura_banda)

        print(f"Trial {trial.number}")
        print(f"Bandwidth = {largura_banda:.4f} GHz")

        return largura_banda

    except Exception as e:

        print("Erro:", e)

        return 0

    finally:

        if hfss:
            hfss.release_desktop()

        print("Tempo trial:", time.time() - start_time)


# ==========================================
# ESTUDO OPTUNA
# ==========================================

study = optuna.create_study(

    direction="maximize",

    study_name="PatchOptimization",

    storage="sqlite:///patch_optuna.db",

    load_if_exists=True
)

study.optimize(objective, n_trials=5)


# ==========================================
# RESULTADO FINAL
# ==========================================

print("\n===== RESULTADO FINAL =====")

print("Melhor largura de banda:",
      study.best_value, "GHz")

print("Melhores parâmetros:")

for k, v in study.best_params.items():
    print(k, "=", v)