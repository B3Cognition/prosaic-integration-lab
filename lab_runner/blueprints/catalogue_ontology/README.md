# Catalogue ontology

Use the [Lab ontology guide](https://github.com/B3Cognition/prosaic-integration-lab/blob/main/docs/catalogue-ontology.md)
to install the released SDKs and copy the example into a fresh directory.

```sh
python host.py discover
python host.py discover --ontology
python host.py run
python host.py run --ontology
```

The first command shows the policy-scoped catalogue. The second adds the
ontology projection. Both run commands read one synthetic receipt locally.
The host supplies catalogue aliases and tool grants. Edit `workflow.yml`
to change the authored graph and `fixtures/attachment.json` to change the
public ontology metadata.
