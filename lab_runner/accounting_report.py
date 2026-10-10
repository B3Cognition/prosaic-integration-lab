"""Readable evidence from real fixture executions, not invented invoice data."""
from decimal import Decimal
from html import escape
import json
from pathlib import Path
from datetime import datetime


def accounting_snapshot(report):
    """Compare durable accounting while retaining a valid report-time witness."""
    timestamp=report.get('as_of')
    if type(timestamp) is not str:
        raise ValueError('accounting report time required')
    try:
        observed=datetime.fromisoformat(timestamp)
    except ValueError:
        raise ValueError('invalid accounting report time') from None
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise ValueError('accounting report time must include timezone')
    return {key:value for key,value in report.items() if key!='as_of'}


def write_report(report, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    runs = report['runs']
    ledger_calls = sum(run['usage']['total_calls'] for run in runs)
    complete = sum(run['usage']['complete_calls'] for run in runs)
    unknown = sum(run['usage']['unresolved_calls'] for run in runs)
    amounts = [Decimal(run['usage']['estimated_amounts']['USD']) for run in runs
               if 'USD' in run['usage']['estimated_amounts']]
    known_estimate = '$' + format(sum(amounts, Decimal(0)), '.6f') if amounts else 'Unknown'
    coverage = f'{complete} complete / {unknown} unresolved'
    def cell(value):
        return 'Unknown' if value is None else escape(str(value))
    def cost(value):
        return 'Unknown' if value is None else '$' + format(Decimal(value), '.6f')
    run_rows, call_rows = [], []
    for run in runs:
        usage = run['usage']
        estimate = usage['estimated_amounts'].get('USD')
        run_rows.append(f'''<tr><td>{cell(run['actor'])}</td><td>{cell(run['case'])}</td>
          <td>{cell(run['status'])}</td><td>{usage['total_calls']}</td>
          <td>{usage['complete_calls']} / {usage['unresolved_calls']}</td><td>{cost(estimate)}</td></tr>''')
        for index, call in enumerate(run['calls'], 1):
            call_rows.append(f'''<tr><td>{cell(run['actor'])}</td><td>{cell(run['case'])} · {index}</td>
              <td>{cell(call.get('input_tokens'))}</td><td>{cell(call.get('cached_input_tokens'))}</td>
              <td>{cell(call.get('output_tokens'))}</td><td>{cell(call['measurement_state'])}</td>
              <td>{cost(call.get('estimate_usd'))}</td></tr>''')
    raw = json.dumps(report, indent=2, allow_nan=False)
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prosaic accounting evidence</title><style>
:root {{ color-scheme:light dark; --bg:light-dark(#f7f9fc,#101820); --panel:light-dark(#fff,#19242e);
--text:light-dark(#152536,#e8eef5); --muted:light-dark(#526477,#a8bacb); --line:light-dark(#dce5ef,#344759);
--accent:light-dark(#176a69,#71cec4); }}
* {{ box-sizing:border-box }} body {{ margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,sans-serif }}
main {{ max-width:1180px;margin:auto;padding:36px 24px }} h1 {{ font-size:32px;line-height:1.2;margin:8px 0 12px }}
h2 {{ font-size:20px;margin-top:34px }} .eyebrow {{ color:var(--accent);font-weight:600;letter-spacing:.08em }}
.muted {{ color:var(--muted) }} .metrics {{ display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:28px 0 }}
.metric {{ background:var(--panel);padding:22px;border-radius:12px }} .value {{ font-size:28px;font-variant-numeric:tabular-nums;font-weight:600 }}
.scroll {{ overflow-x:auto }} table {{ width:100%;border-collapse:collapse;font-size:14px }}
th,td {{ padding:12px 10px;text-align:left;border-bottom:1px solid var(--line) }} th {{ color:var(--muted);font-weight:500 }}
td {{ font-variant-numeric:tabular-nums }} th:last-child,td:last-child {{ text-align:right }}
pre {{ white-space:pre-wrap;overflow-wrap:anywhere;max-height:440px;overflow:auto;background:var(--panel);padding:20px;font-size:12px }}
details {{ margin:28px 0 }} summary {{ color:var(--accent) }} footer {{ border-top:1px solid var(--line);padding-top:20px;margin-top:28px }}
@media(max-width:680px) {{ .metrics {{ grid-template-columns:1fr }} main {{ padding:24px 16px }} }}
</style></head><body><main>
<div class="eyebrow">PROSAIC · ACCOUNTING EVIDENCE</div>
<h1>What was called, measured, and estimated</h1>
<p class="muted">Actual runs through two service replicas and shared PostgreSQL. Synthetic inference; no paid calls.</p>
<div class="metrics">
<section class="metric"><div class="muted">Endpoint dispatches / ledger calls</div><div class="value">{report['independent_model_calls']} / {ledger_calls}</div><div>Independent counters agree</div></section>
<section class="metric"><div class="muted">Known estimate · USD</div><div class="value">{known_estimate}</div><div>Known portion only; fixture prices</div></section>
<section class="metric"><div class="muted">Measurement coverage</div><div class="value">{complete} / {ledger_calls}</div><div>{coverage}</div></section>
</div>
<h2>Owner-scoped run evidence</h2><div class="scroll"><table><thead><tr>
<th>User</th><th>Scenario</th><th>Workflow status</th><th>Calls</th><th>Complete / unknown</th><th>Known estimate · USD</th>
</tr></thead><tbody>{''.join(run_rows)}</tbody></table></div>
<h2>Every measured provider call</h2><div class="scroll"><table><thead><tr>
<th>User</th><th>Scenario / call</th><th>Input tokens</th><th>Cached input</th><th>Output tokens</th><th>Coverage</th><th>Estimate · USD</th>
</tr></thead><tbody>{''.join(call_rows)}</tbody></table></div>
<details><summary>Inspect the captured JSON evidence</summary><pre>{escape(raw)}</pre></details>
<footer class="muted">Synthetic rate card: $2 input, $8 output, $0.50 cached input per million tokens.
Rejected outputs retain their incurred usage. Missing usage stays unknown.
All assessments are billing-ineligible: estimates, not customer charges or invoices.
<br>Fixture ownership: {escape(report['ownership_id'])}</footer>
</main></body></html>'''
    (directory / 'accounting.json').write_text(raw + '\n')
    path = directory / 'accounting.html'
    path.write_text(page)
    return path
