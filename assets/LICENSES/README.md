# Asset licenses and provenance (SPEC.md A.18)

All assets currently in `assets/` are **team-generated placeholders** created for
parallel code work (BUILD_PHASES.md phase 1). They are released as
**CC0 1.0 (public domain)** so any later choice of final art is unencumbered.

## Kenney Starter Kit

Placeholder 3D primitives in this repository are written by the team, not
downloaded. When production assets from the
[Kenny Starter Kit](https://kenney.nl) are introduced, that license notice
stays in this folder as required by the source. For reference, Kenney assets
are distributed under **CC0 1.0 Universal** — the notice is:

> "This startup is licensed under Creative Commons CC0 1.0 Universal. No
> attribution required, but always appreciated."
> — kenney.nl asset hub

(The verbatim notice file ships with the first PR that adds a Kenney asset.)

## Rules

- Every asset has a manifest entry in `assets/manifest.json` with
  `asset_key`, path, content type, license/source, dimensions/scale, checksum,
  owner and fallback key.
- Never commit artwork whose license is not recorded here.
