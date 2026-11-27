"""Gera um visualizador 3D HTML standalone (Three.js) com os 3 STLs embutidos e visao explodida."""

import base64
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
STL_DIR = PROJECT_DIR / "stl"
OUT_HTML = PROJECT_DIR / "visualizador_3d.html"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Chaveiro 3D Rasec — Visualizador Interativo & Visão Explodida</title>
<style>
  :root { --bg: #141414; --panel: rgba(24,24,28,0.86); --accent: #6961D7; --text: #f3f4f6; --muted: #9ca3af; }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif; }
  body { background: radial-gradient(circle at 50% 35%, #222030 0%, var(--bg) 70%); color: var(--text); overflow: hidden; height: 100vh; }
  #canvas-wrap { width: 100%; height: 100%; position: relative; }
  .hud { position: fixed; top: 16px; left: 16px; width: 300px; background: var(--panel); backdrop-filter: blur(12px);
         border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 16px; z-index: 10; box-shadow: 0 12px 32px rgba(0,0,0,0.45); }
  h1 { font-size: 15px; font-weight: 700; margin-bottom: 4px; letter-spacing: -0.01em; }
  .sub { font-size: 12px; color: var(--muted); margin-bottom: 14px; }
  .dims { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 14px; }
  .dim-box { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); border-radius: 8px; padding: 6px; text-align: center; }
  .dim-box b { display: block; font-size: 13px; color: #c4b5fd; }
  .dim-box span { font-size: 10px; color: var(--muted); }
  .ctrl { margin-bottom: 12px; }
  .ctrl label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 5px; color: #e5e7eb; }
  input[type=range] { width: 100%; accent-color: var(--accent); cursor: pointer; }
  .row { display: flex; gap: 8px; margin-bottom: 10px; }
  button { flex: 1; background: rgba(255,255,255,0.07); color: var(--text); border: 1px solid rgba(255,255,255,0.12);
           border-radius: 8px; padding: 8px 10px; font-size: 12px; font-weight: 600; cursor: pointer; transition: 0.15s; }
  button:hover { background: rgba(105,97,215,0.28); border-color: var(--accent); }
  button.active { background: var(--accent); border-color: #8b83f0; color: #fff; }
  .toggles { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 6px; }
  .chk { display: flex; align-items: center; gap: 6px; font-size: 11.5px; color: #d1d5db; cursor: pointer; }
  .chk input { accent-color: var(--accent); }
  .hint { position: fixed; bottom: 14px; left: 50%; transform: translateX(-50%); background: var(--panel);
          border: 1px solid rgba(255,255,255,0.08); border-radius: 999px; padding: 7px 14px; font-size: 11.5px; color: var(--muted); }
</style>
</head>
<body>
<div id="canvas-wrap"></div>
<div class="hud">
  <h1>Chaveiro 3D Rasec (LED)</h1>
  <div class="sub">Visualizador interativo das malhas STL reais</div>
  <div class="dims">
    <div class="dim-box"><b>4,84 cm</b><span>Largura</span></div>
    <div class="dim-box"><b>4,66 cm</b><span>Altura</span></div>
    <div class="dim-box"><b>2,50 cm</b><span>Profund.</span></div>
  </div>
  <div class="ctrl">
    <label><span>Visão Explodida</span><strong id="exp-val">0%</strong></label>
    <input id="explode" type="range" min="0" max="100" value="0" />
  </div>
  <div class="row">
    <button id="btn-anim">Explodir / Montar</button>
    <button id="btn-led" class="active">LED: Ligado</button>
  </div>
  <div class="row">
    <button id="btn-xray">Raio-X Base</button>
    <button id="btn-reset">Resetar Câmera</button>
  </div>
  <div class="toggles">
    <label class="chk"><input type="checkbox" id="vis-logo" checked /> Logo Roxa</label>
    <label class="chk"><input type="checkbox" id="vis-base" checked /> Base Oca</label>
    <label class="chk"><input type="checkbox" id="vis-lid" checked /> Tampa Botão</label>
    <label class="chk"><input type="checkbox" id="vis-elec" checked /> LED + CR2032</label>
  </div>
</div>
<div class="hint">Arraste para girar · Scroll para zoom · Botão direito para mover · Arraste qualquer .STL aqui</div>

<script type="importmap">
{ "imports": { "three": "https://unpkg.com/three@0.164.1/build/three.module.js", "three/addons/": "https://unpkg.com/three@0.164.1/examples/jsm/" } }
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

const STL_B64 = {
  logo: "__LOGO_B64__",
  base: "__BASE_B64__",
  lid:  "__LID_B64__"
};

const wrap = document.getElementById('canvas-wrap');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 0.5, 600);
camera.position.set(52, 42, 72);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
wrap.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 20, 0);

// Iluminacao de estudio
scene.add(new THREE.AmbientLight(0xffffff, 0.55));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.35);
keyLight.position.set(45, 70, 55);
scene.add(keyLight);
const rimLight = new THREE.DirectionalLight(0x9b8cff, 0.85);
rimLight.position.set(-55, 35, -45);
scene.add(rimLight);

// Grid de referencia em mm (cada quadrado = 10mm = 1cm)
const grid = new THREE.GridHelper(120, 12, 0x44405a, 0x262630);
scene.add(grid);

const loader = new STLLoader();
function parseB64STL(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return loader.parse(bytes.buffer);
}

const BASE_H = 13.5, LOGO_T = 3.8;
const matLogo = new THREE.MeshPhysicalMaterial({
  color: 0xb85cff, emissive: 0x6b21a8, emissiveIntensity: 0.45,
  roughness: 0.22, metalness: 0.05, transmission: 0.52, thickness: 4.0, transparent: true, opacity: 0.9
});
const matBase = new THREE.MeshStandardMaterial({ color: 0x202228, roughness: 0.58, metalness: 0.12 });
const matLid  = new THREE.MeshStandardMaterial({ color: 0x2a2d36, roughness: 0.52, metalness: 0.12 });

// 1. Base Oca (gira 180 em X e sobe BASE_H para ficar em pe: Y = 0..13.5)
const baseGeo = parseB64STL(STL_B64.base);
baseGeo.rotateX(Math.PI);
baseGeo.translate(0, 0, BASE_H);
baseGeo.rotateX(-Math.PI / 2); // Z-up CAD -> Y-up Three.js
const baseMesh = new THREE.Mesh(baseGeo, matBase);
scene.add(baseMesh);

// 2. Logo Translúcida em Pe (espigas entram 3.2mm dentro da base)
const logoGeo = parseB64STL(STL_B64.logo);
logoGeo.translate(0, 0, -LOGO_T / 2);
logoGeo.translate(0, BASE_H, 0);
const logoMesh = new THREE.Mesh(logoGeo, matLogo);
scene.add(logoMesh);

// 3. Tampa Inferior (encaixa em Y = 0)
const lidGeo = parseB64STL(STL_B64.lid);
lidGeo.rotateX(-Math.PI / 2);
const lidMesh = new THREE.Mesh(lidGeo, matLid);
scene.add(lidMesh);

// 4. Eletronica ilustrativa interna (CR2032 + LED 5mm + luz pontual)
const elecGroup = new THREE.Group();
const batMesh = new THREE.Mesh(
  new THREE.CylinderGeometry(10, 10, 3.2, 48),
  new THREE.MeshStandardMaterial({ color: 0xd1d5db, metalness: 0.85, roughness: 0.25 })
);
batMesh.position.set(-6.5, 5.2, 0);
elecGroup.add(batMesh);

const ledDome = new THREE.Mesh(
  new THREE.CapsuleGeometry(2.4, 3.2, 12, 24),
  new THREE.MeshStandardMaterial({ color: 0xf5d0fe, emissive: 0xd946ef, emissiveIntensity: 2.2, roughness: 0.15 })
);
ledDome.position.set(10.5, 7.6, 0);
elecGroup.add(ledDome);

const ledLight = new THREE.PointLight(0xd946ef, 320, 48, 1.8);
ledLight.position.set(10.5, 13.5, 0);
elecGroup.add(ledLight);
scene.add(elecGroup);

// Controle de visao explodida
let explodeTarget = 0, explodeCur = 0, animDir = 0;
const slider = document.getElementById('explode');
const expVal = document.getElementById('exp-val');

function applyExplode(t) {
  logoMesh.position.y = t * 24;
  elecGroup.position.y = -t * 14;
  lidMesh.position.y = -t * 28;
}

slider.addEventListener('input', () => {
  animDir = 0;
  explodeTarget = slider.value / 100;
  expVal.textContent = `${slider.value}%`;
});
document.getElementById('btn-anim').addEventListener('click', () => {
  explodeTarget = explodeTarget < 0.5 ? 1 : 0;
  animDir = 1;
});

let ledOn = true;
document.getElementById('btn-led').addEventListener('click', (e) => {
  ledOn = !ledOn;
  e.target.classList.toggle('active', ledOn);
  e.target.textContent = ledOn ? 'LED: Ligado' : 'LED: Desligado';
  ledLight.intensity = ledOn ? 320 : 0;
  matLogo.emissiveIntensity = ledOn ? 0.45 : 0.04;
  ledDome.material.emissiveIntensity = ledOn ? 2.2 : 0.1;
});

let xray = false;
document.getElementById('btn-xray').addEventListener('click', (e) => {
  xray = !xray;
  e.target.classList.toggle('active', xray);
  matBase.transparent = xray; matBase.opacity = xray ? 0.32 : 1.0; matBase.depthWrite = !xray;
  matLid.transparent  = xray; matLid.opacity  = xray ? 0.32 : 1.0; matLid.depthWrite  = !xray;
});

document.getElementById('btn-reset').addEventListener('click', () => {
  camera.position.set(52, 42, 72);
  controls.target.set(0, 20, 0);
});

document.getElementById('vis-logo').onchange = (e) => logoMesh.visible = e.target.checked;
document.getElementById('vis-base').onchange = (e) => baseMesh.visible = e.target.checked;
document.getElementById('vis-lid').onchange  = (e) => lidMesh.visible = e.target.checked;
document.getElementById('vis-elec').onchange = (e) => elecGroup.visible = e.target.checked;

// Drag-and-drop de qualquer arquivo .STL externo
window.addEventListener('dragover', (e) => e.preventDefault());
window.addEventListener('drop', async (e) => {
  e.preventDefault();
  const file = [...e.dataTransfer.files].find(f => f.name.toLowerCase().endsWith('.stl'));
  if (!file) return;
  const buf = await file.arrayBuffer();
  const geo = loader.parse(buf);
  geo.center();
  const custom = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0x6961d7, roughness: 0.4 }));
  custom.position.set(0, 22, 0);
  scene.add(custom);
});

window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

function animate() {
  requestAnimationFrame(animate);
  explodeCur += (explodeTarget - explodeCur) * 0.1;
  if (animDir) {
    const pct = Math.round(explodeCur * 100);
    slider.value = pct;
    expVal.textContent = `${pct}%`;
  }
  applyExplode(explodeCur);
  controls.update();
  renderer.render(scene, camera);
}
animate();
</script>
</body>
</html>
"""


def main() -> None:
    logo_b64 = base64.b64encode((STL_DIR / "01_logo_translucida_vertical.stl").read_bytes()).decode("ascii")
    base_b64 = base64.b64encode((STL_DIR / "02_base_pedestal_led.stl").read_bytes()).decode("ascii")
    lid_b64 = base64.b64encode((STL_DIR / "03_tampa_inferior_botao.stl").read_bytes()).decode("ascii")

    html = (
        HTML_TEMPLATE
        .replace("__LOGO_B64__", logo_b64)
        .replace("__BASE_B64__", base_b64)
        .replace("__LID_B64__", lid_b64)
    )
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Visualizador gerado: {OUT_HTML} ({OUT_HTML.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
