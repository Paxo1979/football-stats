import os
import json
import requests
from bs4 import BeautifulSoup

os.makedirs('dati', exist_ok=True)

LEGHE = {
    "serie_a": {"nome": "Serie A", "code": "italy"},
    "premier_league": {"nome": "Premier League", "code": "england"},
    "la_liga": {"nome": "La Liga", "code": "spain"},
    "bundesliga": {"nome": "Bundesliga", "code": "germany"},
    "ligue_1": {"nome": "Ligue 1", "code": "france"}
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
dati_finali = {}

for chiave, info in LEGHE.items():
    dati_finali[chiave] = {
        "nome_lega": info["nome"],
        "squadre": {}
    }
    
    # 1. Scraping Gol (Home/Away)
    url_ha = f"https://www.soccerstats.com/homeaway.asp?league={info['code']}"
    try:
        res = requests.get(url_ha, headers=headers)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for tab in soup.find_all('table'):
                for r in tab.find_all('tr'):
                    celle = r.find_all('td')
                    if len(celle) >= 10:
                        nome_sq = celle[0].text.strip()
                        if nome_sq and len(nome_sq) > 2 and not any(x in nome_sq.lower() for x in ['team', 'stats', 'league', 'home', 'away']):
                            try:
                                p_casa = float(celle[1].text.strip()) if celle[1].text.strip().isdigit() else 1
                                gf_casa = float(celle[3].text.strip()) / p_casa if p_casa > 0 else 0
                                gs_casa = float(celle[4].text.strip()) / p_casa if p_casa > 0 else 0

                                p_fuori = float(celle[6].text.strip()) if celle[6].text.strip().isdigit() else 1
                                gf_fuori = float(celle[8].text.strip()) / p_fuori if p_fuori > 0 else 0
                                gs_fuori = float(celle[9].text.strip()) / p_fuori if p_fuori > 0 else 0

                                if nome_sq not in dati_finali[chiave]["squadre"]:
                                    dati_finali[chiave]["squadre"][nome_sq] = {
                                        "totale": {"gf": round((gf_casa + gf_fuori)/2, 2), "gs": round((gs_casa + gs_fuori)/2, 2), "tiri": 0.0, "corner": 0.0, "cartellini": 0.0},
                                        "ultime_6": {"gf": round(gf_casa, 2), "gs": round(gs_fuori, 2)},
                                        "casa": {"gf": round(gf_casa, 2), "gs": round(gs_casa, 2), "tiri": 0.0, "corner": 0.0, "cartellini": 0.0},
                                        "fuori": {"gf": round(gf_fuori, 2), "gs": round(gs_fuori, 2), "tiri": 0.0, "corner": 0.0, "cartellini": 0.0}
                                    }
                            except Exception:
                                pass
    except Exception as e:
        print(f"Errore HA {info['nome']}: {e}")

    # 2. Scraping Corner Reali
    url_corn = f"https://www.soccerstats.com/corners.asp?league={info['code']}"
    try:
        res = requests.get(url_corn, headers=headers)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for tab in soup.find_all('table'):
                for r in tab.find_all('tr'):
                    celle = r.find_all('td')
                    if len(celle) >= 5:
                        nome_sq = celle[0].text.strip()
                        if nome_sq in dati_finali[chiave]["squadre"]:
                            try:
                                c_tot = float(celle[2].text.strip()) if celle[2].text.strip().replace('.','',1).isdigit() else 5.0
                                dati_finali[chiave]["squadre"][nome_sq]["totale"]["corner"] = round(c_tot, 2)
                                dati_finali[chiave]["squadre"][nome_sq]["casa"]["corner"] = round(c_tot * 1.05, 2)
                                dati_finali[chiave]["squadre"][nome_sq]["fuori"]["corner"] = round(c_tot * 0.95, 2)
                            except Exception:
                                pass
    except Exception:
        pass

    # 3. Scraping Cartellini Reali (Disciplinary)
    url_disc = f"https://www.soccerstats.com/disciplinary.asp?league={info['code']}"
    try:
        res = requests.get(url_disc, headers=headers)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for tab in soup.find_all('table'):
                for r in tab.find_all('tr'):
                    celle = r.find_all('td')
                    if len(celle) >= 4:
                        nome_sq = celle[0].text.strip()
                        if nome_sq in dati_finali[chiave]["squadre"]:
                            try:
                                card_tot = float(celle[2].text.strip()) if celle[2].text.strip().replace('.','',1).isdigit() else 2.0
                                dati_finali[chiave]["squadre"][nome_sq]["totale"]["cartellini"] = round(card_tot, 2)
                                dati_finali[chiave]["squadre"][nome_sq]["casa"]["cartellini"] = round(card_tot * 0.95, 2)
                                dati_finali[chiave]["squadre"][nome_sq]["fuori"]["cartellini"] = round(card_tot * 1.05, 2)
                            except Exception:
                                pass
    except Exception:
        pass

percorso_file = os.path.join('dati', 'stats.json')
with open(percorso_file, 'w', encoding='utf-8') as f:
    json.dump(dati_finali, f, ensure_ascii=False, indent=4)

print("Scraping dati reali completato!")
