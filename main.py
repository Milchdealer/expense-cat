#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict

import matplotlib.pyplot as plt
import numpy as np

WORKDIR = os.getenv("EXPENSE_CAT_WD", "./res/")
CATEGORIES = {
    "groceries": ["rewe", "edeka", "lidl", "asia markt"],
    "drug store": ["loreal", "dm drogeriemarkt sagt danke"],
    "clothing": ["zalando", "timberland", "uniqlo europe ltd"],
    "books and media": ["buecher"],
    "games": ["steam"],
    "spotify": ["spotify", "bastian lehmann"],
    "podcasts": ["wohlstand fuer alle"],
    "gehalt": ["verdienstabrechnung"],
    "electronics": ["alternate", "tink", "saturn", "mediamarkt", "rhinoshield", "ankertechno",
        "expert-ecom", "mmsecommerc", "digital save"],
    "server and hosting": ["netcup", "contabo", "domainfactory"],
    "office and cloud": ["microsoft"],
    "transportation": ["berliner verkehrsbetriebe"],
    "telecomm": ["klarmobil", "motion tm vertriebs gmbh", "vodafone"],
    "energy": ["enyway gmbh"],
    "luxus": ["myspirits"],
    "insurrance": ["versicherung", "proxalto", "volkswohlbund"],
    "rent": ["nio berlin"],
    "suzuka": ["suzuka"],
    "post": ["dhl ol"],
    "savings": ["fondssparplan", "wertpapiere dkb ag depot"],
    "account shifting": ["überweisung dkb visacard", "kreditkartenabrechnung"],
    "donations": ["wohnungsnotfallhilfe", "wwf sagt danke"],
    "netflix": ["netflix"],
    "amazon": ["amazon"],
    "Rundfunkbeitrag": ["ard zdf beitragsservice"],
    "furniture": ["moebel-kraft gmbh", "ikea"],
    "gifts": ["helmut und hiltrud brenner"]
}

def categorise_transaction(transaction: Dict) -> str:
    txt = transaction["reasonforpayment"].lower() +  "\n" + transaction["text"].lower()
    
    for cat in CATEGORIES.keys():
        for kw in CATEGORIES[cat]:
            if kw in txt:
                return cat

    return "None"


def load_transactions(conn, transactions: List):
    cur = conn.cursor()

    for trans in transactions:
        bdate = datetime.strptime(trans["bdate"], "%d.%m.%Y")
        vdate = datetime.strptime(trans["vdate"], "%d.%m.%Y")
        datum = datetime.strptime(trans["date"], "%d.%m.%Y")
        amount = float(trans["amount"])
        category = categorise_transaction(trans)
        cur.execute(
        """INSERT INTO transactions (
        category, bdate, vdate, postingtext, peer, reasonforpayment, 
        mandatereference, customerreferenz, peeraccount, peerbic, amount,
        datum, freitext) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT DO NOTHING;""",
        (category, bdate, vdate, trans["postingtext"], trans["peer"], trans["reasonforpayment"],
         trans["mandatereference"], trans["customerreferenz"], trans["peeraccount"],
         trans["peerbic"], amount, datum, trans["text"]))

    conn.commit()

def create_table_if_not_exists(conn):
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        category text, bdate date, vdate date, postingtext text, peer text,
        reasonforpayment text, mandatereference text, customerreferenz text,
        peeraccount text, peerbic text, amount real, datum date, freitext text,
        PRIMARY KEY (bdate, vdate, amount, peer, reasonforpayment));""")

    conn.commit()


def create_diagrams(conn):
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT strftime('%Y-%m', MIN(datum)), strftime('%Y-%m', MAX(datum)) FROM transactions;")
    dates = cur.fetchall()
    filename = os.path.join(WORKDIR, "diagram_%s-%s.png" % (str(dates[0][0]), str(dates[0][1])))

    cur.execute("""SELECT DISTINCT strftime('%Y-%m', datum) FROM transactions ORDER BY 1 ASC;""")
    dates = [x[0] for x in cur.fetchall()]
    cur.execute("""SELECT DISTINCT category FROM transactions WHERE category != "account shifting";""")
    categories = [x[0] for x in cur.fetchall()]

    plt.figure(figsize=(12, 12))
    plts = []
    ind = [x for x in range(len(dates))]
    for cat in categories:
        cur.execute("""SELECT strftime('%Y-%m', t.datum) datum, SUM(t.amount) amount
            FROM transactions t
            WHERE t.category != "account shifting" AND t.category = ?
            GROUP BY strftime('%Y-%m', t.datum)
            ORDER BY strftime('%Y-%m', t.datum) ASC;""",
            (cat,)
        )
        data = cur.fetchall()
        if len(data) != len(dates):
            present_dates = [x[0] for x in data]
            for d in dates:
                if d not in present_dates:
                    data.append((d, 0))
        data = [x[1] for x in data]
        bar = plt.bar(ind, data, 0.35)
        plts.append(bar)
        
    plt.grid(True)
    plt.xticks(ind, dates)
    plt.legend(plts, categories)
    plt.savefig(filename)


if __name__ == "__main__":
    conn = sqlite3.connect("./res/expense-cat.db", detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

    create_table_if_not_exists(conn)

    for d in os.listdir(WORKDIR):
        if os.path.isdir(os.path.join(WORKDIR, d)):
            for f in os.listdir(os.path.join(WORKDIR, d)):
                if f == "transactions.json":
                    with open(os.path.join(WORKDIR, d, f)) as transactions_file:
                        transactions = json.load(transactions_file)
                        load_transactions(conn, transactions)

    create_diagrams(conn)

    conn.close()
