
import os
import random
import re
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN")
SECRET_KEY = os.getenv("VK_SECRET_KEY")
GROUP_ID = os.getenv("VK_GROUP_ID")

def roll_weighted_dice(max_value, success_threshold):
    weights = [max(1, success_threshold - abs(i - success_threshold)) for i in range(1, max_value + 1)]
    return random.choices(range(1, max_value + 1), weights=weights, k=1)[0]

@app.route("/", methods=["POST"])
def callback():
    data = request.get_json()

    if data.get("type") == "confirmation":
        return VERIFY_TOKEN

    if data.get("type") == "message_new":
        message = data["object"]["message"]
        text = message.get("text", "").strip().lower()
        peer_id = message["peer_id"]

        if not text.startswith(("вальн", "дайс")):
            return "ok"

        response = handle_command(text)
        if response:
            send_message(peer_id, response)

    return "ok"

def send_message(peer_id, message):
    import requests

    token = os.getenv("VK_BOT_TOKEN")
    payload = {
        "peer_id": peer_id,
        "message": message,
        "random_id": random.randint(1, 1_000_000),
        "access_token": token,
        "v": "5.199"
    }
    requests.post("https://api.vk.com/method/messages.send", data=payload)

def handle_command(text):
    text = text.replace(",", " ")
    text = re.sub(r"[^\w\d\s\+\-dн]", " ", text)

    tokens = list(map(str.strip, text.split()))
    if not tokens or tokens[0] not in ("вальн", "дайс"):
        return ""

    if len(tokens) >= 4 and re.fullmatch(r"\(\d+\)", tokens[1]):
        count = int(tokens[1][1:-1])
        a, z = map(int, tokens[2:4])
        max_roll = a + z
        result_lines = []
        for j in range(count):
            roll = roll_weighted_dice(max_roll, a)
            status = "УСПЕХ" if roll <= a else "ПРОВАЛ"
            result_lines.append(f"Бросок {j+1}: {roll} из {max_roll} — {status}")
        return "\n".join(result_lines)

    numbers = [int(n) for n in tokens[1:] if n.isdigit()]
    if len(numbers) == 2:
        a, z = numbers
        max_roll = a + z
        roll = roll_weighted_dice(max_roll, a)
        status = "УСПЕХ" if roll <= a else "ПРОВАЛ"
        return f"{status}: {roll} из {max_roll}"

    return ""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
