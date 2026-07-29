price = 22.56

if price > 20:
    print("價格大於20元")

price = 18
if price > 20:
    print("價格大於20元")
else:
    print("價格小於或等於20元")
etf = {
    "code": "00918",
    "monthly": True
}

if etf["monthly"]:
    print("這是一檔月配息ETF")
else:
    print("不是月配息ETF")
yield_rate = 8.3

if yield_rate >= 8:
    print("高殖利率ETF")
else:
    print("一般殖利率ETF")
capital_gain_ratio = 98

if capital_gain_ratio >= 90:
    print("符合76W策略")
else:
    print("不符合76W策略")
monthly = True
capital_gain_ratio = 95

if monthly and capital_gain_ratio >= 90:
    print("推薦投資")
else:
    print("不推薦")

etf_database = [
    {
        "code": "00918",
        "monthly": True,
        "capital_gain_ratio": 98
    },
    {
        "code": "00713",
        "monthly": False,
        "capital_gain_ratio": 85
    },
    {
        "code": "00919",
        "monthly": True,
        "capital_gain_ratio": 92
    }
]

print("符合條件的ETF")

for etf in etf_database:

    if etf["monthly"] and etf["capital_gain_ratio"] >= 90:
        print(etf["code"])