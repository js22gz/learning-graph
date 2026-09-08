#!/usr/bin/env python3
"""Compile /home/box/learning-graph → docs/index.html (one page)."""
from pathlib import Path
import html
import re
from datetime import date

ROOT = Path("/home/box/learning-graph")
OUT = Path(__file__).resolve().parent / "docs" / "index.html"

def esc(s: str) -> str:
    return html.escape(s)

def md_inline(s: str) -> str:
    """Escape, then turn **bold** into <strong>."""
    s = esc(s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

def public_source(line: str) -> str:
    # author-year only; drop local disk paths if any slipped through
    line = re.sub(r"\s*\|\s*path:\s*/home/box/[^\n]*", "", line)
    line = re.sub(r"/home/box/[^\s|]+", "", line)
    return line

brief = (ROOT / "brief.md").read_text()
oq = (ROOT / "open-questions.md").read_text()
claim = (ROOT / "claims/C0-retrieval.md").read_text()
ledger = (ROOT / "ledgers/C0-retrieval.md").read_text()

fields = {}
for line in claim.splitlines():
    if line.startswith("Claim:"):
        fields["Claim"] = line[len("Claim:"):].strip()
    elif ":" in line:
        k, _, v = line.partition(":")
        if k.strip() == "C0" or (k.startswith("C") and len(k) > 1 and k[1:].isdigit()):
            continue
        fields[k.strip()] = v.strip()

status = fields.get("Status", "alive")
claim_text = fields.get("Claim", "")
slug = fields.get("Slug", "retrieval")
last = fields.get("Last change", "")
kill = fields.get("What would kill this", "")
tutor = fields.get("Tutor consequence", "none yet")
bounds = fields.get("Bounds", "")

# ledger blocks
ledger_blocks = []
lines = ledger.strip().splitlines()
rest = "\n".join(lines[1:]).strip() if lines and lines[0].startswith("Ledger") else ledger.strip()
if rest:
    cur = []
    for ln in rest.splitlines():
        if len(ln) >= 10 and ln[:4].isdigit() and ln[4] == "-" and ln[7] == "-" and (len(ln) == 10 or ln[10:11] in ("", " ")):
            if cur:
                ledger_blocks.append("\n".join(cur))
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        ledger_blocks.append("\n".join(cur))

# sanitize sources in ledger display
clean_blocks = []
for b in ledger_blocks:
    cleaned = []
    for ln in b.splitlines():
        if ln.startswith("Source:"):
            cleaned.append(public_source(ln))
        else:
            cleaned.append(ln)
    clean_blocks.append("\n".join(cleaned))

brief_lines = [ln.strip() for ln in brief.splitlines() if ln.strip() and not ln.startswith("#")]
oq_items = []
for ln in oq.splitlines():
    if ln.startswith("#"):
        continue
    s = ln.strip()
    if not s:
        continue
    if s[0].isdigit() and "." in s[:4]:
        oq_items.append(s.split(".", 1)[-1].strip())
    elif s.startswith("-"):
        oq_items.append(s[1:].strip())
    else:
        oq_items.append(s)

status_class = {"alive": "alive", "weakened": "weakened", "killed": "killed"}.get(status, "alive")
ledger_html = (
    '<p class="muted">No attacks logged yet.</p>'
    if not clean_blocks
    else "\n".join(f'<pre class="ledger-block">{esc(b)}</pre>' for b in clean_blocks)
)
oq_html = (
    '<p class="muted">None open.</p>'
    if not oq_items
    else "<ol>\n" + "\n".join(f"<li>{esc(i)}</li>" for i in oq_items) + "\n</ol>"
)
brief_html = (
    "\n".join(f"<p>{md_inline(ln)}</p>" for ln in brief_lines)
    if brief_lines
    else "<p>No living claims.</p>"
)

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Learning graph — living claims</title>
<style>
  :root {{
    --bg: #f7f5f0; --ink: #1a1a1a; --muted: #5c5c5c;
    --alive: #1b5e3b; --weakened: #8a5a00; --killed: #8b1e1e;
    --rule: #d9d4c8; --card: #fffef9;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
    font-size: 1.125rem; line-height: 1.55; color: var(--ink); background: var(--bg);
  }}
  main {{ max-width: 42rem; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }}
  header h1 {{ font-size: 1.75rem; font-weight: 600; letter-spacing: -0.02em; margin: 0 0 0.35rem; }}
  .sub {{ color: var(--muted); font-size: 0.95rem; margin: 0 0 2rem; }}
  h2 {{
    font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted);
    border-top: 1px solid var(--rule); padding-top: 1.5rem; margin: 2.25rem 0 0.85rem;
    font-weight: 600; font-family: ui-sans-serif, system-ui, sans-serif;
  }}
  .claim {{ background: var(--card); border: 1px solid var(--rule); border-radius: 6px; padding: 1.25rem 1.35rem; }}
  .claim-id {{ font-family: ui-sans-serif, system-ui, sans-serif; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; }}
  .status {{ font-family: ui-sans-serif, system-ui, sans-serif; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; }}
  .status.alive {{ color: var(--alive); }}
  .status.weakened {{ color: var(--weakened); }}
  .status.killed {{ color: var(--killed); text-decoration: line-through; }}
  .claim p {{ margin: 0.6rem 0 0; }}
  .meta {{ margin-top: 1rem; font-size: 0.92rem; color: var(--muted); }}
  .meta dt {{ font-family: ui-sans-serif, system-ui, sans-serif; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.65rem; }}
  .meta dd {{ margin: 0.15rem 0 0; }}
  .muted {{ color: var(--muted); font-style: italic; }}
  pre.ledger-block {{
    white-space: pre-wrap; font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.82rem; line-height: 1.45; background: var(--card); border: 1px solid var(--rule);
    border-radius: 6px; padding: 1rem 1.1rem; margin: 0 0 0.75rem;
  }}
  footer {{
    margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--rule);
    font-size: 0.85rem; color: var(--muted); font-family: ui-sans-serif, system-ui, sans-serif;
  }}
</style>
</head>
<body>
<main>
  <header>
    <h1>Learning graph</h1>
    <p class="sub">Living claims only. Confidence is the trial record — survived, weakened, or killed.</p>
  </header>
  <h2>Brief</h2>
  {brief_html}
  <h2>Claim C0 · {esc(slug)}</h2>
  <article class="claim">
    <div class="claim-id">C0 · <span class="status {status_class}">{esc(status)}</span></div>
    <p>{esc(claim_text)}</p>
    <dl class="meta">
      <dt>Last change</dt><dd>{esc(last)}</dd>
      <dt>Bounds</dt><dd>{esc(bounds) if bounds else "—"}</dd>
      <dt>What would kill this</dt><dd>{esc(kill)}</dd>
      <dt>Tutor consequence</dt><dd>{esc(tutor)}</dd>
    </dl>
  </article>
  <h2>Ledger · C0</h2>
  {ledger_html}
  <h2>Open questions</h2>
  {oq_html}
  <footer>
    Compiled {date.today().isoformat()} from the living graph. Not a catalogue.
  </footer>
</main>
</body>
</html>
'''
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(clean_blocks)} ledger blocks)")
