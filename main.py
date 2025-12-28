import time
import requests

# ================== CONFIG ==================

BOT_TOKEN = "8565694718:AAHdDrHKohkMOf0iv4xvTrVnvibFCRyDY7w"

CHANNEL_1M  = "-1003104422841"   # WinGo 1M Channel
CHANNEL_30S = "-1003639265979"   # WinGo 30S Channel

API_1M  = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

WIN_STICKER  = "CAACAgEAAxkBAAEgWZhpSXFsTfLLL2l0-3fOYyD57f2mwgACEAADSSyZT7GvEDht8CMlNgQ"
LOSS_STICKER = ""   # empty থাকলে skip

# ================== MEMORY ==================

games = {
    "1M": {
        "api": API_1M,
        "channel": CHANNEL_1M,
        "last_issue": None,
        "last_prediction": None,
        "loss": 0,
        "history": []
    },
    "30S": {
        "api": API_30S,
        "channel": CHANNEL_30S,
        "last_issue": None,
        "last_prediction": None,
        "loss": 0,
        "history": []
    }
}

# ================== TELEGRAM ==================

def md_escape(text):
    esc = r"_*[]()~`>#+-=|{}.!?"
    for c in esc:
        text = text.replace(c, "\\" + c)
    return text

def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "MarkdownV2"
        },
        timeout=10
    )

def send_sticker(chat_id, file_id):
    if not file_id:
        return
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendSticker",
        json={
            "chat_id": chat_id,
            "sticker": file_id
        },
        timeout=10
    )

# ================== NEXORA CORE ==================

def nexora_predict(history):
    if len(history) < 4:
        return None

    x1 = history[-1]
    x3 = history[-3]
    x4 = history[-4]

    if x3 == x4:
        return x1
    else:
        return "BIG" if x1 == "SMALL" else "SMALL"

def fetch_latest(api):
    try:
        r = requests.get(api, timeout=10)
        return r.json()["data"]["list"][0]
    except Exception:
        return None

# ================== MAIN LOOP ==================

print("BOT STARTED — NEXORA AI | OPTION B (Separated Channels)")

while True:
    for g in games.values():

        data = fetch_latest(g["api"])
        if not data:
            continue

        issue = data["issueNumber"]
        number = int(data["number"])
        actual = "BIG" if number >= 5 else "SMALL"

        if issue == g["last_issue"]:
            continue

        # -------- history --------
        g["history"].append(actual)
        if len(g["history"]) > 6:
            g["history"].pop(0)

        # -------- result --------
        if g["last_prediction"] is not None:
            if actual == g["last_prediction"]:
                send_sticker(g["channel"], WIN_STICKER)
                g["loss"] = 0
            else:
                send_sticker(g["channel"], LOSS_STICKER)
                g["loss"] += 1

        # -------- signal --------
        prediction = nexora_predict(g["history"])
        if prediction is None:
            g["last_issue"] = issue
            continue

        closed_period = int(issue[-4:])
        next_period = 1 if closed_period == 2880 else closed_period + 1

        show = "BIGGG" if prediction == "BIG" else "SMALL"
        step = f"STEP_{g['loss'] + 1}"

        msg = f"{next_period:04d}   {show}   {step}"
        send_message(g["channel"], f"*{md_escape(msg)}*")

        g["last_issue"] = issue
        g["last_prediction"] = prediction

    time.sleep(1)
