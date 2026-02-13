# Atividade 2: Comparação de Otimizadores (Samplers)

import optuna
import time
from optuna.samplers import TPESampler, RandomSampler


# Função objetivo
def objective(trial):
    x = trial.suggest_float("x", -10, 10)
    return pow((pow(x, 2) + 6*x + 5),2)

# Função para rodar experimento com epsilon (critério de parada)
def run_study(sampler, nome_sampler, epsilon, max_trials=10000):

    study = optuna.create_study(
        direction="minimize",
        sampler=sampler
    )

    start_time = time.time()

    trials = 0 # Contador de tentativas iniciando em 0

    while trials < max_trials:
        study.optimize(objective, n_trials=1)
        trials += 1 # Aumentando o valor do contador a cada tentativa

        if study.best_value < epsilon: # Se o valor calculado pelo sampler for menor e estiver dentro do critério de parada, sai do while e encerra a busca
            break

    end_time = time.time()
    tempo_total = end_time - start_time

    return {
        "nome": nome_sampler,
        "melhor_x": study.best_params["x"],
        "melhor_valor": study.best_value,
        "tempo": tempo_total,
        "trials": trials
    }


# Definindo epsilon (critério de parada)
epsilon = 1e-4

# Executando os dois samplers
resultado_tpe = run_study(TPESampler(), "TPESampler", epsilon)
resultado_random = run_study(RandomSampler(), "RandomSampler", epsilon)

# Mostrando os resultados
print("\nRESULTADOS")

print(f"\nCritério de Parada: {epsilon}")

for resultado in [resultado_tpe, resultado_random]:
    print(f"\n{resultado['nome']}")
    print("Melhor x:", resultado["melhor_x"])
    print("Melhor valor da função f(x):", resultado["melhor_valor"])
    print("Número de tentativas:", resultado["trials"])
    print("Tempo total:", resultado["tempo"], "segundos")

if resultado_tpe["trials"] < resultado_random["trials"]:
    print("\nTPESampler convergiu com menos tentativas.\n")
else:
    print("\nRandomSampler convergiu com menos tentativas.\n")

