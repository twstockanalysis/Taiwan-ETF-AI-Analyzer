etf_list = [
    "00918",
    "00919",
    "00713",
    "0056",
    "00982A"
]

for etf in etf_list:
    print("目前分析 ETF:", etf)
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
    },
    {
        "code": "00713",
        "name": "元大台灣高息低波",
        "price": 52.10
    }
]

for etf in etf_database:
    print(etf["code"])
    print(etf["name"])
    print(etf["price"])
    print("----------------")
etf_database = [
    {
        "code": "00918",
        "name": "大華優利高填息30",
        "price": 22.56,
        "dividend": 0.84
    },
    {
        "code": "00919",
        "name": "群益台灣精選高息",
        "price": 23.45,
        "dividend": 0.72
    },
    {
        "code": "00713",
        "name": "元大台灣高息低波",
        "price": 52.10,
        "dividend": 1.10
    }
]

print("========== ETF 報表 ==========")

for etf in etf_database:
    print("代號：", etf["code"])
    print("名稱：", etf["name"])
    print("價格：", etf["price"])
    print("配息：", etf["dividend"])
    print("----------------------------")