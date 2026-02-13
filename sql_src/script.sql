-- Ver todos os estudos
SELECT * FROM studies;

-- Ver todos os trials
SELECT trial_id, study_id, state, datetime_start, datetime_complete
FROM trials;

-- Ver valores da função objetivo
SELECT * FROM trial_values;

-- Ver os valores de x testados
SELECT * FROM trial_params;
