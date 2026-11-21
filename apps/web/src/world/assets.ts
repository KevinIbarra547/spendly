/**
 * Manifest access for the world scene (SPEC.md A.18).
 *
 * The manifest at `assets/manifest.json` is the single source of truth for
 * logical `asset_key` values, paths, licenses, scale and fallback keys.
 * Frontend code resolves assets with `asset_key`; no hard-coded OS paths.
 *
 * If the manifest cannot be fetched or a required key is missing, callers
 * fall back to the Real-life summary view (see `fallback.ts`).
 */

import manifestUrl from '../../../../assets/manifest.json?url';

/** Required manifest fields (A.18). All snake_case to match `asset_key`. */
export interface AssetManifestEntry {
  /** Logical key, e.g. "customer-bargain-hunter". */
  asset_key: string;
  /** Repo-relative path, e.g. "assets/customers/customer-bargain-hunter.glb". */
  path: string;
  content_type: string;
  license: string;
  /** Dimensions/model scale documentation string (A.18). */
  dimensions: string;
  /** sha256 checksum of the asset file. */
  checksum: string;
  owner: string;
  /** Key of the fallback asset, or null = fall back to the 2D summary view. */
  fallback_key: string | null;
}

/** Shape of `assets/manifest.json`. */
export interface AssetManifest {
  version: string;
  note: string;
  fallback_behavior: string;
  assets: AssetManifestEntry[];
}

/** Every asset key the world module can serve today. */
export type WorldAssetKey = 'business-sticker-shop' | 'customer-bargain-hunter' | 'event-social-buzz';

/**
 * Keys the current placeholder scene depends on. `event-social-buzz` is
 * deliberately NOT here: it has no display in this phase, so a missing SVG
 * must not break the 3D scene (PR review, #25). It moves into this list when
 * the feature that displays it lands.
 */
const REQUIRED_WORLD_ASSET_KEYS: readonly WorldAssetKey[] = [
  'business-sticker-shop',
  'customer-bargain-hunter',
];

/**
 * Static Vite import map, one entry per served `asset_key`. Vite needs
 * statically analysable imports to hash/serve the files; the manifest decides
 * which of these keys the scene actually uses.
 */
const ASSET_URL_LOADERS: Readonly<Record<WorldAssetKey, () => Promise<{ default: string }>>> = {
  'business-sticker-shop': () => import('../../../../assets/businesses/business-sticker-shop.glb?url'),
  'customer-bargain-hunter': () => import('../../../../assets/customers/customer-bargain-hunter.glb?url'),
  'event-social-buzz': () => import('../../../../assets/events/event-social-buzz.svg?url'),
};

export async function loadManifest(): Promise<AssetManifest> {
  const response = await fetch(manifestUrl);
  if (!response.ok) {
    throw new Error(`Asset manifest request failed: ${response.status}`);
  }
  return (await response.json()) as AssetManifest;
}

/**
 * Resolves the loader for one asset key. Returns null when the key is not
 * served or its file fails to import (renamed/missing) — "missing data".
 */
export async function resolveAssetUrl(key: string): Promise<string | null> {
  const loader = ASSET_URL_LOADERS[key as WorldAssetKey];
  if (!loader) return null;
  try {
    const module = await loader();
    return module.default || null;
  } catch {
    return null;
  }
}

/**
 * Validates the manifest against the served key set, then resolves every
 * required key, or throws listing what is missing.
 */
export async function resolveWorldAssets(manifest: AssetManifest): Promise<Record<WorldAssetKey, string>> {
  const entries = new Map(manifest.assets.map((entry) => [entry.asset_key, entry]));

  const missing = REQUIRED_WORLD_ASSET_KEYS.filter((key) => !entries.has(key));
  if (missing.length > 0) {
    throw new Error(`Asset manifest is missing required keys: ${missing.join(', ')}`);
  }

  // Reverse-drift guard: keys the module serves but the manifest no longer
  // declares. Warning only — never simulatory, display-only keys may lag.
  const unserved = (Object.keys(ASSET_URL_LOADERS) as WorldAssetKey[])
    .filter((key) => !entries.has(key));
  if (unserved.length > 0) {
    console.warn('Asset keys served but absent from the manifest: ' + unserved.join(', '));
  }

  const urls: Partial<Record<WorldAssetKey, string>> = {};
  const failed: string[] = [];
  const resolution = await Promise.all(
    REQUIRED_WORLD_ASSET_KEYS.map(async (key) => [key, await resolveAssetUrl(key)] as const),
  );
  for (const [key, url] of resolution) {
    if (url) urls[key] = url;
    else failed.push(entries.get(key)?.path ?? key);
  }
  if (failed.length > 0) {
    throw new Error(`World assets failed to resolve: ${failed.join(', ')}`);
  }
  // event-social-buzz stays optional: resolve if present, never required.
  const iconUrl = await resolveAssetUrl('event-social-buzz');
  if (iconUrl) urls['event-social-buzz'] = iconUrl;
  return urls as Record<WorldAssetKey, string>;
}
