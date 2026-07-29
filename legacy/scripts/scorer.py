def evaluate_etf(etf):

    score = 0

    if etf["monthly"]:
        score += 30

    if etf["capital_gain_ratio"] >= 90:
        score += 40

    if etf["performance_6m"] >= 10:
        score += 30

    return score