# boot.py
# Sistema Meteorologico - Uberaba MG
# CONFIGURE: WIFI_SSID e WIFI_SENHA abaixo

import gc
import esp
import network
from time import sleep

esp.osdebug(None)

# ─── CONFIGURACAO WIFI ─────────────────────────────────────
WIFI_SSID  = "SEU_SSID_AQUI"
WIFI_SENHA = "SUA_SENHA_AQUI"
# ───────────────────────────────────────────────────────────

ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)

if not sta_if.isconnected():
    print("[WiFi] Conectando a '{}'...".format(WIFI_SSID))
    sta_if.connect(WIFI_SSID, WIFI_SENHA)
    timeout = 0
    while not sta_if.isconnected() and timeout < 20:
        sleep(1)
        timeout += 1

if sta_if.isconnected():
    print("[WiFi] Conectado! IP:", sta_if.ifconfig()[0])
else:
    print("[WiFi] FALHOU - continuando sem rede")

gc.collect()
