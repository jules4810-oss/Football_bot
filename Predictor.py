import os
import json
import numpy as np
from scipy.stats import poisson

BASE_AVG_GOALS = 1.35  # baseline expected goals per team
HOME_ADV = 1.12        # home advantage multiplier

def load_teams(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), 'teams.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('teams', {}), data.get('meta', {})

def get_team_rating(team_name, teams, default_key='Default'):
    # accept variants with spaces/underscores, case-insensitive
    key_variants = [team_name, team_name.replace(' ', '_'), team_name.replace('_', ' ')]
    for k in key_variants:
        if k in teams:
            return teams[k]
    for k in teams:
        if k.lower() == team_name.lower():
            return teams[k]
    return teams.get(default_key, {"attack":1.0, "defense":1.0})

def expected_goals(home, away, teams, meta=None):
    home_r = get_team_rating(home, teams)
    away_r = get_team_rating(away, teams)
    avg_attack = meta.get('avg_attack', 1.0) if meta else 1.0
    avg_defense = meta.get('avg_defense', 1.0) if meta else 1.0

    exp_home = BASE_AVG_GOALS * (home_r.get('attack',1.0)/avg_attack) * (away_r.get('defense',1.0)/avg_defense) * HOME_ADV
    exp_away = BASE_AVG_GOALS * (away_r.get('attack',1.0)/avg_attack) * (home_r.get('defense',1.0)/avg_defense)
    exp_home = max(0.05, exp_home)
    exp_away = max(0.05, exp_away)
    return exp_home, exp_away

def score_distribution(lambda_home, lambda_away, max_goals=6):
    probs = np.zeros((max_goals+1, max_goals+1))
    for i in range(max_goals+1):
        for j in range(max_goals+1):
            probs[i, j] = poisson.pmf(i, lambda_home) * poisson.pmf(j, lambda_away)
    total = probs.sum()
    if total > 0 and total < 0.9999:
        probs = probs / total
    return probs

def predict_match(home, away, teams=None, meta=None, max_goals=6):
    if teams is None:
        teams, meta = load_teams()
    lambda_home, lambda_away = expected_goals(home, away, teams, meta)
    probs = score_distribution(lambda_home, lambda_away, max_goals=max_goals)
    hi, hj = np.unravel_index(np.argmax(probs), probs.shape)
    most_probable = {"home_goals": int(hi), "away_goals": int(hj), "probability": float(probs[hi, hj])}
    home_win = float(np.tril(probs, -1).sum())
    draw = float(np.diag(probs).sum())
    away_win = float(np.triu(probs, 1).sum())
    return {
        "home": home,
        "away": away,
        "expected_goals": {"home": float(lambda_home), "away": float(lambda_away)},
        "most_likely_score": most_probable,
        "outcome_probabilities": {"home_win": home_win, "draw": draw, "away_win": away_win},
        "score_matrix": probs.tolist()
    }

if __name__ == '__main__':
    teams, meta = load_teams(
    print(predict_match('Paris_SG', 'Real_Madrid', teams, meta))
