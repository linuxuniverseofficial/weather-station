# Estação Meteorológica — Uberaba MG
## ESP8266 + BME280 + DHT11 + MQTT + SQLite + Flask

---

## Estrutura dos arquivos

```
meteo/
├── esp8266/
│   ├── boot.py       → configura WiFi (EDITE SSID/SENHA)
│   ├── main.py       → lógica principal + MQTT (EDITE IP DO BROKER)
│   ├── BME280.py     → driver do sensor (não mexer)
│   └── ssd1306.py    → driver do display (não mexer)
│
└── servidor/
    ├── subscriber.py     → consome MQTT e grava no SQLite
    ├── web.py            → interface web Flask
    └── docker-compose.yml
```

---

## 1. Configurar e gravar o ESP8266

### Edite boot.py:
```python
WIFI_SSID  = "nome_da_sua_rede"
WIFI_SENHA = "sua_senha"
```

### Edite main.py:
```python
MQTT_BROKER = "192.168.x.x"   # IP do servidor onde roda o Mosquitto
```

### Gravar via ampy:
```bash
# Instalar ampy (se não tiver)
pip3 install --user adafruit-ampy

# Descobrir a porta serial (geralmente /dev/ttyUSB0 ou /dev/ttyUSB1)
ls /dev/ttyUSB*

# Gravar todos os arquivos (ESP8266 precisa estar no modo normal, não flash)
export AMPY_PORT=/dev/ttyUSB0

ampy put boot.py
ampy put main.py
ampy put BME280.py
ampy put ssd1306.py

# Verificar
ampy ls
```

### Resetar o ESP8266:
Após gravar, pressione o botão RESET ou reconecte o USB.
Abra o monitor serial para verificar:
```bash
screen /dev/ttyUSB0 115200
# ou
minicom -b 115200 -D /dev/ttyUSB0
```
Deve aparecer:
```
[WiFi] Conectando a 'sua_rede'...
[WiFi] Conectado! IP: 192.168.x.xxx
```

---

## 2. Subir o servidor

```bash
cd servidor/

# Sobe subscriber + web em background
docker compose up -d

# Ver logs
docker compose logs -f
```

Acesso web: **http://IP_DO_SERVIDOR:5050**

---

## 3. Verificar fluxo MQTT manualmente

```bash
# Instalar cliente MQTT
sudo apt install mosquitto-clients

# Escutar o tópico (deve aparecer dados a cada 60s)
mosquitto_sub -h localhost -t "casa/meteo/uberaba" -v

# Exemplo de payload esperado:
# casa/meteo/uberaba {"temp":27,"hum":65,"pres":928,"weather":"Tempo Estavel"}
```

---

## Notas

- O ESP8266 publica **a cada 60 segundos** (MQTT_INTERVALO no main.py)
- O banco SQLite fica em `/dados/meteo.db` (volume Docker)
- Registros mais velhos que **30 dias** são removidos automaticamente
- A interface web se auto-atualiza a cada **60 segundos**
- O display OLED mostra um ponto (`.`) no rodapé quando o MQTT está ok
