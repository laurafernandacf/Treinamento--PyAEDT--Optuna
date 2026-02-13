SELECT 
    t.number,
    v.value AS bandwidth,
    p.param_name,
    p.param_value
FROM trials t
JOIN trial_values v ON t.trial_id = v.trial_id
JOIN trial_params p ON t.trial_id = p.trial_id
WHERE t.state = 1
ORDER BY t.number;
