#!/usr/bin/env python3
"""RRE Evidence Sufficiency — adapter / runner for the released v2 build.

The released judge (evidence_judge.py, stage2-ext-2026-10-23-r3-rule-a-b) is
deterministic and takes extraction records. Extraction is the only model step
and is frozen-prompt bound. This adapter makes the pipeline one command:

  extract-packet  Build the stateless extraction packet (frozen prompt +
                  dossiers) for the manual extractor chat — the recorded
                  adapter identity (manual-chat-output/1.0).
  extract-api     Extract via any OpenAI-compatible chat endpoint
                  (env: RRE_API_KEY, RRE_API_BASE, RRE_API_MODEL).
  decide          Apply the authorized two-rule proposal to the released
                  judge and decide extraction records, printing the frozen
                  response schema (ANSWER: ... / ABSTAIN: ...) plus traces.

The judge code is never modified by this adapter. Stdlib only.
"""
import argparse, hashlib, json, os, sys, tempfile, urllib.request
from pathlib import Path

BUILD = Path(__file__).resolve().parent  # set --build to the released build dir
RULES = {"GENERAL_RULE_WITH_SCOPED_EXCEPTION": {"enabled": True},
         "ASSERTED_FACT_IN_HISTORICAL_SOURCE": {"enabled": True}}
PROPOSAL = {"version": "sufficiency/1.1+extension/1.0", "rules": RULES,
            "base_policy": "sufficiency/1.0",
            "candidate_revision": "stage2-ext-2026-10-23-r3-rule-a-b"}


def load_build(build_dir):
    sys.path.insert(0, str(build_dir))
    import evidence_judge, rre_minimal  # noqa
    return evidence_judge, rre_minimal


def mk_record(ej, raw):
    cs = tuple(ej.CandidateAssertion(
        c["source_span"], c["entity"], c["attribute"], c["value"], c["scope"],
        c["assertion_type"], c["relation"], c.get("source_start"), c.get("source_end"))
        for c in raw["candidates"])
    return ej.EvidenceRecord(raw["schema_version"], raw["question"], raw["dossier_sha256"], cs)


def cmd_decide(args):
    ej, rre = load_build(Path(args.build))
    records = json.loads(Path(args.records).read_text())
    targets = {}
    if args.targets:
        targets = {int(k): tuple(v) for k, v in json.loads(Path(args.targets).read_text()).items()}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        ext = ej.VersionedPolicyExtension(rre.RRE(td / "audit.jsonl"), td / "policy.json")
        proposal = ext.propose(PROPOSAL, "Stage 2 authorized two-rule extension",
                               "owner authorization Tarnue Kamara Tyler, 2026-10-21")
        if not ext.apply(proposal, "Tarnue Kamara Tyler"):
            print("ERROR: proposal not applied", file=sys.stderr); return 1
        traces = []
        for n, raw in enumerate(records, 1):
            ent, attr = targets.get(n, (raw["candidates"][0]["entity"], raw["candidates"][0]["attribute"]))
            d = ext.decide(mk_record(ej, raw), ent, attr)
            line = f"ANSWER: {d.answer}" if d.status == "ANSWER" else f"ABSTAIN: {d.reason}"
            print(line)
            traces.append({"item": n, "status": d.status, "answer": d.answer, "reason": d.reason,
                           "policy_version": d.policy_version, "evidence_indices": list(d.evidence_indices),
                           "response": line})
    if args.traces_out:
        Path(args.traces_out).write_text(json.dumps(traces, indent=1) + "\n")
    return 0


def cmd_extract_packet(args):
    prompt = Path(args.build, "FROZEN_EXTRACTION_PROMPT.txt").read_text()
    dossiers = json.loads(Path(args.dossiers).read_text())
    out = [prompt.rstrip(), ""]
    for d in dossiers:
        out.append(f"=== DOSSIER item {d['item']} ===")
        out.append(f"QUESTION: {d['question']}")
        out.append(d["content"])
        out.append("")
    Path(args.out).write_text("\n".join(out))
    print(f"packet written: {args.out} ({len(dossiers)} dossiers, frozen prompt sha256 "
          f"{hashlib.sha256(prompt.encode()).hexdigest()[:8]}…)")
    return 0


def cmd_extract_api(args):
    key = os.environ.get("RRE_API_KEY")
    if not key:
        print("ERROR: RRE_API_KEY not set. Use extract-packet for the manual adapter, "
              "or set RRE_API_KEY / RRE_API_BASE / RRE_API_MODEL.", file=sys.stderr)
        return 1
    base = os.environ.get("RRE_API_BASE", "https://api.openai.com/v1")
    model = os.environ.get("RRE_API_MODEL", "")
    prompt = Path(args.build, "FROZEN_EXTRACTION_PROMPT.txt").read_text()
    dossiers = json.loads(Path(args.dossiers).read_text())
    records = []
    for d in dossiers:
        body = json.dumps({"model": model, "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"QUESTION: {d['question']}\n\n{d['content']}"}]}).encode()
        req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body,
                                     headers={"Authorization": f"Bearer {key}",
                                              "Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            text = json.loads(resp.read())["choices"][0]["message"]["content"]
        rec = json.loads(text)
        rec["dossier_sha256"] = hashlib.sha256(d["content"].encode("utf-8")).hexdigest()
        rec["question"] = d["question"]
        records.append(rec)
        print(f"item {d['item']}: {len(rec['candidates'])} candidates")
    Path(args.out).write_text(json.dumps(records, indent=1) + "\n")
    print(f"records written: {args.out}")
    return 0


def main():
    p = argparse.ArgumentParser(description="RRE released-build adapter")
    p.add_argument("--build", default=str(Path(__file__).resolve().parent),
                   help="directory containing the released build (evidence_judge.py etc.)")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("decide"); d.add_argument("--records", required=True)
    d.add_argument("--targets"); d.add_argument("--traces-out"); d.set_defaults(fn=cmd_decide)
    e = sub.add_parser("extract-packet"); e.add_argument("--dossiers", required=True)
    e.add_argument("--out", required=True); e.set_defaults(fn=cmd_extract_packet)
    a = sub.add_parser("extract-api"); a.add_argument("--dossiers", required=True)
    a.add_argument("--out", required=True); a.set_defaults(fn=cmd_extract_api)
    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
