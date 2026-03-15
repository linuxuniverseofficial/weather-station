#!/usr/bin/env python3
# web.py
# Interface web para visualizacao dos dados meteorologicos
# Acesso: http://IP_DO_SERVIDOR:5050

from flask import Flask, jsonify, render_template_string, request
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "/dados/meteo.db"


def query_db(sql, args=(), one=False):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.execute(sql, args)
    rv = cur.fetchall()
    con.close()
    return (rv[0] if rv else None) if one else rv


HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Estação Meteorológica — Uberaba MG</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Courier New', monospace;
      background: #0a0a0a;
      color: #c8d6e5;
      min-height: 100vh;
    }

    header {
      background: #111;
      border-bottom: 1px solid #1e3a5f;
      padding: 1rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    header h1 {
      font-size: 1.1rem;
      color: #4fc3f7;
      letter-spacing: 2px;
      text-transform: uppercase;
    }

    #status-mqtt {
      font-size: 0.75rem;
      padding: 0.3rem 0.8rem;
      border-radius: 20px;
      background: #1a2a1a;
      color: #4caf50;
      border: 1px solid #2e7d32;
    }

    main { padding: 1.5rem 2rem; max-width: 1400px; margin: 0 auto; }

    /* Cards de leitura atual */
    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    .card {
      background: #111;
      border: 1px solid #1e3a5f;
      border-radius: 8px;
      padding: 1.2rem;
      text-align: center;
    }

    .card .label {
      font-size: 0.7rem;
      color: #607d8b;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 0.4rem;
    }

    .card .value {
      font-size: 2rem;
      font-weight: bold;
      color: #4fc3f7;
    }

    .card .unit {
      font-size: 0.85rem;
      color: #607d8b;
    }

    .card.weather .value {
      font-size: 1.1rem;
      color: #ffd54f;
      line-height: 1.4;
    }

    /* Graficos */
    .charts {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    @media (max-width: 768px) {
      .charts { grid-template-columns: 1fr; }
    }

    .chart-box {
      background: #111;
      border: 1px solid #1e3a5f;
      border-radius: 8px;
      padding: 1rem;
    }

    .chart-box h3 {
      font-size: 0.75rem;
      color: #607d8b;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 0.8rem;
    }

    /* Tabela historico */
    .tabela-wrap {
      background: #111;
      border: 1px solid #1e3a5f;
      border-radius: 8px;
      overflow: hidden;
    }

    .tabela-header {
      padding: 0.8rem 1rem;
      border-bottom: 1px solid #1e3a5f;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .tabela-header h3 {
      font-size: 0.75rem;
      color: #607d8b;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .filtro {
      display: flex;
      gap: 0.5rem;
    }

    .filtro button {
      background: transparent;
      border: 1px solid #1e3a5f;
      color: #607d8b;
      padding: 0.25rem 0.7rem;
      border-radius: 4px;
      cursor: pointer;
      font-family: inherit;
      font-size: 0.75rem;
      transition: all 0.2s;
    }

    .filtro button.ativo, .filtro button:hover {
      background: #1e3a5f;
      color: #4fc3f7;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8rem;
    }

    thead th {
      background: #0d1f33;
      color: #607d8b;
      padding: 0.6rem 1rem;
      text-align: left;
      font-weight: normal;
      text-transform: uppercase;
      letter-spacing: 1px;
      font-size: 0.7rem;
    }

    tbody tr {
      border-bottom: 1px solid #151f2a;
      transition: background 0.15s;
    }

    tbody tr:hover { background: #0d1f33; }

    tbody td {
      padding: 0.55rem 1rem;
      color: #c8d6e5;
    }

    tbody td.temp  { color: #ef9a9a; }
    tbody td.hum   { color: #80deea; }
    tbody td.pres  { color: #a5d6a7; }
    tbody td.weath { color: #ffd54f; }

    footer {
      text-align: center;
      padding: 1rem;
      font-size: 0.7rem;
      color: #37474f;
      border-top: 1px solid #151f2a;
      margin-top: 1.5rem;
    }

    #ultima-atualizacao {
      font-size: 0.7rem;
      color: #37474f;
    }
  </style>
</head>
<body>

<header>
  <h1>⛅ Estação Meteorológica — Uberaba MG / 764m</h1>
  <div>
    <span id="status-mqtt">● ONLINE</span>
    &nbsp;
    <span id="ultima-atualizacao">carregando...</span>
  </div>
</header>

<main>

  <!-- Cards atuais -->
  <div class="cards">
    <div class="card">
      <div class="label">Temperatura</div>
      <div class="value" id="v-temp">--</div>
      <div class="unit">°C</div>
    </div>
    <div class="card">
      <div class="label">Umidade</div>
      <div class="value" id="v-hum">--</div>
      <div class="unit">%</div>
    </div>
    <div class="card">
      <div class="label">Pressão</div>
      <div class="value" id="v-pres">--</div>
      <div class="unit">hPa</div>
    </div>
    <div class="card">
      <div class="label">Variação (1h)</div>
      <div class="value" id="v-taxa">--</div>
      <div class="unit">hPa/h</div>
    </div>
    <div class="card weather">
      <div class="label">Previsão</div>
      <div class="value" id="v-weather">--</div>
    </div>
  </div>

  <!-- Graficos -->
  <div class="charts">
    <div class="chart-box">
      <h3>Pressão Atmosférica (hPa)</h3>
      <canvas id="chart-pres" height="140"></canvas>
    </div>
    <div class="chart-box">
      <h3>Temperatura (°C) e Umidade (%)</h3>
      <canvas id="chart-th" height="140"></canvas>
    </div>
  </div>

  <!-- Tabela historico -->
  <div class="tabela-wrap">
    <div class="tabela-header">
      <h3>Histórico</h3>
      <div class="filtro">
        <button onclick="carregar(50)"  class="ativo" id="btn50">50</button>
        <button onclick="carregar(200)" id="btn200">200</button>
        <button onclick="carregar(500)" id="btn500">500</button>
      </div>
    </div>
    <div style="overflow-x:auto; max-height: 400px; overflow-y:auto;">
      <table>
        <thead>
          <tr>
            <th>Horário</th>
            <th>Temp</th>
            <th>Umidade</th>
            <th>Pressão</th>
            <th>Previsão</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>

</main>

<footer>
  Sistema Meteorológico Uberaba MG &mdash; BME280 + DHT11 + ESP8266 &mdash; dados a cada 60s
</footer>

<script>
  let chartPres = null;
  let chartTH   = null;

  function initCharts(dados) {
    const labels = dados.map(d => d.ts.substring(11, 16)).reverse();
    const pres   = dados.map(d => d.pres).reverse();
    const temp   = dados.map(d => d.temp).reverse();
    const hum    = dados.map(d => d.hum).reverse();

    const cfg = (label, data, color, y2=false) => ({
      label, data,
      borderColor: color,
      backgroundColor: color + '18',
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.3,
      fill: true,
      yAxisID: y2 ? 'y2' : 'y'
    });

    if (chartPres) chartPres.destroy();
    chartPres = new Chart(document.getElementById('chart-pres'), {
      type: 'line',
      data: { labels, datasets: [ cfg('hPa', pres, '#4caf50') ] },
      options: {
        animation: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#37474f', maxTicksLimit: 8 }, grid: { color: '#151f2a' } },
          y: { ticks: { color: '#4caf50' }, grid: { color: '#151f2a' } }
        }
      }
    });

    if (chartTH) chartTH.destroy();
    chartTH = new Chart(document.getElementById('chart-th'), {
      type: 'line',
      data: { labels, datasets: [
        cfg('°C', temp, '#ef9a9a'),
        { ...cfg('%', hum, '#80deea', true), yAxisID: 'y2' }
      ]},
      options: {
        animation: false,
        plugins: { legend: { labels: { color: '#607d8b', boxWidth: 12, font: { size: 11 } } } },
        scales: {
          x:  { ticks: { color: '#37474f', maxTicksLimit: 8 }, grid: { color: '#151f2a' } },
          y:  { ticks: { color: '#ef9a9a' }, grid: { color: '#151f2a' } },
          y2: { position: 'right', ticks: { color: '#80deea' }, grid: { display: false } }
        }
      }
    });
  }

  function carregar(limite) {
    ['btn50','btn200','btn500'].forEach(id => {
      document.getElementById(id).classList.remove('ativo');
    });
    document.getElementById('btn' + limite)?.classList.add('ativo');

    fetch('/api/dados?limite=' + limite)
      .then(r => r.json())
      .then(dados => {
        if (!dados.length) return;

        // Cards
        const u = dados[0];
        document.getElementById('v-temp').textContent    = u.temp;
        document.getElementById('v-hum').textContent     = u.hum;
        document.getElementById('v-pres').textContent    = u.pres;
        document.getElementById('v-weather').textContent = u.weather;
        document.getElementById('ultima-atualizacao').textContent = 'atualizado ' + u.ts.substring(11, 16);

        // Taxa de variacao (diferenca entre primeiro e ultimo registro)
        if (dados.length > 1) {
          const oldest = dados[dados.length - 1];
          const dt_min = (new Date(u.ts) - new Date(oldest.ts)) / 60000;
          if (dt_min > 0) {
            const taxa = ((u.pres - oldest.pres) / dt_min * 60).toFixed(1);
            document.getElementById('v-taxa').textContent = (taxa > 0 ? '+' : '') + taxa;
          }
        }

        // Tabela
        const tbody = document.getElementById('tbody');
        tbody.innerHTML = dados.map(d =>
          `<tr>
            <td>${d.ts.substring(5, 16)}</td>
            <td class="temp">${d.temp}°C</td>
            <td class="hum">${d.hum}%</td>
            <td class="pres">${d.pres} hPa</td>
            <td class="weath">${d.weather}</td>
          </tr>`
        ).join('');

        // Graficos com os ultimos 100
        initCharts(dados.slice(0, 100));
      });
  }

  carregar(50);
  setInterval(() => carregar(50), 60000); // auto-refresh a cada 1min
</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/dados")
def api_dados():
    limite = request.args.get("limite", 50, type=int)
    limite = max(1, min(limite, 1000))  # clamp 1-1000

    if not os.path.exists(DB_PATH):
        return jsonify([])

    rows = query_db(
        """
        SELECT ts, temp, hum, pres, weather
        FROM leituras
        ORDER BY ts DESC
        LIMIT ?
        """,
        (limite,)
    )
    return jsonify([dict(r) for r in rows])


@app.route("/api/resumo")
def api_resumo():
    """Estatísticas do dia atual."""
    if not os.path.exists(DB_PATH):
        return jsonify({})

    row = query_db(
        """
        SELECT
            COUNT(*)                as total,
            ROUND(MIN(temp), 1)     as temp_min,
            ROUND(MAX(temp), 1)     as temp_max,
            ROUND(AVG(temp), 1)     as temp_med,
            ROUND(MIN(pres), 1)     as pres_min,
            ROUND(MAX(pres), 1)     as pres_max,
            ROUND(MAX(hum),  1)     as hum_max
        FROM leituras
        WHERE ts >= datetime('now', 'start of day', 'localtime')
        """,
        one=True
    )
    return jsonify(dict(row) if row else {})


if __name__ == "__main__":
    print("[Web] Iniciando em http://0.0.0.0:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
