def say_hello():
    print("歡迎使用 TW ETF AI Analyzer")
say_hello()
def show_etf(code):
    print("ETF代號：", code)
show_etf("00918")
show_etf("00919")
show_etf("00713")
def show_etf(code, name):

    print("ETF代號：", code)

    print("ETF名稱：", name)
show_etf("00918","大華優利高填息30")
def calculate_yield(dividend, price):

    return dividend / price * 100
yield_rate = calculate_yield(0.84,22.56)

print(f"{yield_rate:.2f}%")
def is_good_etf(monthly, capital_gain_ratio):

    if monthly and capital_gain_ratio >=90:
        return True

    return False
result = is_good_etf(True,98)

print(result)
def evaluate_etf(etf):

    if etf["monthly"] and etf["capital_gain_ratio"]>=90:

        return "推薦"

    else:

        return "不推薦"
etf = {
    "code":"00918",
    "monthly":True,
    "capital_gain_ratio":98
}

print(evaluate_etf(etf))
etf_database = [

    {
        "code":"00918",
        "monthly":True,
        "capital_gain_ratio":98
    },

    {
        "code":"00713",
        "monthly":False,
        "capital_gain_ratio":85
    },

    {
        "code":"00919",
        "monthly":True,
        "capital_gain_ratio":92
    }

]
def evaluate_etf(etf):

    if etf["monthly"] and etf["capital_gain_ratio"]>=90:

        return "推薦"

    return "不推薦"
for etf in etf_database:

    print(etf["code"],evaluate_etf(etf))
def evaluate_etf(etf):

    score = 0

    if etf["monthly"]:
        score +=20

    if etf["capital_gain_ratio"]>=90:
        score +=30

    if etf["performance_6m"]>=10:
        score +=25

    if etf["fund_size"]>=100:
        score +=15

    if etf["expense_ratio"]<=0.35:
        score +=10

    return score
for etf in etf_database:

    print(etf["code"],evaluate_etf(etf))