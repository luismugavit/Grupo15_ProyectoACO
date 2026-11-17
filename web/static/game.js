// Cliente: recibe el estado por SSE y dibuja. Esqueleto minimo.
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const HIT_X = 120;
const COLORS = ["#4fc3f7", "#f06292", "#aed581", "#ffd54f"];

let chart = {notes: [], lookahead: 2.5};
let state = null, recvAt = 0;

const post = (url, body) => fetch(url, {method: "POST",
  headers: {"Content-Type": "application/json"}, body: JSON.stringify(body || {})});

async function startGame() {
  chart = await (await fetch("/api/chart/demo")).json();
  post("/api/start", {chart: "demo"});
}
const stopGame = () => post("/api/stop");

const es = new EventSource("/api/stream");
es.onmessage = e => { state = JSON.parse(e.data); recvAt = performance.now(); };

// Teclas 1-4 simulan pulsadores
document.addEventListener("keydown", e => {
  if ("1234".includes(e.key)) post(`/api/debug/press/${e.key}`);
});

async function refreshHighscores() {
  const rows = await (await fetch("/api/highscores")).json();
  document.getElementById("highscores").innerHTML =
    "<tr><th>Jugador</th><th>Pts</th></tr>" +
    rows.map(r => `<tr><td>${r.name}</td><td>${r.score}</td></tr>`).join("");
}
refreshHighscores();
let lastState = "";

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (state) {
    if (state.state !== lastState) { lastState = state.state; if (lastState === "finished") refreshHighscores(); }
    document.getElementById("title").textContent = state.title || "Juego de ritmo";
    // interpola entre mensajes SSE con el reloj local -> movimiento fluido
    const t = state.song_time + (performance.now() - recvAt) / 1000;
    ctx.strokeStyle = "#fff";
    ctx.beginPath(); ctx.moveTo(HIT_X, 0); ctx.lineTo(HIT_X, canvas.height); ctx.stroke();
    for (const n of chart.notes) {
      if (n < t - 0.3 || n > t + chart.lookahead) continue;
      const x = HIT_X + (n - t) / chart.lookahead * (canvas.width - HIT_X);
      ctx.fillStyle = "#fff";
      ctx.beginPath(); ctx.arc(x, canvas.height / 2, 18, 0, Math.PI * 2); ctx.fill();
    }
    document.getElementById("scores").innerHTML = Object.entries(state.players)
      .map(([id, p]) => `<div style="color:${COLORS[id-1]}"><b>Jugador ${id}</b><br>
        ${p.score} pts · combo ${p.combo}<br>${p.last ?? ""}</div>`).join("");
    if (state.state === "countdown") {
      ctx.fillStyle = "#fff"; ctx.font = "64px sans-serif";
      ctx.fillText(Math.ceil(-t), canvas.width / 2, canvas.height / 2);
    }
  }
  requestAnimationFrame(draw);
}
draw();
