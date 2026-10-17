import os
from dotenv import load_dotenv
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
API_KEY = os.environ.get("GEMINI_API_KEY", "")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    if not API_KEY:
        return jsonify({
            "error": "ابتدا کلید رایگان Gemini API را تنظیم کن."
        }), 503

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    lang = data.get("lang", "fa")

    if not message:
        return jsonify({"error": "پیام خالی است."}), 400

    languages = {
        "fa": "فارسی یا دری",
        "tr": "Türkçe",
        "en": "English"
    }
    language = languages.get(lang, "فارسی یا دری")

    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/interactions"
        )
        response = requests.post(
            url,
            headers={
                "x-goog-api-key": API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "model": "gemini-3.8-flash",
                "input": (
                    "You are Juma.AI, a helpful AI assistant. "
                    "Reply in " + language +
                    ". Be clear, honest and respectful.\\n\\n"
                    "User message: " + message
                )
            },
            timeout=90
        )
        result = response.json()

        if response.status_code != 200:
            error = result.get("error", {}).get(
                "message", "سرویس هوش مصنوعی پاسخ نداد."
            )
            return jsonify({"error": error}), 502

        answer = result.get("output_text", "")
        if not answer:
            for step in result.get("steps", []):
                if step.get("type") == "model_output":
                    for part in step.get("content", []):
                        if part.get("type") == "text":
                            answer += part.get("text", "")

        if not answer:
            return jsonify({
                "error": "پاسخ متنی از مدل دریافت نشد."
            }), 502

        return jsonify({"answer": answer})

    except requests.RequestException:
        return jsonify({
            "error": "اتصال اینترنت یا سرویس هوش مصنوعی مشکل دارد."
        }), 502
    except (KeyError, IndexError, TypeError):
        return jsonify({
            "error": "پاسخ نامعتبر از سرویس هوش مصنوعی دریافت شد."
        }), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
