# Lab 0.9.0 release plan

The maintainer explicitly authorized the version bump, release notes, PR, all
four CI cells, fixes, merge and publication after green qualification. Execute
inline using executing-plans and verification-before-completion. No additional
merge/release confirmation is needed.

Base main: `4787265953bbda9a9e7ed63b500d152b8bcf486b`. Existing feature head:
`391f67100541371f2a71a9055a26ed15acddfd48`. The isolated worktree is reused;
preserve the unrelated original checkout and all earlier artifacts/tags.

- [ ] Prepare 0.9.0 metadata, changelog and release guide; verify source/build.
- [ ] Commit/push, open a PR against main, attach it and run the exact head's
  Linux AMD64/ARM64 × PostgreSQL 16/18 cells. Fix failures and qualify the new head.
- [ ] Obtain a fresh read-only review of release readiness; fix material findings
  with regression evidence. Verify all safe receipts and original archive bytes.
- [ ] Merge with the expected qualified head. Verify the merge file tree equals
  the qualified source; tag that source without replacing any previous tag.
- [ ] Publish original CI wheel/sdist plus checksums and provenance. Verify
  anonymous downloads, clean public-wheel/rebuilt-source consumers and cleanup.
- [ ] Report actual PR/release URLs and final evidence.

Constraints: unchanged SDK train; no paid inference, force pushes, tag/asset
replacement or publication of private logs/state. Local rebuilds cannot replace
the qualified CI artifacts. Rerun the required matrix if implementation/source
qualification changes. Record post-publication evidence in the release assets
and notes without rewriting the qualified source.
