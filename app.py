<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>▶ GRAND WAR MONITOR (TAMAMO API)</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #080b0f; --surface: #0f1318; --surface2: #161c24;
            --border: #252d3a; --border2: #1e2736; --text: #c8d8e8; --muted: #4a5568;
            --accent: #3b82f6; --attack: #ef4444; --defense: #22c55e;
            --fallen: #f97316; --battle: #eab308;
            --mono: 'Share Tech Mono', monospace; --sans: 'Noto Sans JP', sans-serif;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: var(--bg); color: var(--text); font-family: var(--sans); font-size: 13px; min-height: 100vh; }
        header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 10px 16px; position: sticky; top: 0; z-index: 100; }
        .status-bar { background: var(--surface); border-bottom: 1px solid var(--border2); padding: 5px 16px; display: flex; align-items: center; gap: 14px; font-family: var(--mono); font-size: 11px; color: var(--muted); position: sticky; top: 100px; z-index: 99; }
        .day-tabs { display: flex; gap: 4px; }
        .day-tab { background: var(--surface2); border: 1px solid var(--border); color: var(--muted); padding: 2px 8px; border-radius: 3px; cursor: pointer; font-family: var(--mono); font-size: 10px; }
        .day-tab.active { border-color: var(--accent); color: var(--accent); background: #1a2030; }
        h1 { font-family: var(--mono); font-size: 13px; letter-spacing: 2px; color: var(--accent); margin-bottom: 10px; }
        .controls { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
        .ctrl-group { display: flex; align-items: center; gap: 5px; }
        label { font-size: 11px; color: var(--muted); }
        select, input[type=number] { background: var(--surface2); border: 1px solid var(--border); color: var(--text); padding: 5px 8px; font-size: 12px; font-family: var(--sans); border-radius: 3px; outline: none; }
        button { background: var(--accent); border: 1px solid var(--accent); color: #fff; padding: 5px 14px; font-size: 12px; font-family: var(--sans); border-radius: 3px; cursor: pointer; font-weight: bold; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        #clock { margin-left: auto; font-size: 13px; color: var(--accent); font-weight: bold; }
        .main { padding: 12px 16px; }
        #tableContainer { width: 100%; overflow-x: auto; }
        table { width: 100%; border-collapse: separate; border-spacing: 0; font-family: var(--mono); font-size: 12px; min-width: 800px; }
        thead th { background: var(--surface2); padding: 10px; text-align: left; color: var(--muted); position: sticky; top: 0; }
        tbody td { padding: 8px 10px; border-bottom: 1px solid var(--border2); }
        .cid { color: var(--accent); font-weight: bold; margin-right: 8px; }
        .badge { display: inline-block; padding: 2px 7px; border-radius: 10px; font-size: 10px; font-weight: bold; }
        .s-battle { background: #3d2e00; color: var(--battle); }
        .s-fallen { background: #3d1000; color: var(--fallen); }
        .s-defense { background: #0d3020; color: var(--defense); }
        .loading { text-align: center; padding: 40px; color: var(--muted); }
    </style>
</head>
<body>

<header id="header">
    <h1>▶ GRAND WAR MONITOR / TAMAMO API</h1>
    <div class="controls">
        <div class="ctrl-group">
            <label>Group</label>
            <input type="number" id="groupInput" value="19" min="1">
        </div>
        <div class="ctrl-group">
            <label>Class</label>
            <select id="classSelect">
                <option value="3" selected>Grand Master</option>
                <option value="2">Expert</option>
                <option value="1">Elite</option>
            </select>
        </div>
        <div class="ctrl-group">
            <label>Block</label>
            <select id="blockSelect">
                <option value="0">Block A</option>
                <option value="1" selected>Block B</option>
                <option value="2">Block C</option>
                <option value="3">Block D</option>
            </select>
        </div>
        <button id="updateBtn">データ更新</button>
    </div>
</header>

<div class="status-bar">
    <div class="day-tabs" id="dayTabs">
        <span class="day-tab active" data-day="Sat">SAT</span>
        <span class="day-tab" data-day="Sun">SUN</span>
        <span class="day-tab" data-day="Tue">TUE</span>
        <span class="day-tab" data-day="Wed">WED</span>
        <span class="day-tab" data-day="Thu">THU</span>
        <span class="day-tab" data-day="Fri">FRI</span>
    </div>
    <span id="updateStatus">Ready</span>
    <span id="clock">--:--:--</span>
</div>

<div class="main">
    <div id="tableContainer">
        <div class="loading">Please update to fetch data...</div>
    </div>
</div>

<script>
    const LOG_API = 'https://api.tamamo.dev/GvGLog';
    const CASTLE_API = 'https://tamamo.dev/assets/Resource/CastleId.json';
    
    let castleNames = {};
    let currentDay = 'Sat';

    // 時計更新
    setInterval(() => {
        document.getElementById('clock').textContent = new Date().toLocaleTimeString('ja-JP', { hour12: false });
    }, 1000);

    // 拠点データ取得
    async function fetchCastleNames() {
        try {
            const res = await fetch(CASTLE_API);
            const data = await res.json();
            data.forEach(item => {
                castleNames[item.Id] = item.Name;
            });
        } catch (e) {
            console.error("Failed to load castle names");
        }
    }

    async function updateData() {
        const btn = document.getElementById('updateBtn');
        const status = document.getElementById('updateStatus');
        const container = document.getElementById('tableContainer');
        
        btn.disabled = true;
        status.textContent = "Fetching...";
        
        const group = document.getElementById('groupInput').value;
        const gClass = document.getElementById('classSelect').value;
        const block = document.getElementById('blockSelect').value;
        
        try {
            const url = `${LOG_API}?Group=${group}&Class=${gClass}&Block=${block}&Week=${currentDay}`;
            const res = await fetch(url);
            const data = await res.json();
            
            if (!data || data.length === 0) {
                container.innerHTML = '<div class="loading">データが見つかりませんでした</div>';
            } else {
                renderTable(data);
            }
            status.textContent = `Last Update: ${new Date().toLocaleTimeString()}`;
        } catch (e) {
            status.textContent = "Error fetching data";
            console.error(e);
        } finally {
            btn.disabled = false;
        }
    }

    function renderTable(data) {
        let html = `<table>
            <thead>
                <tr>
                    <th>拠ID</th>
                    <th>拠点名</th>
                    <th>現在の所有者</th>
                    <th>攻撃者</th>
                    <th>状態</th>
                    <th>防衛P</th>
                    <th>攻撃P</th>
                    <th>最終更新(JST)</th>
                </tr>
            </thead>
            <tbody>`;
        
        // CastleID順にソート
        data.sort((a, b) => a.CastleId - b.CastleId);

        data.forEach(row => {
            const stateLabel = row.State === 1 ? '布告' : row.State === 2 ? '陥落' : row.State === 3 ? '反撃' : '安定';
            const stateClass = row.State === 1 ? 's-battle' : row.State === 2 ? 's-fallen' : row.State === 4 ? 's-defense' : '';
            
            html += `<tr>
                <td><span class="cid">${row.CastleId}</span></td>
                <td>${castleNames[row.CastleId] || 'Unknown'}</td>
                <td>${row.GuildName || '<span style="color:var(--muted)">-</span>'}</td>
                <td>${row.AttackerGuildName || '<span style="color:var(--muted)">-</span>'}</td>
                <td><span class="badge ${stateClass}">${stateLabel}</span></td>
                <td style="color:var(--defense)">${row.DefensePartyCount}</td>
                <td style="color:var(--attack)">${row.AttackPartyCount}</td>
                <td style="color:var(--muted); font-size:11px;">${row.LastUpdate}</td>
            </tr>`;
        });

        html += `</tbody></table>`;
        document.getElementById('tableContainer').innerHTML = html;
    }

    // タブ切り替え
    document.querySelectorAll('.day-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.day-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentDay = tab.dataset.day;
            updateData();
        });
    });

    document.getElementById('updateBtn').addEventListener('click', updateData);

    // 初期化
    async function init() {
        await fetchCastleNames();
        updateData();
    }
    
    init();
</script>
</body>
</html>
