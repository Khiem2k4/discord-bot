from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot đang chạy ngon lành!"

def run():
    # Chạy web server ở cổng 0.0.0.0 để Render nhận diện
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()