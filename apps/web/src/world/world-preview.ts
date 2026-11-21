/**
 * World preview section, Phase 1 (SPEC.md A.18).
 *
 * Appends the placeholder Game-path stage and starts the scene. Kept
 * self-contained: the world module owns its own markup and inline styling
 * until the shared design system grows Game-path tokens, so no file outside
 * the world folder is touched beyond the single import in main.ts.
 */

import { renderRealLifeSummaryFallback } from './fallback';

const INLINE = 'box-sizing:border-box;';

//#region Mount policy (PR #25 review agreement)

/**
 * The preview mounts only through an explicit visitor action:
 * - click of the landing-page "See the 3D world" button
 *   (`#world-preview-button`, added with the apps/web owner's OK — the
 *   button-review sign-off in the PR is the record), or
 * - the `?world-preview=1` URL flag for direct links and review.
 *
 * Nothing is fetched until a mount actually happens: the landing page stays
 * byte-for-byte unchanged and the three.js chunk is never downloaded without
 * it. The real Game-path navigation (Phase 2, BU6) replaces this opt-in.
 */

let mounted = false;
/** True when the preview was requested through the landing-page button. */
let mountedByButton = false;

/** Loads the preview when the page carries the `?world-preview=1` flag. */
function initWorldPreviewFromUrlFlag(): void {
  if (new URLSearchParams(window.location.search).has('world-preview')) {
    initWorldPreview();
  }
}

/** Loads the preview when the visitor presses the landing-page button. */
function initWorldPreviewFromButton(): void {
  const button = document.getElementById('world-preview-button');
  if (button instanceof HTMLButtonElement) {
    button.addEventListener('click', () => {
      button.disabled = true;
      mountedByButton = true;
      initWorldPreview();
    }, { once: true });
  }
}

initWorldPreviewFromUrlFlag();
initWorldPreviewFromButton();

//#endregion

export function initWorldPreview(): void {
  if (mounted) return; // Guard against a double mount (button + flag).
  const main = document.querySelector('main');
  if (!main) return; // Not a page with a world stage; nothing to render.
  mounted = true;

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

  // When triggered by the button, bring the preview into view.
  if (mountedByButton) {
    try {
      section.scrollIntoView({ behavior: 'smooth', block: 'end' });
    } catch {
      // scrollIntoView not implemented — the section is on the page anyway.
    }
  }

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
