# main.py
# Sistema de Previsao Meteorologica - Uberaba MG
# Versao 5.0 - WiFi + MQTT + Display OLED + BME280 + DHT11

import machine, gc, sys, uos, dht, math, BME280, ssd1306, esp, time
esp.osdebug(None)
from time import sleep
from machine import Pin, I2C, PWM

# ─── CONFIGURACAO MQTT ─────────────────────────────────────
MQTT_BROKER  = "192.168.1.100"   # <<< IP do seu servidor MQTT
MQTT_PORT    = 1883
MQTT_TOPIC   = b"casa/meteo/uberaba"
MQTT_CLIENT  = b"esp8266_meteo"
MQTT_INTERVALO = 60              # publicar a cada N ciclos (1 ciclo = 1s)
# ───────────────────────────────────────────────────────────

# Variáveis de leitura
hum = 0; pres = 0; presA = 0; tempc = 0
altitude = 764  # Altitude fixa - Sede de Uberaba

# Historico de pressao (hPa) em intervalos de 5min
presd1 = -1; presd2 = 0; presd3 = 0; presd4 = 0; presd5 = 0
presd6 = 0; presd7 = 0; presd8 = 0; presd9_aux = 0

# Historico de umidade (%)
humd1 = 0; humd2 = 0; humd3 = 0; humd4 = 0
humd5 = 0; humd6 = 0; humd7 = 0; humd8 = 0

weather = "Inicializando"
frequency = 5000
presd9 = 0; presd10 = 0
mqtt_contador = 0
mqtt_ok = False


# ─── MQTT ──────────────────────────────────────────────────

def mqtt_publish():
    global mqtt_ok
    try:
        from umqtt.simple import MQTTClient
        import network
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected():
            mqtt_ok = False
            return
        client = MQTTClient(MQTT_CLIENT, MQTT_BROKER, MQTT_PORT, keepalive=30)
        client.connect()
        payload = '{{"temp":{},"hum":{},"pres":{},"weather":"{}"}}'.format(
            tempc, hum, presA, weather
        )
        client.publish(MQTT_TOPIC, payload)
        client.disconnect()
        mqtt_ok = True
        gc.collect()
    except Exception as e:
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

        altitude = 764

        presd1 = presd1 + 1

        if presd1 > 59:
            presd1 = -1
            presd9 = presd9 + 1

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
            presd10 = presd10 + 1

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
            weather = str("Aguardando...")
            gc.collect()
            return

        taxa = 0
        if presd9 >= 5 and presd2 > 0:
            delta_pres = float(presA) - float(presd2)
            taxa = (delta_pres / 5) * 60

        taxa_hum = 0
        if presd9 >= 5 and humd1 > 0:
            taxa_hum = float(hum) - float(humd1)

        tend = 0
        if presd9 >= 30 and presd6 > 0:
            media_rec = (float(presd2) + float(presd3) + float(presd4)) / 3
            media_ant = float(presd6)
            tend = media_rec - media_ant

        if taxa < -5:
            weather = str("ALERTA:Tempestade!") if int(hum) > 70 else str("Pressao Despenca")
        elif taxa < -3:
            weather = str("Tempestade Proxima") if int(hum) > 70 else str("Pressao Caindo")
        elif int(presA) < 923:
            if int(hum) > 75:
                if taxa < -1.5:
                    weather = str("Chuva 30-60min")
                elif taxa_hum > 5:
                    weather = str("Chuva Iminente")
                else:
                    weather = str("Chuva Provavel")
            elif int(hum) > 60:
                weather = str("Nublado Umido")
            else:
                weather = str("Nublado Seco")
        elif int(presA) >= 923 and int(presA) <= 933:
            if taxa < -2:
                weather = str("Piorando") if int(hum) > 70 else str("Mudando")
            elif taxa > 2:
                weather = str("Melhorando")
            elif int(hum) > 75:
                weather = str("Estavel Umido")
            else:
                weather = str("Tempo Estavel")
        elif int(presA) > 933:
            if int(hum) < 50:
                weather = str("Ceu Limpo")
            elif int(hum) > 70:
                weather = str("Limpo+Umidade")
            else:
                weather = str("Bom Tempo")
        else:
            weather = str("Tempo Estavel")

        gc.collect()
    except:
        weather = str("Erro")
        gc.collect()


# ─── DISPLAY ───────────────────────────────────────────────

def display():
    global tempc, hum, presA, altitude
    global presd2, presd3, presd4, presd5, presd6, presd9, presd10
    global humd1, humd2, humd3, humd4, humd5, weather, mqtt_ok

    try:
        disp.fill(0)
        disp.hline(1, 53, 126, 1)
        disp.vline(69, 1, 52, 1)

        # Bloco 1 - leituras atuais
        disp.text("C",   18, 1)
        disp.text("%",   18, 12)
        disp.text("hPA", 34, 23)
        disp.text("Alt", 34, 34)
        disp.text("Tx",  42, 45)
        disp.text(str(presd10) + ":" + str(presd9), 32, 7)

        disp.text(str(tempc),  0, 1)
        disp.text(str(hum),    0, 12)
        disp.text(str(presA),  0, 23)
        disp.text("764m",      0, 34)

        if presd9 >= 5 and presd2 > 0:
            taxa = int(((float(presA) - float(presd2)) / 5) * 60)
            taxa_str = str(taxa)
        else:
            taxa_str = "--"
        disp.text(taxa_str, 0, 45)

        # Bloco 2 - historico
        disp.text(str(humd1), 110, 1)
        disp.text(str(humd2), 110, 12)
        disp.text(str(humd3), 110, 23)
        disp.text(str(humd4), 110, 34)
        disp.text(str(humd5), 110, 45)

        disp.text(":", 103, 1)
        disp.text(":", 103, 12)
        disp.text(":", 103, 23)
        disp.text(":", 103, 34)
        disp.text(":", 103, 45)

        disp.text(str(presd2), 72, 1)
        disp.text(str(presd3), 72, 12)
        disp.text(str(presd4), 72, 23)
        disp.text(str(presd5), 72, 34)
        disp.text(str(presd6), 72, 45)

        # Status MQTT no rodape
        status = weather
        if mqtt_ok:
            status = status[:12] + " ."   # ponto indica MQTT ok
        disp.text(status, 0, 56)

        disp.show()
        gc.collect()
    except:
        gc.collect()


# ─── INICIALIZACAO ─────────────────────────────────────────

sensor = dht.DHT11(machine.Pin(13))

i2c  = I2C(scl=Pin(14), sda=Pin(12), freq=10000)
i2cc = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))

bme  = BME280.BME280(i2c=i2c)
disp = ssd1306.SSD1306_I2C(128, 64, i2cc)
disp.fill(0)
disp.show()


# ─── LOOP PRINCIPAL ────────────────────────────────────────

while True:
    read_sensor()
    prevtemp()
    display()

    mqtt_contador += 1
    if mqtt_contador >= MQTT_INTERVALO:
        mqtt_publish()
        mqtt_contador = 0

    sleep(1)

# Fim
