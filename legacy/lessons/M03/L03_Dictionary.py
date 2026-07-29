etf = {
    "code": "00918",
    "name": "大華優利高填息30",
    "price": 22.56,
    "dividend": 0.84,
    "monthly": True
}

print(etf)
print(etf["code"])
print(etf["name"])
etf["expense_ratio"] = 0.30
print(etf)
etf["price"] = 22.88
print(etf["price"])
my_etf = {
    "code": "00919",
    "name": "群益台灣精選高息",
    "price": 23.45,
    "dividend": 0.72,
    "monthly": True
}

print("ETF代號：", my_etf["code"])
print("ETF名稱：", my_etf["name"])
print("價格：", my_etf["price"])
print("配息：", my_etf["dividend"])
etf_database = [
    {
        "code": "00918",
        "name": "大華優利高填息30",
        "price": 22.56
    },
    {
        "code": "00919",
        "name": "群益台灣精選高息",
        "price": 23.45
    }
]

print(etf_database)
my_portfolio = [
    {
        "code": "00918",
        "shares": 1000,
        "buy_price": 22.5
    },
    {
        "code": "00919",
        "shares": 2000,
        "buy_price": 24.1
    },
    {
        "code": "00713",
        "shares": 1500,
        "buy_price": 51.8
    }
]