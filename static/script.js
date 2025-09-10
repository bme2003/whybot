// --- Grid model ---
const W = 32, H = 24;
let start = {x:1,y:1}, goal = {x:30,y:20};
const cells = new Array(H).fill(0).map(()=> new Array(W).fill(0)); // 0 empty, 1 obstacle, 2 hazard
let path = [];
let pathCF = [];
let setMode = null; // "start" | "goal" | null

// --- UI elements ---
const canvas = document.getElementById('grid');
const ctx = canvas.getContext('2d');
const btnStart = document.getElementById('btnStart');
const btnGoal = document.getElementById('btnGoal');
const btnPlan = document.getElementById('btnPlan');
const btnStore = document.getElementById('btnStore');
const btnCounter = document.getElementById('btnCounter');
const btnClear = document.getElementById('btnClear');
const btnWalls = document.getElementById('btnWalls');
const btnDemo = document.getElementById('btnDemo');

const wTime = document.getElementById('w-time');
const wRisk = document.getElementById('w-risk');
const wEnergy = document.getElementById('w-energy');
const wUnc = document.getElementById('w-unc');
const wMem = document.getElementById('w-mem');

const valTime = document.getElementById('val-time');
const valRisk = document.getElementById('val-risk');
const valEnergy = document.getElementById('val-energy');
const valUnc = document.getElementById('val-unc');
const valMem = document.getElementById('val-mem');

[wTime,wRisk,wEnergy,wUnc,wMem].forEach(inp=>{
  inp.addEventListener('input', updateLabels);
});
function updateLabels(){
  valTime.textContent = parseFloat(wTime.value).toFixed(1);
  valRisk.textContent = parseFloat(wRisk.value).toFixed(1);
  valEnergy.textContent = parseFloat(wEnergy.value).toFixed(1);
  valUnc.textContent = parseFloat(wUnc.value).toFixed(1);
  valMem.textContent = parseFloat(wMem.value).toFixed(1);
}
updateLabels();

btnStart.onclick = ()=> setMode = "start";
btnGoal.onclick = ()=> setMode = "goal";
btnClear.onclick = ()=> { clearGrid(); draw(); };
btnWalls.onclick = ()=> { randomWalls(); draw(); };
if (btnDemo) btnDemo.onclick = ()=> { demoScenario(); draw(); };

// Canvas events
canvas.addEventListener('click', (e)=>{
  const {x,y} = cellFromEvent(e);
  if (!inBounds(x,y)) return;
  if (setMode === "start"){ start = {x,y}; setMode=null; draw(); return; }
  if (setMode === "goal"){ goal = {x,y}; setMode=null; draw(); return; }
  // toggle empty -> obstacle -> hazard -> empty
  const v = cells[y][x];
  const nv = (v + 1) % 3;
  cells[y][x] = nv;
  draw();
});

// Planning calls
let baseline = null;

btnPlan.onclick = async ()=> {
  const res = await callPlan(getWeights());
  if (res.found){
    path = res.path;
    pathCF = [];
    baseline = res; // auto-store plan as baseline so Counterfactual "just works"
    renderExplain(res);
  } else {
    path = []; pathCF = [];
    renderExplain(res);
  }
  draw();
};

btnStore.onclick = async ()=>{
  const res = await callPlan(getWeights());
  if (res.found){
    baseline = res;
    path = res.path;
    pathCF = [];
    renderExplain(res);
    draw();
  } else {
    alert("No path to store as baseline.");
  }
};

btnCounter.onclick = async ()=>{
  if (!baseline){
    // Make it foolproof: get a baseline for the user automatically.
    const base = await callPlan(getWeights());
    if (!base.found){
      alert("No path available to set a baseline. Adjust the map.");
      return;
    }
    baseline = base;
    path = base.path;
    renderExplain(base);
    draw();
    alert("Baseline set from current weights. Now move the sliders and click Counterfactual again.");
    return;
  }
  const res = await callPlan(getWeights());
  if (res.found){
    pathCF = res.path;
    const same = samePath(res.path, baseline.path);
    renderExplain(res, baseline, same);
    draw();
    if (same){
      // Nudge the user to change weights more or try the demo scenario
      setTimeout(()=> {
        alert("Counterfactual equals the baseline.\n\nTips:\n• Move sliders more (e.g., Risk=3.0, Time=0.3)\n• Click the Demo Scenario button\n• Add hazard memory near one corridor");
      }, 10);
    }
  } else {
    alert("No counterfactual path found.");
  }
};

// Helpers
function inBounds(x,y){ return x>=0 && x<W && y>=0 && y<H; }
function cellFromEvent(e){
  const rect = canvas.getBoundingClientRect();
  const sx = (e.clientX - rect.left) / rect.width;
  const sy = (e.clientY - rect.top) / rect.height;
  const gx = Math.floor(sx * W);
  const gy = Math.floor(sy * H);
  return {x:gx,y:gy};
}
function clearGrid(){
  for (let y=0;y<H;y++) for (let x=0;x<W;x++) cells[y][x]=0;
  path=[]; pathCF=[];
  start={x:1,y:1}; goal={x:W-2,y:H-2};
}
function randomWalls(){
  clearGrid();
  // border walls
  for (let x=0;x<W;x++){ cells[0][x]=1; cells[H-1][x]=1; }
  for (let y=0;y<H;y++){ cells[y][0]=1; cells[y][W-1]=1; }
  // random interior
  const rnd = (min,max)=> Math.floor(Math.random()*(max-min+1))+min;
  for (let i=0;i<Math.floor(W*H*0.12);i++){
    const x = rnd(1,W-2), y = rnd(1,H-2);
    cells[y][x]=1;
  }
  // a couple hazard memory spots
  cells[6][7]=2; cells[15][18]=2;
}

function demoScenario(){
  // Deterministic 2-corridor map that makes trade-offs obvious.
  clearGrid();
  // Border walls
  for (let x=0;x<W;x++){ cells[0][x]=1; cells[H-1][x]=1; }
  for (let y=0;y<H;y++){ cells[y][0]=1; cells[y][W-1]=1; }
  // Two corridors: top (short but risky), bottom (long but safe)
  // Build a vertical obstacle block with two gaps (top and bottom)
  for (let y=1;y<H-1;y++){
    cells[y][Math.floor(W/2)] = 1;
  }
  // Open two gates
  cells[3][Math.floor(W/2)] = 0;     // upper gate
  cells[H-4][Math.floor(W/2)] = 0;   // lower gate
  // Add hazard memory near upper gate (to bias memory/risk upwards)
  for (let yy=2; yy<=5; yy++){
    cells[yy][Math.floor(W/2)-1] = 2;
    cells[yy][Math.floor(W/2)-2] = 2;
  }
  start = {x:2,y:Math.floor(H/2)};
  goal = {x:W-3, y:Math.floor(H/2)};
}

function getWeights(){
  return {
    time: parseFloat(wTime.value),
    risk: parseFloat(wRisk.value),
    energy: parseFloat(wEnergy.value),
    uncertainty: parseFloat(wUnc.value),
    memory: parseFloat(wMem.value),
  };
}

async function callPlan(weights){
  const obstacles=[], hazards=[];
  for (let y=0;y<H;y++){
    for (let x=0;x<W;x++){
      if (cells[y][x]===1) obstacles.push([x,y]);
      else if (cells[y][x]===2) hazards.push([x,y]);
    }
  }
  const body = {
    width: W, height: H,
    start: [start.x,start.y],
    goal: [goal.x,goal.y],
    obstacles, hazards,
    weights
  };
  const res = await fetch('/plan', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  return await res.json();
}

// Rendering
function draw(){
  const cw = canvas.width, ch = canvas.height;
  const cellW = cw / W, cellH = ch / H;
  ctx.clearRect(0,0,cw,ch);
  // grid background
  for (let y=0;y<H;y++){
    for (let x=0;x<W;x++){
      const v = cells[y][x];
      let color = '#12141c';
      if (v===1) color = '#5b6275';     // obstacle
      else if (v===2) color = '#cc7a00';// hazard memory
      ctx.fillStyle = color;
      ctx.fillRect(x*cellW, y*cellH, cellW-1, cellH-1);
    }
  }
  // paths (baseline first, then counterfactual on top)
  drawPath(path, '#7aa2ff', 3, false);
  drawPath(pathCF, '#ff9e64', 3, true);

  // start/goal
  fillCell(start.x,start.y,'#4bd38a');
  fillCell(goal.x,goal.y,'#ff6b6b');

  function fillCell(x,y,color){
    ctx.fillStyle=color;
    ctx.fillRect(x*cellW, y*cellH, cellW-1, cellH-1);
  }
  function drawPath(p, color, width, dashed){
    if (!p || p.length===0) return;
    ctx.save();
    ctx.strokeStyle=color;
    ctx.lineWidth=width;
    ctx.lineJoin='round';
    if (dashed) ctx.setLineDash([6,4]);
    ctx.beginPath();
    for (let i=0;i<p.length;i++){
      const [x,y]=p[i];
      const cx = x*cellW + cellW/2;
      const cy = y*cellH + cellH/2;
      if (i===0) ctx.moveTo(cx,cy); else ctx.lineTo(cx,cy);
    }
    ctx.stroke();
    ctx.restore();
  }
}

const bars = document.getElementById('bars');
const explainText = document.getElementById('explain-text');
const metrics = document.getElementById('metrics');

function samePath(a,b){
  if (!a || !b) return false;
  if (a.length !== b.length) return false;
  for (let i=0;i<a.length;i++){
    if (a[i][0] !== b[i][0] || a[i][1] !== b[i][1]) return false;
  }
  return true;
}

function renderExplain(res, baseline=null, isSame=false){
  explainText.textContent = res.explanation;
  const pct = res.percentages || {};
  const terms = ["time","risk","energy","uncertainty","memory"];
  bars.innerHTML = '';
  terms.forEach(t=>{
    const div = document.createElement('div');
    div.className = 'bar';
    const name = document.createElement('div');
    name.className='name'; name.textContent = t;
    const value = document.createElement('div');
    value.className='value'; value.textContent = (pct[t]||0).toFixed(1)+'%';
    div.appendChild(name); div.appendChild(value);
    bars.appendChild(div);
  });
  let m = `Steps: ${res.steps} · Total Cost: ${res.total_cost.toFixed(2)}`;
  if (baseline && baseline.found){
    const dSteps = res.steps - baseline.steps;
    const dCost = res.total_cost - baseline.total_cost;
    const arrow = (x)=> x>0?'▲':(x<0?'▼':'=');
    m += ` | Δ Steps ${arrow(dSteps)} ${dSteps} · Δ Cost ${arrow(dCost)} ${dCost.toFixed(2)}`;
    if (isSame) m += ` · (Counterfactual = Baseline)`;
  }
  metrics.textContent = m;
}

// boot
randomWalls();
draw();
