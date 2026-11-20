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

export interface AssetManifestEntry {
  /** Logical key, e.g. "customer-bargain-hunter". */
  asset_key: string;
  /** Repo-relative path, e.g. "assets/customers/customer-bargain-hunter.glb". */
  path: string;
  contentType: string;
  license: string;
  /** Dimensions/model scale documentation string (A.18). */
  dimensions: string;
  /** sha256 checksum of the asset file. */
  checksum: string;
  owner: string;
  /** Key of the fallback asset, or null = fall back to the 2D summary view. */
  fallbackKey: string | null;
}

export interface AssetManifest {
  version: string;
  note: string;
  fallbackBehavior: string;
  assets: AssetManifestEntry[];
}

/** All asset keys the placeholder world scene may resolve. */
export type WorldAssetKey = 'business-sticker-shop' | 'customer-bargain-hunter' | 'event-social-buzz';

const WORLD_ASSET_KEYS: readonly WorldAssetKey[] = [
  'business-sticker-shop',
  'customer-bargain-hunter',
  'event-social-buzz',
];

/**
 * Static Vite import map, one entry per manifest `asset_key`. Vite needs
 * statically analysable imports to hash/serve the files; the manifest decides
 * which of these keys the scene actually uses.
 */
const ASSET_URL_LOADERS: Readonly<Record<WorldAssetKey, (() => Promise<{ default: string }>) | undefined>> = {
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
 * Resolves the loader for one asset key. Throws when the manifest is missing
 * an entry or declares a key the world module does not serve — both count as
 * "missing data" and trigger the fallback.
 */
export async function resolveAssetUrl(key: string): Promise<string | null> {
  const loader = ASSET_URL_LOADERS[key as WorldAssetKey];
  if (!loader) return null;
  try {
    const module = await loader();
    return module.default || null;
  } catch {
    // Asset file renamed/missing (Vite import failed) — treat as missing data.
    return null;
  }
}

/** Resolves every key the scene needs, or throws listing what is missing. */
export async function resolveWorldAssets(manifest: AssetManifest): Promise<Record<WorldAssetKey, string>> {
  const entries = new Map(manifest.assets.map((entry) => [entry.asset_key, entry]));
  const missing = WORLD_ASSET_KEYS.filter((key) => !entries.has(key));
  if (missing.length > 0) {
    throw new Error(`Asset manifest is missing required keys: ${missing.join(', ')}`);
  }
  const resolved = await resolveAllAssetUrls(WORLD_ASSET_KEYS, entries);
  return resolved;
}

async function resolveAllAssetUrls(
  keys: readonly WorldAssetKey[],
  entries: Map<string, AssetManifestEntry>,
): Promise<Record<WorldAssetKey, string>> {
  const urls: Partial<Record<WorldAssetKey, string>> = {};
  const failed: string[] = [];
  const resolution = await Promise.all(
    keys.map(async (key) => [key, await resolveAssetUrl(key)] as const),
  );
  for (const [key, url] of resolution) {
    if (url) urls[key] = url;
    else failed.push(entries.get(key)?.path ?? key);
  }
  if (failed.length > 0) {
    throw new Error(`World assets failed to resolve: ${failed.join(', ')}`);
  }
  return urls as Record<WorldAssetKey, string>;
}
