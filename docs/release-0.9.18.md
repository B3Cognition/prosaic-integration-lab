# Lab 0.9.18 — guarded workflow recovery

The [guarded recovery blueprint](guarded-recovery.md) shows how a trusted
host configures Runtime recovery through Harness and reads the durable
outcome. The example requires a lookup and checks the final answer against
the tool result.

The separate recovery profile pins Core 0.5.1, Runtime 0.9.25, Harness
0.9.19, recorder 0.3.0 and store 0.4.5 from released wheels. The existing
ontology and reasoning profiles retain their versions and evidence.

The installed blueprint lane covers both synthetic provider wires from
the Lab wheel and a wheel rebuilt from the source archive. It checks the
original invocation budget, exactly one authorized read, correction and
retry evidence, and resume with matching or changed host settings.
No live inference is required.
