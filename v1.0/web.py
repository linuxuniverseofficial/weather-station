#!/usr/bin/env python3
# web_lpr.py
# Interface web para visualizacao de placas capturadas
# Acesso: http://IP_DO_SERVIDOR:5051

from flask import Flask, jsonify, render_template_string, request
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "/dados/lpr.db"


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
  <title>Controle de Acesso — Veicular</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg:        #0d1520;
      --bg2:       #111d2e;
      --bg3:       #162236;
      --blue:      #0a2a4a;
      --blue-mid:  #1565c0;
      --blue-lt:   #5ba3e8;
      --blue-pale: #0d1f35;
      --cyan:      #00e5ff;
      --cyan-dim:  #00b8d4;
      --gold:      #d4a855;
      --text:      #cfe3f5;
      --text-dim:  #4d7a9e;
      --border:    #1a3050;
      --shadow:    rgba(0, 30, 80, 0.40);
      --moto:      #ff9800;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'DM Mono', monospace;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      zoom: 1.4;
    }

    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image: radial-gradient(var(--blue-pale) 1px, transparent 1px);
      background-size: 28px 28px;
      opacity: 0.5;
      pointer-events: none;
      z-index: 0;
    }

    header {
      background: var(--blue);
      padding: 0 2.5rem;
      display: flex;
      align-items: stretch;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 10;
      box-shadow: 0 2px 20px var(--shadow);
      border-bottom: 1px solid var(--border);
    }

    .header-brand {
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 1rem 0;
      border-right: 1px solid rgba(255,255,255,0.15);
      padding-right: 2rem;
      margin-right: 2rem;
    }

    .header-eyebrow {
      font-size: 0.55rem;
      color: var(--cyan-dim);
      letter-spacing: 4px;
      text-transform: uppercase;
      margin-bottom: 0.2rem;
    }

    header h1 {
      font-family: 'Cormorant Garamond', serif;
      font-size: 1.4rem;
      font-weight: 300;
      color: #ffffff;
      letter-spacing: 1px;
    }

    header h1 span { color: var(--gold); font-weight: 600; }

    .header-right {
      display: flex;
      align-items: center;
      gap: 2rem;
    }

    #clock {
      font-family: 'Cormorant Garamond', serif;
      font-size: 1.6rem;
      font-weight: 300;
      color: var(--cyan);
      letter-spacing: 2px;
    }

    #status {
      font-size: 0.65rem;
      padding: 0.3rem 1rem;
      border-radius: 20px;
      background: rgba(0,229,255,0.08);
      color: var(--cyan);
      border: 1px solid rgba(0,229,255,0.25);
      letter-spacing: 2px;
      text-transform: uppercase;
    }

    #status.offline {
      color: #ef9a9a;
      border-color: rgba(239,154,154,0.4);
      background: rgba(239,154,154,0.08);
    }

    main {
      padding: 2rem 2.5rem;
      max-width: 1200px;
      margin: 0 auto;
      position: relative;
      z-index: 1;
    }

    .section-label {
      font-size: 0.6rem;
      color: var(--cyan-dim);
      letter-spacing: 4px;
      text-transform: uppercase;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.8rem;
    }

    .section-label::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border);
    }

    .ultimas {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 1rem;
      margin-bottom: 2.5rem;
    }

    @media (max-width: 900px) {
      .ultimas { grid-template-columns: repeat(3, 1fr); }
    }

    .placa-card {
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.4rem 1rem;
      text-align: center;
      position: relative;
      overflow: hidden;
      box-shadow: 0 4px 16px var(--shadow);
      animation: slideDown 0.4s cubic-bezier(.22,.68,0,1.2);
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .placa-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 28px var(--shadow);
    }

    .placa-card:first-child {
      border-color: var(--cyan-dim);
      background: linear-gradient(160deg, #0d1f35 0%, #111d2e 100%);
    }

    .placa-card:first-child::before {
      content: 'RECENTE';
      position: absolute;
      top: 0; left: 0; right: 0;
      background: var(--cyan-dim);
      color: #0d1520;
      font-size: 0.5rem;
      font-weight: 700;
      letter-spacing: 3px;
      padding: 3px 0;
      text-align: center;
    }

    .placa-icon {
      font-size: 1.2rem;
      margin-bottom: 0.5rem;
    }

    .placa-numero {
      font-family: 'DM Mono', monospace;
      font-size: 1.25rem;
      font-weight: 400;
      color: var(--cyan);
      letter-spacing: 4px;
      margin-bottom: 0.6rem;
    }

    .placa-card:first-child .placa-numero {
      font-size: 1.35rem;
      text-shadow: 0 0 18px rgba(0,229,255,0.4);
    }

    .placa-divider {
      width: 30px;
      height: 1px;
      background: var(--border);
      margin: 0.5rem auto;
    }

    .placa-hora {
      font-size: 0.7rem;
      color: var(--text-dim);
      margin-bottom: 0.2rem;
    }

    .placa-camera {
      font-size: 0.65rem;
      color: var(--gold);
      letter-spacing: 1px;
    }

    .placa-score {
      font-size: 0.6rem;
      color: var(--blue-lt);
      margin-top: 0.3rem;
    }

    .historico-wrap {
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 20px var(--shadow);
    }

    .historico-header {
      padding: 1rem 1.5rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: linear-gradient(135deg, #0a2a4a 0%, #1565c0 100%);
    }

    .historico-header h3 {
      font-family: 'Cormorant Garamond', serif;
      font-size: 1rem;
      font-weight: 400;
      color: white;
      letter-spacing: 1px;
    }

    .filtros {
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }

    .filtros input {
      background: rgba(0,229,255,0.08);
      border: 1px solid rgba(0,229,255,0.2);
      color: var(--cyan);
      padding: 0.3rem 0.8rem;
      border-radius: 6px;
      font-family: 'DM Mono', monospace;
      font-size: 0.7rem;
      width: 130px;
      letter-spacing: 1px;
    }

    .filtros input::placeholder { color: rgba(0,229,255,0.35); }
    .filtros input:focus { outline: none; background: rgba(0,229,255,0.14); }

    .filtros button {
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.2);
      color: rgba(255,255,255,0.65);
      padding: 0.3rem 0.8rem;
      border-radius: 6px;
      cursor: pointer;
      font-family: 'DM Mono', monospace;
      font-size: 0.7rem;
      transition: all 0.2s;
    }

    .filtros button.ativo,
    .filtros button:hover {
      background: rgba(0,229,255,0.2);
      color: var(--cyan);
      border-color: rgba(0,229,255,0.4);
    }

    .total-badge {
      font-size: 0.6rem;
      color: rgba(255,255,255,0.5);
      padding: 0.2rem 0.7rem;
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 20px;
      letter-spacing: 1px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
    }

    thead th {
      background: var(--bg3);
      color: var(--cyan-dim);
      padding: 0.7rem 1.5rem;
      text-align: left;
      font-weight: 400;
      text-transform: uppercase;
      letter-spacing: 2px;
      font-size: 0.6rem;
      border-bottom: 1px solid var(--border);
    }

    tbody tr {
      border-bottom: 1px solid var(--bg3);
      transition: background 0.15s;
    }

    tbody tr:hover { background: var(--bg3); }

    tbody td { padding: 0.65rem 1.5rem; }

    td.td-placa {
      font-family: 'DM Mono', monospace;
      color: var(--cyan);
      font-size: 0.95rem;
      letter-spacing: 3px;
    }

    td.td-hora  { color: var(--text); font-size: 0.78rem; }
    td.td-cam   { color: var(--gold); font-size: 0.75rem; }
    td.td-tipo  { font-size: 0.8rem; }

    .tipo-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.65rem;
      padding: 0.15rem 0.5rem;
      border-radius: 20px;
    }

    .tipo-car {
      background: rgba(91,163,232,0.15);
      color: var(--blue-lt);
      border: 1px solid rgba(91,163,232,0.3);
    }

    .tipo-motorcycle {
      background: rgba(255,152,0,0.15);
      color: var(--moto);
      border: 1px solid rgba(255,152,0,0.3);
    }

    .score-bar {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .score-fill {
      height: 4px;
      background: var(--bg3);
      border-radius: 2px;
      width: 60px;
      overflow: hidden;
    }

    .score-fill-inner {
      height: 100%;
      background: linear-gradient(90deg, var(--cyan-dim), var(--cyan));
      border-radius: 2px;
    }

    .score-num { color: var(--text-dim); font-size: 0.7rem; }

    @keyframes slideDown {
      from { opacity: 0; transform: translateY(-12px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    footer {
      text-align: center;
      padding: 1.5rem;
      font-size: 0.6rem;
      color: var(--text-dim);
      letter-spacing: 3px;
      text-transform: uppercase;
      margin-top: 2rem;
      position: relative;
      z-index: 1;
    }
  </style>
</head>
<body>

<header>
  <div class="header-brand">
    <div class="header-eyebrow">Sistema de Segurança</div>
    <h1>Controle de Acesso <span>Veicular</span></h1>
  </div>
  <div class="header-right">
    <span id="clock">--:--:--</span>
    <span id="status">● Ao Vivo</span>
  </div>
</header>

<main>

  <div class="section-label">Últimas Detecções</div>
  <div class="ultimas" id="ultimas"></div>

  <div class="section-label">Histórico de Acessos</div>
  <div class="historico-wrap">
    <div class="historico-header">
      <h3>Registro de Placas</h3>
      <div class="filtros">
        <input type="text" id="busca" placeholder="Buscar placa..." oninput="filtrar()">
        <button onclick="carregarHistorico(50)"  class="ativo" id="btn50">50</button>
        <button onclick="carregarHistorico(200)" id="btn200">200</button>
        <button onclick="carregarHistorico(500)" id="btn500">500</button>
        <span class="total-badge" id="total">0 registros</span>
      </div>
    </div>
    <div style="overflow-x:auto; max-height:440px; overflow-y:auto;">
      <table>
        <thead>
          <tr>
            <th>Placa</th>
            <th>Data &amp; Hora</th>
            <th>Câmera</th>
            <th>Tipo</th>
            <th>Confiança</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>

</main>

<footer>Sistema LPR &mdash; Frigate &middot; MQTT &mdash; Atualização automática a cada 10s</footer>

<script>
  let todosRegistros = [];
  let limiteAtual = 50;
  let ultimaPlaca = null;

  function atualizarRelogio() {
    const now = new Date();
    document.getElementById('clock').textContent =
      now.toLocaleTimeString('pt-BR', { hour12: false });
  }
  setInterval(atualizarRelogio, 1000);
  atualizarRelogio();

  function formatarData(ts) {
    // ts vem como "2026-03-15 11:05:00"
    const d = new Date(ts.replace(' ', 'T'));
    const dia  = String(d.getDate()).padStart(2, '0');
    const mes  = String(d.getMonth() + 1).padStart(2, '0');
    const ano  = d.getFullYear();
    const hora = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', hour12: true });
    return `${dia}/${mes}/${ano} ${hora}`;
  }

  function tipoIcon(tipo) {
    if (tipo === 'motorcycle') return '🏍️';
    return '🚗';
  }

  function tipoBadge(tipo) {
    if (tipo === 'motorcycle') {
      return `<span class="tipo-badge tipo-motorcycle">🏍️ Moto</span>`;
    }
    return `<span class="tipo-badge tipo-car">🚗 Carro</span>`;
  }

  function copiarPlaca(placa, el) {
    const ta = document.createElement('textarea');
    ta.value = placa;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);

    el.style.borderColor = 'var(--cyan)';
    el.style.boxShadow = '0 0 16px rgba(0,229,255,0.4)';
    const num = el.querySelector('.placa-numero');
    const orig = num.textContent;
    num.textContent = 'COPIADO';
    num.style.color = 'var(--cyan)';
    setTimeout(() => {
      el.style.borderColor = '';
      el.style.boxShadow = '';
      num.textContent = orig;
      num.style.color = '';
    }, 800);
  }

  function renderUltimas(dados) {
    const ul = document.getElementById('ultimas');
    const top5 = dados.slice(0, 5);
    ul.innerHTML = top5.map((d, i) => `
      <div class="placa-card" onclick="copiarPlaca('${d.placa}', this)" style="cursor:pointer" title="Clique para copiar">
        <div class="placa-icon">${tipoIcon(d.tipo)}</div>
        <div class="placa-numero">${d.placa}</div>
        <div class="placa-divider"></div>
        <div class="placa-hora">${formatarData(d.ts)}</div>
        <div class="placa-camera">${d.camera}</div>
        <div class="placa-score">${(d.score * 100).toFixed(0)}% conf.</div>
      </div>
    `).join('');
    if (top5.length > 0) ultimaPlaca = top5[0].placa;
  }

  function renderTabela(dados) {
    const tbody = document.getElementById('tbody');
    tbody.innerHTML = dados.map(d => {
      const pct = Math.round(d.score * 100);
      return `<tr>
        <td class="td-placa">${d.placa}</td>
        <td class="td-hora">${formatarData(d.ts)}</td>
        <td class="td-cam">${d.camera}</td>
        <td class="td-tipo">${tipoBadge(d.tipo)}</td>
        <td>
          <div class="score-bar">
            <div class="score-fill"><div class="score-fill-inner" style="width:${pct}%"></div></div>
            <span class="score-num">${pct}%</span>
          </div>
        </td>
      </tr>`;
    }).join('');
    document.getElementById('total').textContent = dados.length + ' registros';
  }

  function filtrar() {
    const busca = document.getElementById('busca').value.toUpperCase().trim();
    if (!busca) { renderTabela(todosRegistros); return; }
    renderTabela(todosRegistros.filter(d => d.placa.includes(busca)));
  }

  function carregarHistorico(limite) {
    limiteAtual = limite;
    ['btn50','btn200','btn500'].forEach(id =>
      document.getElementById(id).classList.remove('ativo'));
    document.getElementById('btn' + limite)?.classList.add('ativo');
    buscarDados();
  }

  function buscarDados() {
    fetch('/api/placas?limite=' + limiteAtual)
      .then(r => r.json())
      .then(dados => {
        renderUltimas(dados);
        todosRegistros = dados;
        filtrar();
        const st = document.getElementById('status');
        st.textContent = '● Ao Vivo';
        st.className = '';
      })
      .catch(() => {
        const st = document.getElementById('status');
        st.textContent = '● Offline';
        st.className = 'offline';
      });
  }

  buscarDados();
  setInterval(buscarDados, 10000);
</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/placas")
def api_placas():
    limite = request.args.get("limite", 50, type=int)
    limite = max(1, min(limite, 1000))

    if not os.path.exists(DB_PATH):
        return jsonify([])

    rows = query_db(
        """
        SELECT ts, placa, score, camera, COALESCE(tipo, 'car') as tipo
        FROM placas
        ORDER BY ts DESC
        LIMIT ?
        """,
        (limite,)
    )
    return jsonify([dict(r) for r in rows])


@app.route("/api/resumo")
def api_resumo():
    if not os.path.exists(DB_PATH):
        return jsonify({})

    row = query_db(
        """
        SELECT
            COUNT(*) as total_hoje,
            COUNT(DISTINCT placa) as placas_unicas
        FROM placas
        WHERE ts >= datetime('now', 'start of day', 'localtime')
        """,
        one=True
    )
    return jsonify(dict(row) if row else {})


if __name__ == "__main__":
    print("[Web] Iniciando em http://0.0.0.0:5051")
    app.run(host="0.0.0.0", port=5051, debug=False)
