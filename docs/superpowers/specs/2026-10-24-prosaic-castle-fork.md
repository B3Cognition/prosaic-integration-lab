# Independent Prosaic Castle transition

Approved direction: independent fork, no original-repository backports. Baselines:
Castle 53637196cc215e9bd5b85b9253b3430b2781b884 and Lab 66d61bb. Preserve
original Git history, license, legacy code/tests and historic artifact profiles.

Default provider retains LanceDB, raw FTS ranking, read-only scope and exact
source/revision/hash checks. Packaging removes mandatory model/NLP dependencies
from provider installation, retaining explicit legacy/dense extras. Memory
stays disabled by default; dense and recency remain opt-in.

The four shipped SOAR rules become a separately opted-in Python policy with
differential tests, explicit trusted project/time context, top-50 and signed-score
behavior. Inventory custom rules; refuse them in this policy rather than pretend
equivalence. Retain legacy SOAR until custom-rule migration is demonstrated.

Retrieval judging, entity refinement and corpus-origin detection stay optional
consumer workflows through installed Runtime/Harness APIs. Validate complete
ranking permutations, preserve untouched tails and fallback/audit evidence.
Never run these jobs during ordinary retrieval or mutate source corpora
automatically. Host supplies provider configuration. Unqualified transports
remain explicit compatibility gaps, with their legacy code retained.

SUE remains separately installable with its existing execution identity and pure
engine bytes. Harness retains accepted state and frozen inputs through resume.
Prosaic review keeps its 64 KiB/16-source bound and independent disabled default.
Standalone Castle's 2 MiB/2,000-drawer path remains available in legacy code;
do not claim parity for the larger input or CLI transports.

Lab adds checksummed candidate profiles, preserving previous profiles and
hackathon v10. Run credential-free requirements comparison/replay, actual worker
snapshot/unavailable tests and full default/enabled suites. Fixture outcomes
prove mechanics, not model quality. No live inference, push or release.
