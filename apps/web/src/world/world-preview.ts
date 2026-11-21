/**
 * World preview section, Phase 1 (SPEC.md A.18).
 *
 * Appends the placeholder Game-path stage to the landing page and starts the
 * scene. Kept self-contained: the world module owns its own markup and inline
 * styling until the shared design system grows Game-path tokens, so no file
 * outside the world folder is touched beyond the one-line import in main.ts.
 */

import { renderRealLifeSummaryFallback } from './fallback';

const INLINE = 'box-sizing:border-box;';

/**
 * Dev/preview-only mount (PR #25 review agreement): the preview renders only
 * when the page is opened with `?world-preview=1`, so the public landing page
 * stays byte-for-byte unchanged and nothing fetches the three.js chunk
 * without an explicit request. Re-homing behind the real Game-path route is
 * Phase 2 (BU6) work.
 */
export function initWorldPreview(): void {
  const requested = new URLSearchParams(window.location.search).has('world-preview');
  if (!requested) return;
  const main = document.querySelector('main');
  if (!main) return; // Not a page with a world stage; nothing to render.

  const section = document.createElement('section');
  section.className = 'world-preview';
  section.setAttribute('aria-labelledby', 'world-preview-title');
  section.style.cssText = 'padding:48px 0;';

  const inner = document.createElement('div');
  inner.style.cssText = `${INLINE}max-width:1440px;margin:0 auto;padding:0 24px;`;

  const title = document.createElement('h2');
  title.id = 'world-preview-title';
  title.textContent = 'World preview (Game path placeholder)';
  title.style.cssText = 'margin:0 0 4px;font-size:28px;color:#172033;';

  const blurb = document.createElement('p');
  blurb.textContent =
    'Phase 1 placeholder scene: ground plus placeholder Sticker Shop and customer models from the asset manifest. Day playback (BU6) arrives in phase 2.';
  blurb.style.cssText = 'margin:0 0 16px;color:#596579;';

  const stage = document.createElement('div');
  stage.className = 'world-stage';
  stage.dataset.state = 'loading';
  stage.style.cssText = `${INLINE}height:360px;border-radius:12px;overflow:hidden;` +
    'background:#101827;position:relative;';

  const canvas = document.createElement('canvas');
  canvas.setAttribute('role', 'img');
  canvas.setAttribute(
    'aria-label',
    'Placeholder 3D world preview: a ground plane with the Sticker Shop and one customer standing beside it',
  );
  canvas.style.cssText = `${INLINE}width:100%;height:100%;display:block;`;

  const loading = document.createElement('p');
  loading.setAttribute('data-loading-note', '');
  loading.textContent = 'Loading placeholder world…';
  loading.setAttribute('aria-live', 'polite');
  loading.style.cssText = `${INLINE}margin:0;padding:16px;color:#C3CEDB;font:12px/1.5 Inter, system-ui, sans-serif;`;

  stage.append(loading, canvas);
  inner.append(title, blurb, stage);
  section.append(inner);

  main.append(section);

  void bootstrapWorldScene(stage);
}

/**
 * Loads the scene (and, through it, `assets.ts` and the three.js loaders)
 * dynamically. If any module in that subtree fails to resolve — for example a
 * renamed or missing placeholder model — the dynamic import rejects, the page
 * above survives untouched, and the Real-life summary fallback takes over.
 */
async function bootstrapWorldScene(stage: HTMLElement): Promise<void> {
  try {
    const { mountWorldScene } = await import('./scene');
    mountWorldScene(stage, stage.querySelector('canvas') as HTMLCanvasElement);
  } catch (error) {
    renderRealLifeSummaryFallback(stage, (error as Error)?.message ?? 'world module failed to load');
  }
}

initWorldPreview();
