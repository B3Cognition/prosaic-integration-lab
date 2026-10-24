# Prosaic Castle Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an independent fork, optional model jobs and installed Lab/
hackathon qualification while retaining legacy capabilities.

**Architecture:** Preserve Castle compatibility code; ship a lean FTS provider
and pure SUE separately. Lab composes optional model jobs using public Runtime/
Harness APIs. Ordinary retrieval dispatches neither models nor SOAR.

**Tech Stack:** Python, LanceDB/Tantivy, Runtime 0.9.8, Harness 0.9.4,
PostgreSQL 16/18, pytest, wheel/sdist.

**Spec:** ../specs/2026-10-24-prosaic-castle-fork.md

## Global Constraints

- No original Castle backports or historic evidence rewrites.
- Memory/review independently disabled; raw FTS default; dense/boosts opt-in.
- Preserve scope, provenance, revision, exact bytes and installed SDK boundaries.
- No live inference, push, release or publication.

## Review Focus

- Custom rules must fail admission instead of disappearing.
- Invalid permutations preserve original ranking and untouched tail.
- Missing memory never triggers model fallback or redispatch.
- Resume retains frozen source, owner and accounting bindings.
- Lean install must operate without embedding, NLP or SOAR packages.

### Task 1: Independent distribution

Files: fork pyproject.toml, README, provenance, packaging tests.
Produces: installed prosaic-castle worker plus unchanged thin adapter/SUE.

- [ ] Add failing metadata/import/actual-worker checks in lean environment.
- [ ] Implement fork metadata, optional dependency groups and provenance.
- [ ] Build/rebuild wheel/sdist; verify installed payload and real FTS worker.

### Task 2: Deterministic rules

Files: fork policy module, custom-rule inventory, differential tests.
Produces: opt-in pure policy API with explicit project/clock, no SML import.

- [ ] Test all four rules, signed/tied scores, top-50, bad/future dates,
  repeated calls and custom-rule rejection; watch failures.
- [ ] Implement policy; compare legacy bridge via rule-output oracle and
  record real SML qualification as separate gate.
- [ ] Run focused/legacy suites and retain custom-rule inventory.

### Task 3: Optional model jobs

Files: Lab jobs module, tests and guide.
Produces: host-opted-in ranking/refinement/origin sessions using public SDKs.

- [ ] Watch failing tests for disabled zero calls, malformed fallback,
  permutations/tail, frozen input and receipt-only resume.
- [ ] Implement explicit jobs with immutable source binding and audit.
- [ ] Verify fixture attribution; document retained transport compatibility.

### Task 4: Lab and hackathon adoption

Files: new dependency profile, installed integration tests/runner and guides.
Consumes: installed Task 1 artifacts and Task 2/3 public interfaces.

- [ ] Add failing installed scope/snapshot/resume/unavailable composition tests.
- [ ] Adopt new candidate hashes without changing old profiles/engine identity.
- [ ] Run full default/enabled suites, installed PostgreSQL 16/18 lanes and
  requirements matrix/replay; preserve historical scorer and evidence.
- [ ] Record evidence, independent review, local commits and remaining gates.
