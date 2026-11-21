/**
 * Real-life summary fallback (SPEC.md A.18 / `apps/web/src/world/AGENTS.md`).
 * When the 3D load fails or model/manifest data is missing, the Game-path
 * stage is replaced with a calm, clearly-labelled two-dimensional summary
 * instead of a broken canvas.
 */

const INLINE = 'box-sizing:border-box;';

export function renderRealLifeSummaryFallback(container: HTMLElement, reason?: string): void {
  container.innerHTML = '';
  container.dataset.state = 'fallback';

  const card = document.createElement('div');
  card.setAttribute('role', 'status');
  card.style.cssText = `${INLINE}height:100%;width:100%;padding:24px;color:#F8FAFC;` +
    'background:#1B293B;border-radius:12px;display:flex;flex-direction:column;gap:8px;' +
    'font:16px/1.5 Inter, system-ui, sans-serif;';

  const heading = document.createElement('h3');
  heading.textContent = 'Real-life summary (fallback view)';
  heading.style.cssText = 'font-size:20px;margin:0;color:#F8FAFC;';

  const body = document.createElement('p');
  body.textContent = 'The 3D world could not load, so the calm Real-life summary is shown instead. Refresh the page to try the 3D world view again.';
  body.style.cssText = 'margin:0;color:#C3CEDB;';

  const list = document.createElement('ul');
  list.style.cssText = 'margin:8px 0 0;padding-left:20px;color:#C3CEDB;';
  for (const line of ['Visitors: —', 'Units sold: —', 'Wallet change: —']) {
    const item = document.createElement('li');
    item.textContent = line;
    list.append(item);
  }

  const placeholderNote = document.createElement('p');
  placeholderNote.textContent = 'Placeholder screen — day playback (BU6) is not wired to the engine yet. No money or simulation data is shown.';
  placeholderNote.style.cssText = `${INLINE}margin-top:auto;color:#FBBF24;font-size:12px;`;

  card.append(heading, body, list, placeholderNote);

  if (reason) {
    const detail = document.createElement('p');
    detail.textContent = `Reason: ${reason}`;
    detail.style.cssText = 'margin:0;color:#C3CEDB;font-size:12px;';
    card.append(detail);
  }

  container.append(card);
}
