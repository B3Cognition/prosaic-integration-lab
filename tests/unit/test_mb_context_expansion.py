"""Fixture-only tests; no pilot tasks, answers, queries, or actual corpus text."""
import copy
import hashlib
import unittest

from lab_runner.memory_benchmark.context_expansion import fetch_window, validate_catalog
from lab_runner.memory_benchmark.build_catalog import assemble_catalog

NAMESPACE = "pilot-michal-prosaic-20261025"
def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()

def fixture():
    texts = ["alpha\n", "bravó\n", "charlie\n", "delta\n", "echo\n", "foxtrot\n"]
    source_id = sha("/original/exports/fixture.md")
    records, slices = {}, {}
    group = sha("fixture-order-group")
    for i, text in enumerate(texts):
        rid = f"r{i}"
        records[rid] = dict(recordId=rid, textSha256=sha(text), revision="rev1",
            representation="project", wing="notes", sourceId=source_id, chunkIndex=i,
            orderGroup=group, sourceFileSha256=sha("".join(texts)), capturedAt="2026-10-25T00:00:00Z")
        provenance = dict(record_id=rid, text_sha256=sha(text), revision="rev1",
            representation="project", wing="notes", captured_at="2026-10-25T00:00:00Z",
            source_id=source_id)
        slices[rid] = dict(record_id=rid, text_sha256=sha(text), slice_sha256=sha(text),
            text=text, start_char=0, next_start_char=None, complete=True,
            provenance=provenance, schema_version=1)
    catalog = dict(schemaVersion=1, namespace=NAMESPACE, corpusSha256=sha("manifest"),
        sourceCount=1, recordCount=6, records=records, groups={group:list(records)})
    hit = dict(slices["r2"]["provenance"], score=1.0, rank=1, excerpt="charlie\n",
        excerpt_is_complete=True, alternate_sources=[], alternate_sources_complete=True)
    return catalog, slices, hit

class Provider:
    def __init__(self, slices):
        self.slices, self.calls = slices, []
    def fetch(self, record_id, start_char=0, max_chars=8000):
        self.calls.append((record_id, start_char, max_chars))
        return copy.deepcopy(self.slices[record_id])

class ExpansionTests(unittest.TestCase):
    def setUp(self):
        self.catalog, self.slices, self.hit = fixture()
        self.provider = Provider(self.slices)
    def run_window(self, **kw):
        return fetch_window(self.provider, self.hit, self.catalog, NAMESPACE, ["notes"], **kw)
    def test_valid_exact_bytes_order_and_bounded_fetch(self):
        out = self.run_window()
        self.assertEqual([s["record_id"] for s in out], ["r0","r1","r2","r3","r4"])
        self.assertEqual("".join(s["text"] for s in out), "alpha\nbravó\ncharlie\ndelta\necho\n")
        self.assertEqual(sum(len(s["text"].encode()) for s in out), 32)
        self.assertEqual(out, [self.slices[f"r{i}"] for i in range(5)])
        self.assertEqual(self.provider.calls, [(f"r{i}",0,800) for i in range(5)])
    def test_wrong_namespace_and_scope_reject_before_fetch(self):
        for namespace, wings in [("other",["notes"]),(NAMESPACE,["sessions"]),(NAMESPACE,"notes")]:
            with self.subTest(namespace=namespace,wings=wings), self.assertRaises(ValueError):
                fetch_window(self.provider,self.hit,self.catalog,namespace,wings)
        self.assertEqual(self.provider.calls, [])
    def test_stale_or_malformed_seed_rejected(self):
        for key,value in [("revision","rev0"),("text_sha256","0"*64),("source_id",sha("other")),
                          ("wing","sessions"),("representation","exchange"),("record_id","missing")]:
            with self.subTest(key=key):
                hit = dict(self.hit, **{key:value})
                with self.assertRaises(ValueError):
                    fetch_window(self.provider,hit,self.catalog,NAMESPACE,["notes"])
    def test_tampered_or_truncated_fetched_slice_rejected(self):
        changes = [("text","tampered"),("slice_sha256","A"*64),("complete",False),
            ("start_char",1),("next_start_char",2),("record_id","other"),("schema_version",2)]
        for key,value in changes:
            with self.subTest(key=key):
                catalog,slices,hit=fixture()
                slices["r1"][key]=value
                with self.assertRaises(ValueError):
                    fetch_window(Provider(slices),hit,catalog,NAMESPACE,["notes"])
    def test_returned_provenance_cannot_cross_source_revision_or_scope(self):
        for key,value in [("revision","rev2"),("source_id",sha("collision")),("wing","sessions"),
                          ("representation","exchange"),("text_sha256","f"*64),("record_id","r0")]:
            with self.subTest(key=key):
                catalog,slices,hit=fixture()
                slices["r1"]["provenance"][key]=value
                with self.assertRaises(ValueError):
                    fetch_window(Provider(slices),hit,catalog,NAMESPACE,["notes"])
    def test_missing_record_is_not_silently_ignored(self):
        del self.slices["r1"]
        with self.assertRaises((KeyError,ValueError)):
            self.run_window()
    def test_bad_radius_rejected_and_boundary_window_small(self):
        for radius in [-1,3,True,2.0]:
            with self.subTest(radius=radius),self.assertRaises(ValueError):
                self.run_window(radius=radius)
        self.assertEqual([x["record_id"] for x in self.run_window(radius=0)], ["r2"])
    def test_corrupt_catalog_groups_cannot_cross_provenance_or_hide_ids(self):
        mutations = [lambda c:c["records"]["r1"].update(revision="rev2"),
            lambda c:c["records"]["r1"].update(sourceId=sha("collision")),
            lambda c:c["records"]["r1"].update(chunkIndex=5),
            lambda c:c["records"].pop("r1"),
            lambda c:c.update(query="forbidden"),
            lambda c:c["records"]["r1"].update(rawSourcePath="/private/path")]
        for mutate in mutations:
            catalog,slices,hit=fixture(); mutate(catalog)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                fetch_window(Provider(slices),hit,catalog,NAMESPACE,["notes"])

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.original="/original/exports/fixture.md"
        self.data=b"one\ntwo\n"
        self.revision=sha("3:project:one\ntwo\n")[:24]
        self.manifest=dict(namespace=NAMESPACE, sourceCount=1,
            files=[dict(path="exports/fixture.md",wing="notes",sha256=sha(self.data),bytes=8)])
        self.imported=dict(sources=[dict(source=self.original,wing="notes",sha256=sha(self.data),
            drawers=2,revision=self.revision,exactReconstruction=True,recordIds=["a","b"])])
        self.rows=dict(ids=["b","a"],documents=["two\n","one\n"],metadatas=[
            dict(source_file=self.original,source_revision=self.revision,representation="project",
                 wing="notes",chunk_index=i,ingest_complete=True,filed_at="2026-10-25T00:00:00Z") for i in [1,0]])
    def build(self):
        return assemble_catalog(self.manifest,self.imported,self.rows,{"exports/fixture.md":self.data},sha("manifest"))
    def test_catalog_joins_source_exactly_and_keeps_only_metadata(self):
        c=self.build()
        validate_catalog(c)
        self.assertEqual(c["recordCount"],2)
        self.assertEqual(c["records"]["a"]["sourceId"],sha(self.original))
        self.assertEqual(c["groups"][c["records"]["a"]["orderGroup"]],["a","b"])
        self.assertNotIn(self.original,str(c))
        self.assertNotIn("one\ntwo",str(c))
    def test_rejects_incomplete_contiguity_source_hash_revision_and_import_id_mismatch(self):
        mutations=[lambda:self.rows["documents"].__setitem__(0,"bad"),
            lambda:self.rows["metadatas"][0].update(chunk_index=3),
            lambda:self.rows["metadatas"][0].update(source_revision="old"),
            lambda:self.rows["metadatas"][0].update(ingest_complete=False),
            lambda:self.rows["metadatas"][0].update(source_file="/collision/fixture.md"),
            lambda:self.imported["sources"][0].update(recordIds=["missing","b"]),
            lambda:self.manifest["files"][0].update(sha256="0"*64)]
        for mutation in mutations:
            self.setUp(); mutation()
            with self.subTest(mutation=mutation),self.assertRaises(ValueError): self.build()

if __name__ == "__main__": unittest.main()
