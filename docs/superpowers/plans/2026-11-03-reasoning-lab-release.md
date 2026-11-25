# Lab 0.9.2 release plan

User explicitly authorized making CI green, fixing failures, merging all four
PRs (Lab42, Core3, Runtime15, Harness10) and releasing a new Lab version.
Execute inline with finishing/verification skills and a fresh read-only release
review. No further merge/publication confirmation is required.

Lab implementation head:776bbe043c5c49f79a6fbc3154b8665e73f895ec.
Current main:74f001ceba5afaeae011d8b456665ec2957e5a09.
Next available version:0.9.2. Both SDK manifests retain their exact existing pins.

1. Prepare 0.9.2 metadata, release guide/changelog and current handoff. Run local
   version-aware/package/reasoning checks, commit/push final source and qualify
   that exact head in both existing CI workflows. Diagnose/fix failures without
   suppressing required gates or treating missing infrastructure as a skip.
2. Review release integrity. Require all four service/database cells and both
   reasoning architectures. Download only original final-run lab-release-bytes,
   four safe acceptance receipts and two reasoning reports. Verify source/run
   identity, manifests, zero failed/skipped required cases and exact-owned cleanup.
3. Audit CI archives against committed source and clean inventories. Merge Lab42
   with expected qualified head and prove identical source/merge file trees.
   Merge Core3/Runtime15/Harness10 only on green CI and unchanged expected heads.
4. Tag the qualified Lab source without replacing a tag. Publish original CI
   archives, checksums and safe verification provenance on GitHub. Verify anonymous
   downloads and fresh public-wheel/rebuilt-source consumers; bind reasoning and
   ordinary manifests separately. Add post-publication evidence as new assets.

No new model inference, SDK publication, force push, tag/asset replacement or
unrelated working-tree changes. Preserve previous release evidence. Retain active
review worktrees until merged/verified; do not remove unrelated checkouts.
