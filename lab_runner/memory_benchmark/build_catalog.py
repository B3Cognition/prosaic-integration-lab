"""Private operator-stage whole-index metadata seal builder. No task access."""
import argparse
import json
from pathlib import Path

from .context_expansion import NAMESPACE, WINGS, validate_catalog, _require, _sha, _hex

def assemble_catalog(manifest, imported, rows, source_bytes, corpus_sha256):
    """Validate full original import against exact original exports; emit metadata."""
    _require(manifest.get("namespace") == NAMESPACE and _hex(corpus_sha256), "manifest identity")
    files, sources = manifest["files"], imported["sources"]
    _require(type(files) is list and type(sources) is list and len(files) == len(sources)
        == manifest["sourceCount"] and bool(files), "source count")
    file_map = {item["path"]:item for item in files}
    _require(len(file_map) == len(files) and set(file_map) == set(source_bytes), "source files")
    expected_ids = [rid for source in sources for rid in source["recordIds"]]
    ids, docs, metas = (rows[key] for key in ["ids","documents","metadatas"])
    _require(all(type(value) is list for value in [ids,docs,metas]) and
        len(ids) == len(docs) == len(metas) == len(expected_ids) and
        len(set(ids)) == len(ids) and set(ids) == set(expected_ids)
        and len(set(expected_ids)) == len(expected_ids), "exact imported ids")
    by_id = dict(zip(ids,zip(docs,metas)))
    records, groups, used_paths = {}, {}, set()
    for source in sources:
        original = source.get("sourceFileOriginal", source.get("source"))
        _require(type(original) is str and Path(original).is_absolute(), "original source path")
        relative = "exports/" + Path(original).name
        _require(relative in file_map and relative not in used_paths, "original source collision")
        used_paths.add(relative)
        entry, raw = file_map[relative], source_bytes[relative]
        _require(type(raw) is bytes, "source bytes")
        text = raw.decode("utf-8")
        revision = _sha(("3:project:"+text).encode())[:24]
        _require(_sha(raw) == entry["sha256"] == source["sha256"] and len(raw) == entry["bytes"], "source hash")
        _require(source["revision"] == revision and source["wing"] == entry["wing"]
            and source["wing"] in WINGS and source["exactReconstruction"] is True, "source metadata")
        record_ids = source["recordIds"]
        _require(type(source["drawers"]) is int and source["drawers"] == len(record_ids) > 0, "drawer count")
        source_id = _sha(original.encode())
        group = _sha(json.dumps([source_id,source["wing"],revision,"project"],separators=(",",":")).encode())
        _require(group not in groups, "source group collision")
        ordered = []
        for rid in record_ids:
            doc, meta = by_id[rid]
            _require(type(doc) is str and 0 < len(doc) <= 800 and type(meta) is dict, "record bounds")
            _require(meta.get("source_file") == original and meta.get("source_revision") == revision
                and meta.get("representation") == "project" and meta.get("wing") == source["wing"]
                and meta.get("ingest_complete") is True and type(meta.get("chunk_index")) is int,
                "record source metadata")
            ordered.append((meta["chunk_index"],rid,doc,meta))
        ordered.sort()
        _require([row[0] for row in ordered] == list(range(len(ordered))) and
            [row[1] for row in ordered] == record_ids and
            "".join(row[2] for row in ordered).encode() == raw, "full exact source reconstruction")
        groups[group] = record_ids[:]
        for index,rid,doc,meta in ordered:
            records[rid] = dict(recordId=rid,textSha256=_sha(doc.encode()),revision=revision,
                representation="project",wing=source["wing"],sourceId=source_id,chunkIndex=index,
                orderGroup=group,sourceFileSha256=_sha(raw),capturedAt=meta.get("filed_at"))
    _require(used_paths == set(file_map), "all sources covered")
    return validate_catalog(dict(schemaVersion=1,namespace=NAMESPACE,corpusSha256=corpus_sha256,
        sourceCount=len(groups),recordCount=len(records),records=records,groups=groups))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--palace",type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve(strict=True)
    _require(not args.output.exists(), "catalog output already exists")
    manifest_bytes = (archive/"corpus-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    imported = json.loads((archive/"import-result.json").read_bytes())
    _require(manifest.get("sourceCount") == 18 and len(imported["sources"]) == 18
        and sum(len(s["recordIds"]) for s in imported["sources"]) == 414, "sealed pilot cardinality")
    source_bytes = {}
    for entry in manifest["files"]:
        relative = entry["path"]
        _require(type(relative) is str and relative.startswith("exports/") and
            len(Path(relative).parts) == 2 and relative.endswith(".md"), "export path")
        path = (archive/relative).resolve(strict=True)
        _require(path.is_relative_to((archive/"exports").resolve(strict=True)), "export escape")
        source_bytes[relative] = path.read_bytes()
    from cognitive_castle.config import CognitiveCastleConfig
    from cognitive_castle.context import CastleContext, PalacePaths
    config_dir = archive/"config"
    _require((config_dir/"config.json").is_file(), "explicit config")
    cfg = CognitiveCastleConfig(config_dir=config_dir)
    palace = (args.palace or archive/"frozen-palace").resolve(strict=True)
    paths = PalacePaths.resolve(palace,config_dir=config_dir)
    identity_path = paths.provider/"identity.json"
    _require(json.loads(identity_path.read_text()) == {"schema_version":1,"namespace":NAMESPACE}, "palace namespace")
    with CastleContext.open(paths,config=cfg,create=False,read_only=True) as context:
        # Whole authorized index, no query/results selection and no task files.
        rows = context.get_collection().get(include=["documents","metadatas"])
        catalog = assemble_catalog(manifest,imported,rows,source_bytes,_sha(manifest_bytes))
    payload = (json.dumps(catalog,ensure_ascii=False,indent=2)+"\n").encode()
    with args.output.open("xb") as target:
        target.write(payload)
    print(json.dumps(dict(catalogSha256=_sha(payload),sourceCount=catalog["sourceCount"],
        recordCount=catalog["recordCount"],metadataOnly=True,readOnly=True)))

if __name__ == "__main__":
    main()
