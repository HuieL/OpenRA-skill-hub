# Provenance

This is a carry of the upstream Anatomy skill (MIT) at exactly
`wheresryan22/anatomy` revision `1482e8469b0a9e0d8cc18ea2740a01423d29ae80`,
as pinned by the OpenRA research-videos module (VID02 pinned dependencies;
`docs/module-acceptance-criteria/research-videos.md`).

Carried verbatim, unmodified:

- `SKILL.md` (root skill contract)
- `LICENSE` (upstream MIT)
- `README.md` (upstream overview)
- `kit/` (SVG / WebGL / 3D kit: iso-kit, canvas-painter, gl, lathe, tube,
  turn controllers, react bindings)
- `references/` (craft, motion, webgl, 3D, verify, walkthrough, ...)
- `scripts/` (build, capture/drive and visual-audit scripts, plus the
  upstream `.test.mjs` self-tests for those scripts)

Not carried (deliberately, by the module's carry scope and the hub's
2 MiB per-entry cap):

- `examples/` — 25 MB of demo figure bundles; demos are not needed to use
  the skill and would exceed the entry cap
- `evals/`, `tests/` — upstream CI-side evaluation scaffolding
- `agents/`, `.github/` — repository infrastructure
- `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` —
  project documents, not skill content

No file carried here is edited relative to the pinned revision; any future
change is a new `source.revision` pin recorded in `entry.json`, and upstream
drift is compared through the hub's normal update diff.

The skill body is framework-free TypeScript/JS writing SVG/HTML; execution
happens in the host project on the user's machine. Nothing here runs at
catalog browse time.
