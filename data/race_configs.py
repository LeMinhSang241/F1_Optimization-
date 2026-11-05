"""
Race configuration data for F1 Strategy Optimization.
Based on Italian GP (Monza 2023) and British GP (Silverstone 2023).
"""

RACE_CONFIGS = {
    "monza": {
        "name": "Italian GP (Monza)",
        "year": 2023,
        "n_laps": 53,
        "pit_loss": 23.2,        # seconds
        "alpha_fuel": 0.058,     # s/lap - lap time improvement per lap as fuel burns
        "gamma_track": 0.022,    # s/lap - lap time improvement as track rubbers in
        "fuel_load_kg": 100.0,   # kg starting fuel
        "fuel_burn_kg_per_lap": 1.6,
        "compounds": {
            "soft": {
                "name": "Soft (C4)",
                "code": 0,
                "t_base": 81.50,       # seconds baseline lap time
                "d1": 0.120,           # linear degradation coefficient (s/lap)
                "d2": 0.0050,          # quadratic degradation coefficient (s/lap^2)
                "l_max": 22,           # max safe stint length (laps)
                "color": "#FF1E1E",
            },
            "medium": {
                "name": "Medium (C3)",
                "code": 1,
                "t_base": 82.20,
                "d1": 0.070,
                "d2": 0.0020,
                "l_max": 35,
                "color": "#FFF200",
            },
            "hard": {
                "name": "Hard (C2)",
                "code": 2,
                "t_base": 83.00,
                "d1": 0.040,
                "d2": 0.0010,
                "l_max": 48,
                "color": "#EBEBEB",
            },
        },
        # Historical Verstappen strategy for comparison
        "verstappen_2023": {
            "strategy": [("medium", 26), ("hard", 27)],
            "description": "1-stop: Medium (26) -> Hard (27)",
        },
    },
    "silverstone": {
        "name": "British GP (Silverstone)",
        "year": 2023,
        "n_laps": 52,
        "pit_loss": 21.5,
        "alpha_fuel": 0.062,
        "gamma_track": 0.025,
        "fuel_load_kg": 100.0,
        "fuel_burn_kg_per_lap": 1.6,
        "compounds": {
            "soft": {
                "name": "Soft (C3)",
                "code": 0,
                "t_base": 89.20,
                "d1": 0.145,
                "d2": 0.0065,
                "l_max": 18,
                "color": "#FF1E1E",
            },
            "medium": {
                "name": "Medium (C2)",
                "code": 1,
                "t_base": 89.85,
                "d1": 0.085,
                "d2": 0.0028,
                "l_max": 30,
                "color": "#FFF200",
            },
            "hard": {
                "name": "Hard (C1)",
                "code": 2,
                "t_base": 90.60,
                "d1": 0.050,
                "d2": 0.0014,
                "l_max": 42,
                "color": "#EBEBEB",
            },
        },
    },
}

# Compound ordering for FIA compliance check (code values)
COMPOUND_CODES = {"soft": 0, "medium": 1, "hard": 2}
CODE_TO_COMPOUND = {0: "soft", 1: "medium", 2: "hard"}
COMPOUND_NAMES = {0: "Soft", 1: "Medium", 2: "Hard"}
COMPOUND_COLORS = {0: "#FF1E1E", 1: "#FFF200", 2: "#EBEBEB"}

# GA hyperparameters (from blueprint)
GA_PARAMS = {
    "population_size": 60,
    "max_generations": 150,
    "pc_initial": 0.85,       # initial crossover probability
    "pc_min": 0.50,
    "pm_initial": 0.25,       # initial mutation probability
    "pm_min": 0.05,
    "beta_risk": 50.0,        # cliff penalty coefficient (s/lap over limit)
    "phi_fia": 100_000.0,     # FIA violation penalty (seconds)
    "elite_size": 2,          # elitism: keep best N individuals
    "diversity_threshold": 0.15,  # trigger chaos injection
    "chaos_pm_multiplier": 2.5,
    # Warm-start pivot settings
    "warm_start_generations": 15,
    # Init weights
    "init_weight_1stop": 0.65,
    "init_weight_2stop": 0.30,
    "init_weight_3stop": 0.05,
    # Mutation type probabilities
    "micro_prob": 0.60,
    "meso_prob": 0.25,
    "macro_prob": 0.15,
}

# Safety Car parameters (for stochastic scenario)
SC_PARAMS = {
    "poisson_lambda": 0.3,          # Expected SC events per race
    "sc_lap_min": 5,                # SC cannot happen in first N laps
    "sc_lap_max_fraction": 0.85,    # SC cannot happen after this fraction of race
    "sc_duration_laps": (3, 8),     # (min, max) SC duration in laps
    "sc_speed_factor": 0.60,        # Fraction of normal speed under SC
    "vsc_speed_factor": 0.80,       # Fraction of normal speed under VSC
    "sc_pit_loss_reduction": 0.46,  # Pit loss multiplier under SC (23.2 -> ~12.5s)
    "vsc_pit_loss_reduction": 0.68, # Pit loss multiplier under VSC
    "monte_carlo_runs": 500,        # MC runs for stochastic fitness evaluation
}

# Dirty air parameters (multi-car simulation)
DIRTY_AIR_PARAMS = {
    "gap_threshold": 1.5,           # seconds gap within which dirty air applies
    "time_penalty_per_lap": 0.35,   # seconds added per lap when in dirty air
    "drs_gap_threshold": 1.0,       # seconds gap for DRS activation
    "drs_benefit": 0.5,             # seconds benefit from DRS per lap
}
