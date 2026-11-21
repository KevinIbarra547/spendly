# Asset licenses and provenance (SPEC.md A.18)

All assets currently in `assets/` are **team-generated placeholders** created for
parallel code work (BUILD_PHASES.md phase 1). They are released as
**CC0 1.0 (public domain)** so any later choice of final art is unencumbered.

## Kenney Starter Kit

Kenney assets (from kenney.nl) are distributed under the Creative Commons
**CC0 1.0 Universal** deed — no attribution required. This repository does not
yet contain any Kenney files. When the first Kenney Starter Kit asset lands
here, its verbatim license notice file ships in this folder in the same PR,
as required by the source.

## Rules

- Every asset has a manifest entry in `assets/manifest.json` with
  `asset_key`, path, content type, license/source, dimensions/scale, checksum,
  owner and fallback key.
- Never commit artwork whose license is not recorded here.
