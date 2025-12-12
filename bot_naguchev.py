# bot_naguchev.py
import requests
import os

# === НАСТРОЙКИ ===
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "ваш_ключ")  # будем передавать через переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LEAGUE_MAP = {
    "PL": 2021, "SA": 2019, "PD": 2014, "BL1": 2002,
    "FL1": 2015, "ELC": 2016, "DED": 2003, "PPL": 2017,
    "BSA": 2013, "CL": 2001, "EC": 2018, "WC": 2000,
}

SEASON = 2025
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram настройки не заданы")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def get_avg_league(league_id):
    try:
        r = requests.get(f"{BASE_URL}/competitions/{league_id}/matches", 
                         headers=HEADERS, params={"season": SEASON})
        matches = [m for m in r.json().get("matches", []) 
                   if m["score"]["fullTime"]["home"] is not None]
        if not matches: return 2.5
        total = sum((m["score"]["fullTime"]["home"] or 0) + (m["score"]["fullTime"]["away"] or 0) for m in matches)
        return total / len(matches)
    except:
        return 2.5

def get_team_stats(team_id):
    try:
        r = requests.get(f"{BASE_URL}/teams/{team_id}/matches",
                         headers=HEADERS, params={"limit": 10, "status": "FINISHED", "season": SEASON})
        matches = r.json().get("matches", [])
        if not matches: return 0.0, 0.0
        scored = conceded = 0
        for m in matches:
            if m["homeTeam"]["id"] == team_id:
                scored += m["score"]["fullTime"]["home"] or 0
                conceded += m["score"]["fullTime"]["away"] or 0
            else:
                scored += m["score"]["fullTime"]["away"] or 0
                conceded += m["score"]["fullTime"]["home"] or 0
        n = len(matches)
        return scored / n, conceded / n
    except:
        return 0.0, 0.0

def main():
    message = "🎯 <b>Прогнозы по стратегии Нагучева</b>\n📅 " + str(SEASON) + "\n\n"
    signals = []

    for code, league_id in [("PL", 2021), ("SA", 2019), ("PD", 2014), ("BL1", 2002), ("CL", 2001)]:
        try:
            r = requests.get(f"{BASE_URL}/matches", headers=HEADERS,
                             params={"competitions": league_id, "status": "SCHEDULED", "limit": 3})
            matches = r.json().get("matches", [])[:2]
            league_avg = get_avg_league(league_id)

            for match in matches:
                home = match["homeTeam"]
                away = match["awayTeam"]
                hs, hc = get_team_stats(home["id"])
                as_, ac = get_team_stats(away["id"])
                total = max(0, (hs + ac) + (as_ + hc) - league_avg)
                total = round(total, 2)

                if total < 1.5:
                    signals.append(f"⚽ {home['name']} vs {away['name']}\n💯 Тотал: {total} → ✅ ТМ 1.5\n")
                elif total > 2.7:
                    signals.append(f"⚽ {home['name']} vs {away['name']}\n💯 Тотал: {total} → ✅ ТБ 2.5\n")
        except:
            continue

    if signals:
        message += "\n".join(signals)
    else:
        message += "ℹ️ Нет сильных сигналов сегодня."

    message += "\n\n⚠️ Прогноз не гарантирует выигрыш."

    print(message)
    send_telegram(message)

if __name__ == "__main__":
    main()