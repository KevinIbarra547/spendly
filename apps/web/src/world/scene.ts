/**
 * World scene bootstrap — Phase 1 placeholder (SPEC.md A.18, A.13).
 *
 * Renders a three.js 0.147.0 Game-path stage: ground, the placeholder Sticker
 * Shop and one placeholder customer, all resolved by `asset_key` from
 * `assets/manifest.json`. This scene plays no simulation role: it reads
 * assets only, decides nothing about who buys, prices, stock or money, and
 * falls back to the Real-life summary when anything fails to load.
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

import { loadManifest, resolveWorldAssets } from './assets';
import { renderRealLifeSummaryFallback } from './fallback';

const GAME_CANVAS_COLOR = 0x101827;
const GAME_SURFACE_COLOR = 0x1b293b;

/** Maximum wait for the manifest or any model fetch before falling back. */
const LOAD_TIMEOUT_MS = 8000;

export function mountWorldScene(stage: HTMLElement, canvas: HTMLCanvasElement): void {
  void loadWorldScene(stage, canvas);
}

/**
 * Races `promise` against a timeout; the timer is always cleared once the
 * promise settles, so nothing lingers after startup.
 */
function withTimeout<T>(promise: Promise<T>, what: string): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_resolve, reject) => {
    timer = setTimeout(() => reject(new Error(`Timed out loading ${what}`)), LOAD_TIMEOUT_MS);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

async function loadWorldScene(stage: HTMLElement, canvas: HTMLCanvasElement): Promise<void> {
  let renderer: THREE.WebGLRenderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  } catch (error) {
    renderRealLifeSummaryFallback(stage, `WebGL renderer unavailable (${(error as Error).message})`);
    return;
  }
  renderer.outputEncoding = THREE.sRGBEncoding;

  try {
    const manifest = await withTimeout(loadManifest(), 'asset manifest');
    const urls = await withTimeout(resolveWorldAssets(manifest), 'placeholder assets');

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(GAME_CANVAS_COLOR);

    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    camera.position.set(0, 2.2, 7.5);
    camera.lookAt(0, 1.1, 0);

    const hemisphere = new THREE.HemisphereLight(0xcfe3ff, 0x1b293b, 0.9);
    const key = new THREE.DirectionalLight(0xffffff, 0.8);
    key.position.set(4, 8, 6);
    scene.add(hemisphere, key);

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(24, 24),
      new THREE.MeshStandardMaterial({ color: GAME_SURFACE_COLOR, roughness: 1 }),
    );
    ground.rotation.x = -Math.PI / 2;
    scene.add(ground);

    const grid = new THREE.GridHelper(24, 24, 0x334155, 0x273449);
    scene.add(grid);

    const loader = new GLTFLoader();
    const [shop, customer] = await Promise.all([
      withTimeout(loadModel(loader, urls['business-sticker-shop']), 'business-sticker-shop.glb')
        .then((gltf) => { gltf.scene.position.set(-1.6, 0, 0); return gltf.scene; }),
      withTimeout(loadModel(loader, urls['customer-bargain-hunter']), 'customer-bargain-hunter.glb')
        .then((gltf) => { gltf.scene.position.set(1.6, 0, 2.2); gltf.scene.rotation.y = THREE.MathUtils.degToRad(135); return gltf.scene; }),
    ]);
    scene.add(shop, customer);

    // The placeholder scene is static: render on demand (once after setup,
    // and again on resize) instead of running a render loop that would
    // redraw an unchanged frame ~60 times per second on student Chromebooks.
    const renderFrame = () => renderer.render(scene, camera);
    resize(renderer, camera, canvas);
    renderFrame();
    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(() => {
        resize(renderer, camera, canvas);
        renderFrame();
      });
      observer.observe(canvas);
    }

    stage.querySelector('[data-loading-note]')?.remove();
    stage.dataset.state = 'ready';
  } catch (error) {
    renderer.dispose();
    renderRealLifeSummaryFallback(stage, (error as Error)?.message ?? 'unknown asset error');
  }
}

function resize(renderer: THREE.WebGLRenderer, camera: THREE.PerspectiveCamera, canvas: HTMLCanvasElement): void {
  const width = canvas.clientWidth || 960;
  const height = canvas.clientHeight || 360;
  renderer.setSize(width, height, false);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  camera.aspect = width / Math.max(height, 1);
  camera.updateProjectionMatrix();
}

function loadModel(loader: GLTFLoader, url: string): Promise<{ scene: THREE.Group }> {
  return new Promise((resolve, reject) => {
    loader.load(
      url,
      (gltf) => resolve({ scene: gltf.scene as THREE.Group }),
      undefined,
      (error) => reject(error instanceof Error ? error : new Error('GLTF load failed')),
    );
  });
}
