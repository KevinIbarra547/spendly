/**
 * Entry for the dev-only world preview page (`apps/web/world-dev.html`).
 * Mounts the Phase 1 placeholder scene into the page root. Nothing here runs
 * on the public landing page; onboarding screens will use `mountWorld`
 * directly in Phase 2 (PR #25 review agreement).
 */

import { mountWorld } from './world-preview';

const root = document.getElementById('world-dev-root');
if (root) mountWorld(root);
