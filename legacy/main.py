print("welcome to use TW ETF AI Analyzer")

from config.settings import VERSION
print("Version:", VERSION)


from scripts.calculator import calculate_yield
yield_rate = calculate_yield(0.84,22.56)
print(f"殖利率：{yield_rate:.2f}%")


from scripts.scorer import evaluate_etf
etf = {
    "code":"00918",
    "monthly":True,
    "capital_gain_ratio":98,
    "performance_6m":12.5
}
score = evaluate_etf(etf)
print(score)


from scripts.calculator import calculate_total_cost
from scripts.portfolio import calculate_market_value

buy_cost = calculate_total_cost
market_value = calculate_market_value

print("買進成本：", buy_cost)
print("目前市值：", market_value)