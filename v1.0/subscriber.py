#!/usr/bin/env python3
# subscriber.py
# Consome mensagens MQTT do ESP8266 e grava em SQLite
# Executado no servidor Linux

import paho.mqtt.client as mqtt
import sqlite3
import json
import os
import time
from datetime import datetime

# ─── CONFIGURACAO ──────────────────────────────────────────
#MQTT_BROKER = "172.20.0.45"
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")

MQTT_PORT   = 1883
DB_PATH     = "/dados/meteo.db"
MQTT_TOPIC  = "casa/meteo/uberaba"

#MQTT_PORT   = int(os.environ.get("MQTT_PORT", 1883))
#DB_PATH     = os.environ.get("DB_PATH", "/dados/meteo.db")
# ───────────────────────────────────────────────────────────


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            ts      DATETIME DEFAULT (datetime('now', 'localtime')),
            temp    REAL,
            hum     REAL,
            pres    REAL,
            weather TEXT
        )
    """)
    # Indice para consultas por data
    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_ts ON leituras (ts DESC)
    """)
    con.commit()
    con.close()
    print("[DB] Banco inicializado em", DB_PATH)


def gravar(temp, hum, pres, weather):
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO leituras (temp, hum, pres, weather) VALUES (?, ?, ?, ?)",
            (temp, hum, pres, weather)
        )
        con.commit()

        # Limpar registros antigos (manter 30 dias)
        con.execute("""
            DELETE FROM leituras
            WHERE ts < datetime('now', '-30 days', 'localtime')
        """)
        con.commit()
        con.close()
    except Exception as e:
        print("[DB] Erro ao gravar:", e)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Conectado ao broker")
        client.subscribe(MQTT_TOPIC)
        print("[MQTT] Inscrito em:", MQTT_TOPIC)
    else:
        print("[MQTT] Falha na conexao, rc =", rc)


def on_message(client, userdata, msg):
    try:
        raw = msg.payload.decode("utf-8")
        d = json.loads(raw)

        temp    = float(d.get("temp", 0))
        hum     = float(d.get("hum", 0))
        pres    = float(d.get("pres", 0))
        weather = str(d.get("weather", ""))

        gravar(temp, hum, pres, weather)

        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] T:{temp}°C  H:{hum}%  P:{pres}hPa  {weather}")

    except Exception as e:
        print("[MQTT] Erro ao processar mensagem:", e)
        print("       Payload recebido:", msg.payload)


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("[MQTT] Desconectado inesperadamente. Reconectando...")


if __name__ == "__main__":
    init_db()

    client = mqtt.Client(client_id="meteo_subscriber")
    client.on_connect    = on_connect
    client.on_message    = on_message
    client.on_disconnect = on_disconnect

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            print("[MQTT] Erro de conexao:", e, "— tentando novamente em 10s")
            time.sleep(10)
