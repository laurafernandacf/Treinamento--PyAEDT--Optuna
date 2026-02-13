# Atividade 3: Persistência + Critério de Parada

import optuna, time

def objective(trial):
    x = trial.suggest_float("x", -10, 10)
    return pow((pow(x, 2) + 6*x + 5),2)

# Criando ou carregando estudo persistente
study = optuna.create_study(
    study_name="Teste",
    direction="minimize",
    storage="sqlite:///experimento.db",
    load_if_exists=True
)

epsilon = 1e-7 # Critério de parada
max_trials = 5000 # Número máximo de tentativas

start_time = time.time()

trials = 0

# Loop manual para permitir parada antecipada
while trials < max_trials:
    study.optimize(objective, n_trials=1)
    trials += 1

    # Critério de parada
    if study.best_value < epsilon:
        print("\nCritério de parada atingido.")
        break

end_time = time.time()
tempo_total = end_time - start_time

x_best = study.best_params["x"]

# Resultados

print("\nRESULTADO")
print("Raiz encontrada:", x_best)
print("f(x) =", x_best**2 + 6*x_best + 5)
print("Melhor valor da função:", study.best_value) # [f(x)]^2 que é comparado com epsilon
print("Trials executados nessa rodada:", trials)
print("Total de trials acumulados no banco:", len(study.trials))
print("Tempo de execução:", tempo_total, "segundos")

#Teste
