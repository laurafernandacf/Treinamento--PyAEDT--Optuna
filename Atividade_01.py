# Atividade 1: Minimização de Funções

import optuna

def objective(trial):
    x = trial.suggest_float("x", -10, 10)
    return pow((pow(x, 2) + 6*x + 5),2)

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=1000)

x_best = study.best_params["x"]

print("Raiz encontrada:", x_best)
print("f(x) =", x_best**2 + 6*x_best + 5)
