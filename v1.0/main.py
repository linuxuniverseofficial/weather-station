# main.py
# Sistema de Previsao Meteorologica - Uberaba MG
# Versao 6.0 - Display simplificado + NTP + MQTT robusto

import machine, gc, dht, math, BME280, ssd1306, esp, time, ntptime
esp.osdebug(None)
from time import sleep
from machine import Pin, I2C

# ─── CONFIGURACAO MQTT ─────────────────────────────────────
MQTT_BROKER    = "172.20.0.45"   # <<< IP do seu servidor MQTT
MQTT_PORT      = 1883
MQTT_TOPIC     = b"casa/meteo/uberaba"
MQTT_CLIENT    = b"esp8266_meteo"
MQTT_INTERVALO = 60               # publicar a cada N ciclos (1 ciclo = 1s)
NTP_INTERVALO  = 3600             # resync NTP a cada 1 hora
# ───────────────────────────────────────────────────────────

# Leituras
hum = 0; pres = 0; presA = 0; tempc = 0
altitude = 764

# Historico de pressao
presd1 = -1; presd2 = 0; presd3 = 0; presd4 = 0; presd5 = 0
presd6 = 0; presd7 = 0; presd8 = 0; presd9_aux = 0
humd1 = 0; humd2 = 0; humd3 = 0; humd4 = 0
humd5 = 0; humd6 = 0; humd7 = 0; humd8 = 0

weather = "Inicializando"
presd9 = 0; presd10 = 0
mqtt_contador = 0
ntp_contador  = 0
wifi_ok  = False
mqtt_ok  = False


# ─── NTP ───────────────────────────────────────────────────

def ntp_sync():
    try:
        ntptime.settime()
        return True
    except:
        return False

def get_hora():
    try:
        t = time.localtime()
        # UTC-3 Brasilia
        h = (t[3] - 3) % 24
        m = t[4]
        return "{:02d}:{:02d}".format(h, m)
    except:
        return "--:--"


# ─── WIFI ──────────────────────────────────────────────────

def check_wifi():
    global wifi_ok
    import network
    sta_if = network.WLAN(network.STA_IF)
    wifi_ok = sta_if.isconnected()
    return wifi_ok


# ─── MQTT ──────────────────────────────────────────────────

def mqtt_publish():
    global mqtt_ok
    if not check_wifi():
        mqtt_ok = False
        return
    try:
        import usocket
        from umqtt.simple import MQTTClient
        client = MQTTClient(MQTT_CLIENT, MQTT_BROKER, MQTT_PORT, keepalive=10)
        client.sock = usocket.socket()
        client.sock.settimeout(5)  # timeout de 5s no socket
        client.connect()
        payload = '{{"temp":{},"hum":{},"pres":{},"weather":"{}"}}'.format(
            tempc, hum, presA, weather
        )
        client.publish(MQTT_TOPIC, payload)
        client.disconnect()
        mqtt_ok = True
        gc.collect()
    except:
        mqtt_ok = False
        gc.collect()


# ─── SENSOR ────────────────────────────────────────────────

def read_sensor():
    global tempc, hum, pres, presA, altitude
    global presd1, presd2, presd3, presd4, presd5
    global presd6, presd7, presd8, presd9_aux, presd9, presd10
    global humd1, humd2, humd3, humd4, humd5, humd6, humd7, humd8

    try:
        tempc = bme.temperature
        tempc = tempc.replace("C", "")
        tempc = math.trunc(float(tempc))

        sensor.measure()
        hum = sensor.humidity()

        pres = bme.pressure
        pres = pres.replace("hPa", "")
        presA = math.trunc(float(pres))

        presd1 += 1

        if presd1 > 59:
            presd1 = -1
            presd9 += 1

        if presd9 == 5:
            presd2 = presA; humd1 = hum
        if presd9 == 10:
            presd3 = presd2; presd2 = presA
            humd2 = humd1; humd1 = hum
        if presd9 == 15:
            presd4 = presd3; presd3 = presd2; presd2 = presA
            humd3 = humd2; humd2 = humd1; humd1 = hum
        if presd9 == 20:
            presd5 = presd4; presd4 = presd3; presd3 = presd2; presd2 = presA
            humd4 = humd3; humd3 = humd2; humd2 = humd1; humd1 = hum
        if presd9 == 25:
            presd6 = presd5; presd5 = presd4; presd4 = presd3
            presd3 = presd2; presd2 = presA
            humd5 = humd4; humd4 = humd3; humd3 = humd2; humd2 = humd1; humd1 = hum
        if presd9 == 30:
            presd7 = presd6; presd6 = presd5; presd5 = presd4
            presd4 = presd3; presd3 = presd2; presd2 = presA
            humd6 = humd5; humd5 = humd4; humd4 = humd3
            humd3 = humd2; humd2 = humd1; humd1 = hum
        if presd9 == 35:
            presd8 = presd7; presd7 = presd6; presd6 = presd5
            presd5 = presd4; presd4 = presd3; presd3 = presd2; presd2 = presA
            humd7 = humd6; humd6 = humd5; humd5 = humd4
            humd4 = humd3; humd3 = humd2; humd2 = humd1; humd1 = hum
        if presd9 == 40:
            presd9_aux = presd8; presd8 = presd7; presd7 = presd6
            presd6 = presd5; presd5 = presd4; presd4 = presd3
            presd3 = presd2; presd2 = presA
            humd8 = humd7; humd7 = humd6; humd6 = humd5
            humd5 = humd4; humd4 = humd3; humd3 = humd2; humd2 = humd1; humd1 = hum
        if presd9 > 59:
            presd9 = 0
            presd10 += 1

        gc.collect()
    except:
        gc.collect()


# ─── PREVISAO ──────────────────────────────────────────────

def prevtemp():
    global tempc, hum, presA
    global presd2, presd3, presd4, presd5, presd6, presd9
    global humd1, humd2, weather

    try:
        if presd9 < 1:
            weather = "Aguardando..."
            gc.collect()
            return

        taxa = 0
        if presd9 >= 5 and presd2 > 0:
            taxa = ((float(presA) - float(presd2)) / 5) * 60

        taxa_hum = 0
        if presd9 >= 5 and humd1 > 0:
            taxa_hum = float(hum) - float(humd1)

        if taxa < -5:
            weather = "ALERTA:Tempest!" if int(hum) > 70 else "Pressao Despenca"
        elif taxa < -3:
            weather = "Tempest.Proxima" if int(hum) > 70 else "Pressao Caindo"
        elif int(presA) < 923:
            if int(hum) > 75:
                if taxa < -1.5:
                    weather = "Chuva 30-60min"
                elif taxa_hum > 5:
                    weather = "Chuva Iminente"
                else:
                    weather = "Chuva Provavel"
            elif int(hum) > 60:
                weather = "Nublado Umido"
            else:
                weather = "Nublado Seco"
        elif 923 <= int(presA) <= 933:
            if taxa < -2:
                weather = "Piorando" if int(hum) > 70 else "Mudando"
            elif taxa > 2:
                weather = "Melhorando"
            elif int(hum) > 75:
                weather = "Estavel Umido"
            else:
                weather = "Tempo Estavel"
        elif int(presA) > 933:
            if int(hum) < 50:
                weather = "Ceu Limpo"
            elif int(hum) > 70:
                weather = "Limpo+Umidade"
            else:
                weather = "Bom Tempo"
        else:
            weather = "Tempo Estavel"

        gc.collect()
    except:
        weather = "Erro"
        gc.collect()


# ─── DISPLAY ───────────────────────────────────────────────
# Layout:
# ┌──────────────────────────────┐
# │ 28C        │   11:47         │
# │ 52%        │                 │
# │ 916hPa     │   Wifi: On      │
# │ 764m       │                 │
# │ Tx: -1     │   MQTT: On      │
# ├──────────────────────────────┤
# │ Pressao Despenca             │
# └──────────────────────────────┘

def display():
    global tempc, hum, presA, presd2, presd9, presd10
    global weather, wifi_ok, mqtt_ok

    try:
        disp.fill(0)

        # divisores
        disp.vline(62, 0, 53, 1)
        disp.hline(0, 53, 128, 1)

        # ── Coluna esquerda ──
        disp.text(str(tempc) + "C",   0, 2)
        disp.text(str(hum) + "%",     0, 13)
        disp.text(str(presA) + "hPa", 0, 24)
        disp.text("764m",             0, 35)

        if presd9 >= 5 and presd2 > 0:
            taxa = int(((float(presA) - float(presd2)) / 5) * 60)
            taxa_str = "Tx:" + ("+" if taxa >= 0 else "") + str(taxa)
        else:
            taxa_str = "Tx:--"
        disp.text(taxa_str, 0, 46)

        # ── Coluna direita ──
        disp.text(get_hora(), 66, 5)

        disp.text("Wifi:", 66, 22)
        disp.text("On" if wifi_ok else "Off", 106, 22)

        disp.text("MQTT:", 66, 38)
        disp.text("On" if mqtt_ok else "Off", 106, 38)

        # ── Rodape ──
        disp.text(weather[:16], 0, 56)

        disp.show()
        gc.collect()
    except:
        gc.collect()


# ─── INICIALIZACAO ─────────────────────────────────────────

sensor = dht.DHT11(machine.Pin(13))
i2c    = I2C(scl=Pin(14), sda=Pin(12), freq=10000)
i2cc   = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))
bme    = BME280.BME280(i2c=i2c)
disp   = ssd1306.SSD1306_I2C(128, 64, i2cc)
disp.fill(0)
disp.show()

check_wifi()
if wifi_ok:
    ntp_sync()
    read_sensor()
    prevtemp()
    mqtt_publish()  # primeiro publish imediato

# ─── LOOP PRINCIPAL ────────────────────────────────────────

while True:
    read_sensor()
    prevtemp()
    check_wifi()
    display()

    mqtt_contador += 1
    if mqtt_contador >= MQTT_INTERVALO:
        mqtt_publish()
        mqtt_contador = 0

    ntp_contador += 1
    if ntp_contador >= NTP_INTERVALO:
        if wifi_ok:
            ntp_sync()
        ntp_contador = 0

    sleep(1)

# Fim
