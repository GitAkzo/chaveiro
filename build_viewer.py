"""Gera index.html responsivo (GitHub Pages) com os 3 STLs embutidos e visao explodida."""

import base64
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
STL_DIR = PROJECT_DIR / "stl"
OUT_HTML = PROJECT_DIR / "index.html"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<title>Chaveiro 3D Rasec — Visualizador Interativo & Cotação STL</title>
<meta name="description" content="Visualizador 3D interativo com visão explodida, medidas em cm e download dos arquivos STL do Chaveiro 3D Rasec com base oca para LED." />
<meta property="og:title" content="Chaveiro 3D Rasec — Visualizador 3D & Arquivos STL" />
<meta property="og:description" content="4,84 × 4,66 × 2,50 cm · 3 peças sem suportes (Logo translúcida + Base oca LED + Tampa com botão). Gire em 3D e baixe os STLs." />
<meta property="og:image" content="https://gitakzo.github.io/chaveiro/preview_chaveiro_3d_v2.png" />
<meta property="og:type" content="website" />
<meta name="theme-color" content="#141414" />
<style>
  :root { --bg: #141414; --panel: rgba(22,22,27,0.88); --accent: #6961D7; --text: #f3f4f6; --muted: #9ca3af; --border: rgba(255,255,255,0.1); }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif; -webkit-tap-highlight-color: transparent; }
  html, body { background: radial-gradient(circle at 50% 35%, #242136 0%, var(--bg) 72%); color: var(--text); overflow: hidden; height: 100%; width: 100%; }
  #canvas-wrap { width: 100%; height: 100%; position: relative; touch-action: none; }
  .mobile-bar { display: none; position: fixed; top: 10px; left: 10px; right: 10px; z-index: 15; align-items: center; justify-content: space-between;
                background: var(--panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 12px; padding: 10px 12px; }
  .mobile-bar .m-title { font-size: 13.5px; font-weight: 700; }
  .mobile-bar .m-sub { font-size: 11px; color: #c4b5fd; }
  .mobile-bar button { flex: 0 0 auto; padding: 8px 12px; font-size: 12px; }
  .hud { position: fixed; top: 16px; left: 16px; width: 320px; max-height: calc(100vh - 32px); overflow-y: auto;
         background: var(--panel); backdrop-filter: blur(14px); border: 1px solid var(--border);
         border-radius: 16px; padding: 16px; z-index: 20; box-shadow: 0 14px 36px rgba(0,0,0,0.5); transition: transform 0.25s ease; }
  h1 { font-size: 16px; font-weight: 700; margin-bottom: 3px; }
  .sub { font-size: 12px; color: var(--muted); margin-bottom: 12px; }
  .dims { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 12px; }
  .dim-box { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); border-radius: 8px; padding: 6px; text-align: center; }
  .dim-box b { display: block; font-size: 13px; color: #c4b5fd; }
  .dim-box span { font-size: 10px; color: var(--muted); }
  .ctrl { margin-bottom: 12px; }
  .ctrl label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 5px; color: #e5e7eb; }
  input[type=range] { width: 100%; accent-color: var(--accent); cursor: pointer; height: 22px; }
  .row { display: flex; gap: 8px; margin-bottom: 8px; }
  button { flex: 1; background: rgba(255,255,255,0.07); color: var(--text); border: 1px solid var(--border);
           border-radius: 9px; padding: 9px 10px; font-size: 12px; font-weight: 600; cursor: pointer; transition: 0.15s; min-height: 36px; }
  button:hover { background: rgba(105,97,215,0.28); border-color: var(--accent); }
  button.active { background: var(--accent); border-color: #8b83f0; color: #fff; }
  .toggles { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 10px 0 12px; }
  .chk { display: flex; align-items: center; gap: 6px; font-size: 11.5px; color: #d1d5db; cursor: pointer; }
  .chk input { accent-color: var(--accent); width: 15px; height: 15px; }
  .sec-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin: 10px 0 6px; font-weight: 700; }
  .dl-list { display: flex; flex-direction: column; gap: 6px; }
  .dl-link { display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: #e5e7eb; font-size: 11.5px;
             background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 8px 10px; transition: 0.15s; }
  .dl-link:hover { border-color: var(--accent); background: rgba(105,97,215,0.2); }
  .dl-link span { font-size: 10.5px; color: #c4b5fd; }
  .note { margin-top: 10px; font-size: 11px; color: var(--muted); line-height: 1.45; background: rgba(105,97,215,0.1);
          border: 1px solid rgba(105,97,215,0.25); border-radius: 8px; padding: 8px 10px; }
  .hint { position: fixed; bottom: 14px; left: 50%; transform: translateX(-50%); background: var(--panel); white-space: nowrap;
          border: 1px solid var(--border); border-radius: 999px; padding: 7px 14px; font-size: 11.5px; color: var(--muted); z-index: 10; }
  @media (max-width: 768px) {
    .mobile-bar { display: flex; }
    .hud { top: auto; left: 10px; right: 10px; bottom: 10px; width: auto; max-height: 62vh; border-radius: 16px; }
    .hud.collapsed { transform: translateY(calc(100% + 24px)); }
    .hud h1, .hud .sub { display: none; }
    .hint { display: none; }
  }
</style>
</head>
<body>
<div id="canvas-wrap"></div>

<div class="mobile-bar">
  <div>
    <div class="m-title">Chaveiro 3D Rasec (LED)</div>
    <div class="m-sub">4,84 × 4,66 × 2,50 cm · ~11,8 g PLA</div>
  </div>
  <button id="btn-drawer" class="active">Controles & STLs</button>
</div>

<div class="hud collapsed" id="hud">
  <h1>Chaveiro 3D Rasec (LED)</h1>
  <div class="sub">Visualizador 3D interativo para impressão e cotação</div>
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
  <div class="sec-title">Baixar Arquivos STL (Sem Suportes)</div>
  <div class="dl-list">
    <a class="dl-link" href="stl/01_logo_translucida_vertical.stl" download>01. Logo Translúcida<span>Roxo · 3,4 g</span></a>
    <a class="dl-link" href="stl/02_base_pedestal_led.stl" download>02. Base Oca LED<span>Preto · 6,7 g</span></a>
    <a class="dl-link" href="stl/03_tampa_inferior_botao.stl" download>03. Tampa c/ Botão<span>Preto · 1,7 g</span></a>
  </div>
  <div class="note">
    <strong>Especificação para cotação:</strong> FDM bico 0.4 mm · Camada 0.20 mm · <strong>Zero suportes</strong>.<br/>
    Logo em <strong>PETG/PLA Roxo Translúcido</strong> (100% infill); Base e Tampa em <strong>Preto Fosco</strong> (20% infill).
  </div>
</div>

<div class="hint">Arraste para girar · Scroll para zoom · Cada quadrado do chão = 1 cm</div>

<script type="importmap">
{ "imports": { "three": "https://unpkg.com/three@0.164.1/build/three.module.js", "three/addons/": "https://unpkg.com/three@0.164.1/examples/jsm/" } }
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

const STL_B64 = { logo: "__LOGO_B64__", base: "__BASE_B64__", lid: "__LID_B64__" };
const isMobile = () => window.innerWidth <= 768;

const wrap = document.getElementById('canvas-wrap');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 0.5, 600);
function resetCamera() {
  const dist = isMobile() ? 1.28 : 1.0;
  camera.position.set(54 * dist, 42 * dist, 76 * dist);
  controls.target.set(0, 19, 0);
}

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
wrap.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
resetCamera();

scene.add(new THREE.AmbientLight(0xffffff, 0.58));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.35);
keyLight.position.set(45, 70, 55);
scene.add(keyLight);
const rimLight = new THREE.DirectionalLight(0x9b8cff, 0.85);
rimLight.position.set(-55, 35, -45);
scene.add(rimLight);
scene.add(new THREE.GridHelper(120, 12, 0x44405a, 0x262630));

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

const baseGeo = parseB64STL(STL_B64.base);
baseGeo.rotateX(Math.PI); baseGeo.translate(0, 0, BASE_H); baseGeo.rotateX(-Math.PI / 2);
const baseMesh = new THREE.Mesh(baseGeo, matBase); scene.add(baseMesh);

const logoGeo = parseB64STL(STL_B64.logo);
logoGeo.translate(0, 0, -LOGO_T / 2); logoGeo.translate(0, BASE_H, 0);
const logoMesh = new THREE.Mesh(logoGeo, matLogo); scene.add(logoMesh);

const lidGeo = parseB64STL(STL_B64.lid);
lidGeo.rotateX(-Math.PI / 2);
const lidMesh = new THREE.Mesh(lidGeo, matLid); scene.add(lidMesh);

const elecGroup = new THREE.Group();
const batMesh = new THREE.Mesh(new THREE.CylinderGeometry(10, 10, 3.2, 48),
  new THREE.MeshStandardMaterial({ color: 0xd1d5db, metalness: 0.85, roughness: 0.25 }));
batMesh.position.set(-6.5, 5.2, 0); elecGroup.add(batMesh);

const ledDome = new THREE.Mesh(new THREE.CapsuleGeometry(2.4, 3.2, 12, 24),
  new THREE.MeshStandardMaterial({ color: 0xf5d0fe, emissive: 0xd946ef, emissiveIntensity: 2.2, roughness: 0.15 }));
ledDome.position.set(10.5, 7.6, 0); elecGroup.add(ledDome);

const ledLight = new THREE.PointLight(0xd946ef, 320, 48, 1.8);
ledLight.position.set(10.5, 13.5, 0); elecGroup.add(ledLight);
scene.add(elecGroup);

let explodeTarget = 0, explodeCur = 0, animDir = 0;
const slider = document.getElementById('explode');
const expVal = document.getElementById('exp-val');
slider.addEventListener('input', () => { animDir = 0; explodeTarget = slider.value / 100; expVal.textContent = `${slider.value}%`; });
document.getElementById('btn-anim').addEventListener('click', () => { explodeTarget = explodeTarget < 0.5 ? 1 : 0; animDir = 1; });

let ledOn = true;
document.getElementById('btn-led').addEventListener('click', (e) => {
  ledOn = !ledOn; e.target.classList.toggle('active', ledOn);
  e.target.textContent = ledOn ? 'LED: Ligado' : 'LED: Desligado';
  ledLight.intensity = ledOn ? 320 : 0; matLogo.emissiveIntensity = ledOn ? 0.45 : 0.04; ledDome.material.emissiveIntensity = ledOn ? 2.2 : 0.1;
});

let xray = false;
document.getElementById('btn-xray').addEventListener('click', (e) => {
  xray = !xray; e.target.classList.toggle('active', xray);
  matBase.transparent = xray; matBase.opacity = xray ? 0.32 : 1.0; matBase.depthWrite = !xray;
  matLid.transparent  = xray; matLid.opacity  = xray ? 0.32 : 1.0; matLid.depthWrite  = !xray;
});

document.getElementById('btn-reset').addEventListener('click', resetCamera);
document.getElementById('vis-logo').onchange = (e) => logoMesh.visible = e.target.checked;
document.getElementById('vis-base').onchange = (e) => baseMesh.visible = e.target.checked;
document.getElementById('vis-lid').onchange  = (e) => lidMesh.visible = e.target.checked;
document.getElementById('vis-elec').onchange = (e) => elecGroup.visible = e.target.checked;

const hud = document.getElementById('hud');
const btnDrawer = document.getElementById('btn-drawer');
btnDrawer.addEventListener('click', () => {
  const open = hud.classList.toggle('collapsed');
  btnDrawer.textContent = open ? 'Controles & STLs' : 'Fechar Painel';
});

window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight);
});

(function animate() {
  requestAnimationFrame(animate);
  explodeCur += (explodeTarget - explodeCur) * 0.1;
  if (animDir) { const pct = Math.round(explodeCur * 100); slider.value = pct; expVal.textContent = `${pct}%`; }
  logoMesh.position.y = explodeCur * 24; elecGroup.position.y = -explodeCur * 14; lidMesh.position.y = -explodeCur * 28;
  controls.update(); renderer.render(scene, camera);
})();
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
    print(f"index.html gerado: {OUT_HTML} ({OUT_HTML.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
