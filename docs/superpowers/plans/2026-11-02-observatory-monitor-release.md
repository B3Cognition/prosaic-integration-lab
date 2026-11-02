# Lab 0.9.1 release plan

The maintainer explicitly authorizes checking all four PR #41 cells, fixing
failures, merging and releasing a new version once green. Execute inline using
verification-before-completion and a fresh read-only release review. No extra
integration decision or permission is needed. Reuse the existing isolated
worktree; preserve unrelated checkouts and all earlier release evidence.

Base main: `9879e108c9fb77a892dae998fe0f449abf027f88`. Implementation head:
`f0398df87e0490ca96f51745da2305a6eccfc158`; its four cells passed in run41343271503.
Version: 0.9.1. SDK manifest remains unchanged.

1. Update package version, changelog, release guide and current handoff. Verify
   version-aware distribution tests, source assets and local build. Commit/push
   the versioned head and update PR #41 around its final release scope.
2. Require all four exact-versioned-head Linux AMD64/ARM64 × PostgreSQL16/18 cells.
   Diagnose/fix any failures; qualify a fresh head after source changes. Obtain
   a read-only review before merging and resolve material findings.
3. Download only the final run's original lab-release-bytes and four safe receipt
   artifacts. Verify run/head identities, all required lanes/counts, zero skips,
   cleanup, SDK manifest, original archive payloads against Git and clean inventory,
   and per-cell Python/Node test summaries.
4. Merge PR #41 with the expected qualified head. Verify identical merge/source
   file trees; tag the qualified source without replacing prior tags. Publish
   original CI archives, checksums, release notes and verification provenance.
5. Verify anonymous downloads and fresh public-wheel/rebuilt-source consumers,
   source frontend/assets and exact temporary cleanup. Record post-publication
   evidence in release assets/notes without rewriting the qualified source.

No new real-model inference, SDK changes, force pushes, global pruning, tag/asset
replacement or publication of private logs/state. Local builds verify inventory
but cannot replace original successful CI archives. Report actual PR/release URLs
and final evidence, including remaining capture/qualification limitations.
