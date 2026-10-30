"""Synthetic metadata/slice fixtures only; no pilot cases or answer text."""
import copy
import hashlib
import unittest

try:
    from lab_runner.memory_benchmark.document_context import fetch_document_context
except ModuleNotFoundError as exc:
    if exc.name != "document_context":
        raise
    fetch_document_context = None


NAMESPACE = "pilot-michal-prosaic-20261025"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def fixture():
    catalog = dict(schemaVersion=1, namespace=NAMESPACE, corpusSha256=sha("manifest"),
                   sourceCount=5, recordCount=0, records={}, groups={})
    slices, sources = {}, {}
    specs = [("a", "note-orbit-controls.md", "notes", 7),
             ("b", "note-orbit-manual.md", "notes", 3),
             ("c", "note-orbit-reference.md", "notes", 3),
             ("d", "note-orbit-controls-details.md", "excluded-notes", 3),
             ("e", "session-orbit-controls.md", "sessions", 3)]
    for label, name, wing, count in specs:
        texts = [f"{label} section {i}: plain fixture prose.\n" for i in range(count)]
        source_id, group = sha(name), sha(label)
        sources[source_id] = dict(path="exports/" + name, sha256=sha("".join(texts)), wing=wing)
        catalog["groups"][group] = []
        for index, text in enumerate(texts):
            rid = f"{label}{index}"
            provenance = dict(record_id=rid, text_sha256=sha(text), revision="r1",
                              representation="project", wing=wing,
                              captured_at="2026-10-25T00:00:00Z", source_id=source_id)
            catalog["records"][rid] = dict(recordId=rid, textSha256=sha(text), revision="r1",
                representation="project", wing=wing, capturedAt=provenance["captured_at"],
                sourceId=source_id, chunkIndex=index, orderGroup=group,
                sourceFileSha256=sources[source_id]["sha256"])
            catalog["groups"][group].append(rid)
            slices[rid] = dict(record_id=rid, text_sha256=sha(text), slice_sha256=sha(text),
                text=text, start_char=0, next_start_char=None, complete=True,
                provenance=provenance, schema_version=1)
    catalog["recordCount"] = len(catalog["records"])
    return catalog, slices, sources, dict(slices["a3"]["provenance"], excerpt="preview")


class Provider:
    """Exact provider fetch boundary; no search or alternate read interface."""
    def __init__(self, slices):
        self.slices, self.calls = slices, []

    def fetch(self, record_id, start_char=0, max_chars=800):
        self.calls.append((record_id, start_char, max_chars))
        return copy.deepcopy(self.slices[record_id])


class DocumentContextTests(unittest.TestCase):
    def setUp(self):
        self.catalog, self.slices, self.sources, self.hit = fixture()
        self.provider = Provider(self.slices)

    def fetch(self, **kwargs):
        self.assertIsNotNone(fetch_document_context, "document context policy is not implemented")
        values = dict(provider=self.provider, seed_hit=self.hit, catalog=self.catalog,
                      namespace=NAMESPACE, allowed_wings=["notes", "sessions"],
                      sources=self.sources)
        values.update(kwargs)
        return fetch_document_context(**values)

    def test_introductions_and_neighbors_have_distinct_roles_and_exact_bytes(self):
        out = self.fetch()
        self.assertEqual([s["record_id"] for s in out], ["a3", "a0", "b0", "b1", "a2", "a4", "a1", "a5"])
        self.assertEqual([s["contextRole"] for s in out], ["seed", "sourceIntroduction",
                         "relatedIntroduction", "relatedIntroduction", "neighbor", "neighbor", "neighbor", "neighbor"])
        self.assertTrue(all(s["seedSourceId"] == self.hit["source_id"] for s in out))
        for value in out:
            core = {k: v for k, v in value.items() if k not in {"contextRole", "seedSourceId"}}
            self.assertEqual(core, self.slices[value["record_id"]])
        self.assertEqual(self.provider.calls, [(rid, 0, 800) for rid in ["a3", "a0", "b0", "b1", "a2", "a4", "a1", "a5"]])

    def test_seen_bodies_skip_duplicates_but_never_remove_seed(self):
        out = self.fetch(seen_ids=("a3", "a0", "b0", "a2"))
        self.assertEqual([s["record_id"] for s in out], ["a3", "b1", "a4", "a1", "a5"])
        self.assertEqual(len(self.provider.calls), 5)

    def test_highest_filename_similarity_wins_before_lexical_tie_break(self):
        sid = self.catalog["records"]["c0"]["sourceId"]
        self.sources[sid]["path"] = "exports/note-orbit-controls-overview.md"
        self.assertEqual([s["record_id"] for s in self.fetch()][2:4], ["c0", "c1"])

    def test_duplicate_source_paths_are_rejected_before_fetch(self):
        # Exact duplicate paths are ambiguous and must never become a ranking tie.
        b = self.catalog["records"]["b0"]["sourceId"]
        c = self.catalog["records"]["c0"]["sourceId"]
        self.sources[c]["path"] = self.sources[b]["path"]
        with self.assertRaises(ValueError):
            self.fetch()
        self.assertEqual(self.provider.calls, [])

    def test_nonmatching_filenames_do_not_trigger_related_reads(self):
        for rid, name in [("b0", "note-plain-manual.md"), ("c0", "note-other-reference.md")]:
            self.sources[self.catalog["records"][rid]["sourceId"]]["path"] = "exports/" + name
        out = self.fetch()
        self.assertEqual([s["record_id"] for s in out], ["a3", "a0", "a2", "a4", "a1", "a5"])

    def test_boundary_seed_is_unique_and_introduction_does_not_expand_radius(self):
        out = self.fetch(seed_hit=self.slices["a0"]["provenance"])
        self.assertEqual([s["record_id"] for s in out], ["a0", "b0", "b1", "a1", "a2"])
        self.assertEqual([s["contextRole"] for s in out], ["seed", "relatedIntroduction", "relatedIntroduction", "neighbor", "neighbor"])

    def test_invalid_namespace_wing_and_seed_fail_before_any_fetch(self):
        cases = [dict(namespace="other"), dict(allowed_wings=["sessions"]),
                 dict(allowed_wings="notes"), dict(seed_hit=dict(self.hit, revision="old")),
                 dict(seed_hit=dict(self.hit, record_id="missing"))]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.fetch(**changes)
        self.assertEqual(self.provider.calls, [])

    def test_invalid_source_mapping_or_ambiguous_identity_fails_before_fetch(self):
        sid = self.hit["source_id"]
        for key, value in [("sha256", "0" * 64), ("wing", "sessions"),
                           ("path", "../note-orbit-controls.md"), ("path", "/tmp/evil.md")]:
            sources = copy.deepcopy(self.sources)
            sources[sid][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.fetch(sources=sources)
        sources = copy.deepcopy(self.sources)
        del sources[sid]
        with self.assertRaises(ValueError):
            self.fetch(sources=sources)
        self.assertEqual(self.provider.calls, [])

    def test_tampered_related_bytes_and_cross_source_provenance_abort(self):
        for field, value in [("text", "tampered"), ("complete", False), ("start_char", True)]:
            provider = Provider(copy.deepcopy(self.slices))
            provider.slices["b1"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.fetch(provider=provider)
        provider = Provider(copy.deepcopy(self.slices))
        provider.slices["b1"]["provenance"]["source_id"] = self.hit["source_id"]
        with self.assertRaises(ValueError):
            self.fetch(provider=provider)

    def test_bad_catalog_index_or_seen_identity_is_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["records"]["a2"]["chunkIndex"] = True
        with self.assertRaises(ValueError):
            self.fetch(catalog=catalog)
        for seen in ["a0", ["missing"], [True]]:
            with self.subTest(seen=seen), self.assertRaises(ValueError):
                self.fetch(seen_ids=seen)
        self.assertEqual(self.provider.calls, [])


if __name__ == "__main__":
    unittest.main()
