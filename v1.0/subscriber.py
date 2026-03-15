#!/usr/bin/env python3
# subscriber_lpr.py
# Consome eventos LPR do Frigate via MQTT e grava em SQLite

import paho.mqtt.client as mqtt
import sqlite3
import json
import os
import time
from datetime import datetime

# ─── CONFIGURACAO ──────────────────────────────────────────
#MQTT_BROKER = "192.168.0.247"
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")

MQTT_PORT   = 1883
DB_PATH     = "/dados/lpr.db"
MQTT_TOPIC  = "frigate/tracked_object_update"

#MQTT_PORT   = int(os.environ.get("MQTT_PORT", 1883))
#DB_PATH     = os.environ.get("DB_PATH", "/dados/lpr.db")
# ───────────────────────────────────────────────────────────

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS placas (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            ts      DATETIME DEFAULT (datetime('now', 'localtime')),
            placa   TEXT,
            score   REAL,
            camera  TEXT,
            tipo    TEXT DEFAULT 'car'
        )
    """)
    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_ts ON placas (ts DESC)
    """)
    # Migração: adiciona coluna tipo se banco já existia sem ela
    try:
        con.execute("ALTER TABLE placas ADD COLUMN tipo TEXT DEFAULT 'car'")
        print("[DB] Coluna 'tipo' adicionada ao banco existente")
    except Exception:
        pass  # já existe
    con.commit()
    con.close()
    print("[DB] Banco inicializado em", DB_PATH)

def gravar(placa, score, camera, tipo):
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO placas (placa, score, camera, tipo) VALUES (?, ?, ?, ?)",
            (placa, score, camera, tipo)
        )
        con.commit()
        con.execute("""
            DELETE FROM placas
            WHERE ts < datetime('now', '-90 days', 'localtime')
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
        d = json.loads(msg.payload.decode("utf-8"))

        if d.get("type") != "lpr":
            return
        placa = d.get("plate")
        if not placa:
            return

        score  = float(d.get("score", 0))
        camera = str(d.get("camera", ""))
        tipo   = str(d.get("label", "car"))

        gravar(placa, score, camera, tipo)
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {tipo.upper()} | Placa: {placa}  Score: {score:.2f}  Camera: {camera}")

    except Exception as e:
        print("[MQTT] Erro ao processar mensagem:", e)
        print("       Payload:", msg.payload)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("[MQTT] Desconectado inesperadamente. Reconectando...")

if __name__ == "__main__":
    init_db()
    client = mqtt.Client(client_id="lpr_subscriber")
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
