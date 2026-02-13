# Atividade 04: Visualização Avançada
# Persistência + Critério de Parada + Gráficos

import optuna
import time
import optuna.visualization as vis

# Função objetivo (Atividade 1)
# f(x) = x² + 6x + 5

def objective(trial):
    x = trial.suggest_float("x", -10, 10)
    return (x**2 + 6*x + 5)**2

# Criando ou carregando estudo persistente

study = optuna.create_study(
    study_name="Teste",
    direction="minimize",
    storage="sqlite:///experimento.db",
    load_if_exists=True
)

# Critério de parada
epsilon = 1e-7
max_trials = 5000

start_time = time.time()
trials = 0

while trials < max_trials:
    study.optimize(objective, n_trials=1)
    trials += 1

    if study.best_value < epsilon:
        print("\nCritério de parada atingido.")
        break

end_time = time.time()
tempo_total = end_time - start_time

# Resultados
x_best = study.best_params["x"]

print("\nRESULTADO")
print("Raiz encontrada:", x_best)
print("f(x) =", x_best**2 + 6*x_best + 5)
print("Melhor valor da função (f(x))²:", study.best_value)
print("Trials executados nesta rodada:", trials)
print("Total de trials acumulados no banco:", len(study.trials))
print("Tempo de execução:", tempo_total, "segundos")

# Plots

# Histórico de Otimização
fig1 = vis.plot_optimization_history(study)
fig1.show()
fig1.write_html(".\plot\historico_otimizacao.html")

# https://optuna.readthedocs.io/en/stable/reference/visualization/generated/optuna.visualization.plot_optimization_history.html

# Slice Plot
fig2 = vis.plot_slice(study)
fig2.show()
fig2.write_html(".\plot\slice_plot.html")

# https://optuna.readthedocs.io/en/stable/reference/visualization/generated/optuna.visualization.plot_slice.html

print("\nGráficos salvos como:")
print("- historico_otimizacao.html")
print("- slice_plot.html")
