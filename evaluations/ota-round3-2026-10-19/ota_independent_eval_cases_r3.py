"""Independent black-box test cases for the Recursive Revision Engine (RRE)
correction mechanism - ROUND THREE (fresh seal).

Evaluator : OTA Reacts, independent evaluator. I authored neither the
            implementation nor any of its existing tests.
Target    : https://github.com/Founder5222196/recursive-revision-engine
            NEW fixed commit fd08777 (verified by direct raw fetch).
Claim     : rre_recovery/rre_persistent.py now verifies candidates in
            isolation - candidate rules are never installed in the live
            object - so no rejected candidate, empty or otherwise, can mutate
            live rules, version, or identity at any point; snapshot()
            deep-copies nested state. This file tests that claim; it does
            not assume it.
Defect    : Found in round two (case C6/D1): a rejected empty candidate
            emptied the live object's in-memory rules ({}); durable state was
            never touched, and D1 caught the divergence.
Method    : Black-box, public interfaces only.
            Used from rre_minimal.py: RRE(), act(), identify(),
            accept_correction(), acknowledge(), propose(), apply(),
            verify_audit().
            Used from rre_recovery/rre_persistent.py: PersistentRRE(), act(),
            commit_candidate(), snapshot(), verify_chain().
            Outcomes are judged only from public return values, public
            snapshot() equality comparisons, and the engine's own audit and
            state files on disk. This harness never reads .rules directly,
            never calls RRE.verify() to judge behavior, and never imports
            engine internals.
IMPORT    : Pin from round two, kept: modules are loaded by explicit absolute
            path via importlib - sys.path is never modified - and
            rre_minimal.__file__ is recorded as cases R1/R2 and in the JSON
            report so the binding is on the record.
Run       : Place this file at the repository root, next to rre_minimal.py,
            then run:  python3 ota_independent_eval_cases_r3.py
            Exit code 0 iff every case passes. A JSON report is written to
            ota_independent_eval_report_r3.json.
Provenance: This case file was authored and sealed (SHA-256 published in the
            repository) before any execution against the target commit. No
            case changes after the seal.

Case groups
-----------
R  Import binding on the record (R1/R2).
A  Base engine (root rre_minimal.py), fresh path: the correction must change
   behavior through the public loop (acknowledge != revise; authority
   enforced; after the authorized correction: missing evidence reports
   uncertainty, answerable cases still answer; stale proposals rejected;
   audit chain valid).
B  Persistent layer (rre_persistent.py): a good correction candidate is
   retained and behavior is correct on both missing-evidence and answerable
   inputs.
C  Faulty proposed revisions must be rejected and rolled back, including one
   relabeled as good and carrying acknowledged/accepted labels, one that
   reverts to guessing, and one malformed (empty) candidate. C8 is the
   DIRECT PROBE OF THE ROUND-TWO DEFECT: after the rejected empty candidate,
   WITHOUT any restart, the live object's snapshot AND its behavior on both
   missing and answerable inputs must be unchanged. C9 probes snapshot()
   deep-copy isolation.
D  Restart behavior, persistent layer (D1-D5, with D1 exactly as formulated
   in round two) and base engine (D6-D11, the round-two D6/D7 deciders kept
   as regression, plus the round-two probes D8-D11).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
# Deliberately no sys.path manipulation. Both modules are loaded by explicit
# absolute path so `import rre_minimal` can never resolve to a stale copy.


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rre_minimal = _load_module("rre_minimal_under_test", ROOT / "rre_minimal.py")
rre_persistent = _load_module(
    "rre_persistent_under_test", ROOT / "rre_recovery" / "rre_persistent.py")

RRE = rre_minimal.RRE
verify_audit = rre_minimal.verify_audit
PersistentRRE = rre_persistent.PersistentRRE
verify_chain = rre_persistent.verify_chain

APPROVER = "ota-independent-evaluator-r3"
RESULTS: list[dict] = []

MISSING_INPUTS = [
    "no source was produced for this item",
    "the requested record exists but the relevant page is absent",
    "the only witness has no recollection and no documents exist",
    "the dataset field for this question is null in every copy",
]

ANSWERABLE_INPUTS = [
    "a notarized transcript states the shipment total was 742 units",
    "two independent ledgers agree the answer is twelve",
    "the cited regulation, on file, fixes the deadline at 30 days",
    "a signed lab report in the dossier gives the yield as 61.2 percent",
]


def run_case(case_id: str, description: str, fn) -> None:
    expected = actual = ""
    passed = False
    try:
        expected, actual, passed = fn()
    except Exception:
        actual = "EXCEPTION (counts as FAIL): " + traceback.format_exc(limit=4)
        expected = "case completes without exception"
        passed = False
    RESULTS.append({"case_id": case_id, "description": description,
                    "expected": expected, "actual": actual, "passed": passed})
    print(f"[{'PASS' if passed else 'FAIL'}] {case_id} {description}")
    print(f"        expected: {expected}")
    print(f"        actual:   {actual}")


def main() -> int:
    print("=" * 78)
    print("Independent black-box evaluation, round three: RRE correction mechanism")
    print("Target: Founder5222196/recursive-revision-engine @ fd08777")
    print("=" * 78)

    # -------------------------------------------------------------
    # Group R - import binding on the record
    # -------------------------------------------------------------
    def r1():
        f = str(Path(rre_minimal.__file__).resolve())
        want = str((ROOT / "rre_minimal.py").resolve())
        return ("repository ROOT rre_minimal.py", f, f == want)
    run_case("R1", "Module binding: rre_minimal resolves to the repository ROOT "
             "copy (not rre_recovery/)", r1)

    def r2():
        f = str(Path(rre_persistent.__file__).resolve())
        want = str((ROOT / "rre_recovery" / "rre_persistent.py").resolve())
        return ("rre_recovery/rre_persistent.py", f, f == want)
    run_case("R2", "Module binding: rre_persistent resolves to rre_recovery/", r2)

    with TemporaryDirectory() as td:
        tmp = Path(td)

        # -------------------------------------------------------------
        # Group A - base engine (root rre_minimal.py), fresh path
        # -------------------------------------------------------------
        audit_a = tmp / "groupA_audit.jsonl"
        r = RRE(audit_a)
        S: dict = {}

        def a1():
            got = r.act(True, "no source was produced for this item")
            S["baseline"] = got
            return "guess (the documented faulty rule)", repr(got), got == "guess"
        run_case("A1", "Baseline: fresh agent guesses on missing evidence", a1)

        r.identify("report_unknown", S["baseline"],
                   "controlled input explicitly has no supporting evidence")
        r.accept_correction(
            "When evidence is missing, report uncertainty instead of guessing.",
            APPROVER,
            "baseline action was 'guess' on a missing-evidence input")
        r.acknowledge("Understood; I will report uncertainty.")
        r.acknowledge("Correction accepted; I will do better.")

        def a2():
            got = r.act(True, "still no supporting record after acknowledgments")
            ok = got == "guess"
            return ("guess (acknowledgment alone must not change behavior)",
                    repr(got), ok)
        run_case("A2", "Two acknowledgments do not change behavior", a2)

        S["proposal"] = r.propose()

        def a3():
            denied = r.apply(S["proposal"])
            got = r.act(True, "probe after unauthorized apply attempt")
            ok = denied is False and got == "guess"
            return ("apply returns False; behavior stays 'guess'",
                    f"apply={denied}, act={got!r}", ok)
        run_case("A3", "Apply without named approval is rejected; behavior unchanged",
                 a3)

        def a4():
            applied = r.apply(S["proposal"], approved_by=APPROVER)
            return "True", repr(applied), applied is True
        run_case("A4", "Authorized apply of the correction succeeds", a4)

        for i, text in enumerate(MISSING_INPUTS, 1):
            def a_missing(text=text):
                got = r.act(True, text)
                return "report_unknown", repr(got), got == "report_unknown"
            run_case(f"A{4 + i}",
                     f"Missing-evidence case {i}/4: must report uncertainty",
                     a_missing)

        def a9():
            got = r.act(True, "a notarized transcript states the total is 742 units")
            return ("report_unknown (per the public interface contract the "
                    "evidence_missing flag governs the action)",
                    repr(got), got == "report_unknown")
        run_case("A9",
                 "Rich-looking text is still treated as missing when the flag "
                 "says so", a9)

        for i, text in enumerate(ANSWERABLE_INPUTS, 1):
            def a_answerable(text=text):
                got = r.act(False, text)
                return ("answer_from_evidence", repr(got),
                        got == "answer_from_evidence")
            run_case(f"A{9 + i}",
                     f"Answerable case {i}/4: must still answer from evidence",
                     a_answerable)

        def a14():
            denied = r.apply(S["proposal"], approved_by=APPROVER)
            got = r.act(True, "probe after stale proposal resubmission")
            ok = denied is False and got == "report_unknown"
            return ("stale apply returns False; behavior stays 'report_unknown'",
                    f"apply={denied}, act={got!r}", ok)
        run_case("A14", "Stale proposal resubmission is rejected; behavior unchanged",
                 a14)

        def a15():
            ok, msg = verify_audit(audit_a)
            return "(True, 'verified N events')", f"({ok}, {msg!r})", ok is True
        run_case("A15", "Base-engine audit hash chain verifies after Group A", a15)

        # -------------------------------------------------------------
        # Group B - persistent layer: good correction retained
        # -------------------------------------------------------------
        state_p = tmp / "persist" / "state.json"
        audit_p = tmp / "persist" / "audit.jsonl"
        p = PersistentRRE(state_p, audit_p)
        T: dict = {}

        def b1():
            got = p.act(True)
            return "guess (documented baseline)", repr(got), got == "guess"
        run_case("B1", "Baseline: fresh persistent agent guesses on missing "
                 "evidence", b1)

        def b2():
            ok = p.commit_candidate({"missing_evidence": "report_unknown"},
                                    "ota-good-correction")
            return "True (candidate retained)", repr(ok), ok is True
        run_case("B2", "Good correction candidate passes verification and is "
                 "retained", b2)

        for i in range(1, 5):
            def b_missing():
                got = p.act(True)
                return "report_unknown", repr(got), got == "report_unknown"
            run_case(f"B{2 + i}",
                     f"Missing-evidence case {i}/4 after correction", b_missing)

        for i in range(1, 5):
            def b_answerable():
                got = p.act(False)
                return ("answer_from_evidence", repr(got),
                        got == "answer_from_evidence")
            run_case(f"B{6 + i}",
                     f"Answerable case {i}/4 after correction", b_answerable)

        # -------------------------------------------------------------
        # Group C - faulty revisions must be rejected and rolled back
        # -------------------------------------------------------------
        T["before_faulty"] = p.snapshot()

        def c1():
            ok = p.commit_candidate({"missing_evidence": "always_refuse"},
                                    "relabeled-as-good",
                                    acknowledged=True, accepted=True)
            return ("False (behavioral verification must reject it regardless "
                    "of labels)", repr(ok), ok is False)
        run_case("C1", "Faulty always-refuse candidate rejected despite "
                 "acknowledged/accepted labels", c1)

        def c2():
            now = p.snapshot()
            same = now == T["before_faulty"]
            return ("snapshot identical to pre-candidate snapshot",
                    f"identical={same}", same)
        run_case("C2", "Rollback restores the exact pre-candidate snapshot", c2)

        def c3():
            got = p.act(True)
            return ("report_unknown (prior corrected state, not reverted to "
                    "guess)", repr(got), got == "report_unknown")
        run_case("C3", "After rollback: missing evidence still reports "
                 "uncertainty", c3)

        def c4():
            got = p.act(False)
            return "answer_from_evidence", repr(got), got == "answer_from_evidence"
        run_case("C4", "After rollback: answerable case still answers", c4)

        def c5():
            before = p.snapshot()
            ok = p.commit_candidate({"missing_evidence": "guess"},
                                    "revert-to-guessing")
            unchanged = p.snapshot() == before
            return ("False and snapshot unchanged",
                    f"commit={ok}, unchanged={unchanged}",
                    ok is False and unchanged)
        run_case("C5", "Faulty revert-to-guess candidate rejected and rolled "
                 "back", c5)

        # --- the original round-two defect: the rejected empty candidate ---
        T["pre_empty"] = p.snapshot()
        T["pre_empty_state"] = state_p.read_bytes()

        def c6():
            before = p.snapshot()
            state_before = state_p.read_bytes()
            try:
                ok = p.commit_candidate({}, "empty-candidate")
                outcome = f"returned {ok}"
                rejected = ok is False
            except Exception as exc:
                outcome = f"raised {type(exc).__name__}: {exc}"
                rejected = True
            state_unchanged = state_p.read_bytes() == state_before
            ok_chain, chain_msg = verify_chain(audit_p)
            mem = p.snapshot()
            detail = (f"{outcome}; durable state unchanged={state_unchanged}; "
                      f"chain=({ok_chain}, {chain_msg!r}); in-memory snapshot "
                      f"equals pre-candidate snapshot={mem == before}")
            return ("rejected (False or exception), durable state unchanged, "
                    "audit chain valid", detail,
                    rejected and state_unchanged and ok_chain)
        run_case("C6", "Malformed empty candidate cannot take effect; durable "
                 "state intact", c6)

        # --- DIRECT PROBE OF THE ROUND-TWO DEFECT, no restart ---
        def c8():
            snap_ok = p.snapshot() == T["pre_empty"]
            try:
                missing = p.act(True)
                answerable = p.act(False)
                behavior = f"act(True)={missing!r}, act(False)={answerable!r}"
                behavior_ok = (missing == "report_unknown"
                               and answerable == "answer_from_evidence")
            except Exception as exc:
                behavior = f"act raised {type(exc).__name__}: {exc}"
                behavior_ok = False
            state_ok = state_p.read_bytes() == T["pre_empty_state"]
            detail = (f"snapshot_unchanged={snap_ok}; behavior: {behavior}; "
                      f"durable_state_unchanged={state_ok}")
            return ("WITHOUT any restart: live snapshot equals the "
                    "pre-candidate snapshot; act(True)='report_unknown' and "
                    "act(False)='answer_from_evidence'; durable state "
                    "unchanged", detail,
                    snap_ok and behavior_ok and state_ok)
        run_case("C8", "ROUND-TWO DEFECT PROBE: immediately after the rejected "
                 "empty candidate, with NO restart, the live object's snapshot "
                 "AND behavior on missing and answerable inputs are unchanged",
                 c8)

        def c9():
            snap = p.snapshot()
            nested = snap.get("rules")
            nested_is_dict = isinstance(nested, dict)
            if nested_is_dict:
                nested["missing_evidence"] = "tampered-evaluator-mutation"
                nested["injected"] = "x"
            snap["version"] = 999
            snap["version_id"] = "v999-tampered"
            after = p.snapshot()
            try:
                got = p.act(True)
                behavior = f"act(True)={got!r}"
                behavior_ok = got == "report_unknown"
            except Exception as exc:
                behavior = f"act raised {type(exc).__name__}: {exc}"
                behavior_ok = False
            detail = (f"snapshot_had_nested_rules={nested_is_dict}; "
                      f"post_mutation_snapshot={json.dumps(after, sort_keys=True)}; "
                      f"{behavior}")
            return ("mutating a returned snapshot (nested rule assignment, "
                    "key injection, version/version_id rewrite) does not "
                    "affect the live object; behavior still report_unknown",
                    detail,
                    nested_is_dict and after == T["pre_empty"] and behavior_ok)
        run_case("C9", "snapshot() deep-copies nested state: mutating the "
                 "returned snapshot cannot corrupt the live object", c9)

        def c7():
            ok, msg = verify_chain(audit_p)
            return "(True, ...)", f"({ok}, {msg!r})", ok is True
        run_case("C7", "Persistent audit chain verifies after faulty-candidate "
                 "group", c7)

        # -------------------------------------------------------------
        # Group D - restart behavior
        # D1-D5: persistent layer; D1 is a deciding case this round and is
        # kept EXACTLY as formulated in round two.
        # D6-D11: BASE engine - the round-two deciders kept as regression.
        # -------------------------------------------------------------
        T["audit_bytes_before_restart"] = audit_p.read_bytes()
        q = PersistentRRE(state_p, audit_p)  # re-initialization / restart

        def d1():
            snap = q.snapshot()
            same = snap == T["before_faulty"] and snap == p.snapshot()
            return ("snapshot equals the pre-restart durable snapshot",
                    f"equal={same}", same)
        run_case("D1", "Re-initialization restores persistent state (state "
                 "survives restart)", d1)

        def d2():
            after = audit_p.read_bytes()
            before = T["audit_bytes_before_restart"]
            ok, msg = verify_chain(audit_p)
            prefix = after.startswith(before)
            grew = len(after.splitlines()) > len(before.splitlines())
            stages = [json.loads(x)["stage"] for x in after.splitlines()]
            has_restart = "RESTART_RESTORED" in stages
            detail = (f"byte_prefix_preserved={prefix}, event_count_grew={grew}, "
                      f"RESTART_RESTORED_recorded={has_restart}, "
                      f"chain=({ok}, {msg!r})")
            return ("history preserved (byte prefix), events appended, "
                    "chain valid", detail, prefix and grew and has_restart and ok)
        run_case("D2", "Persistent audit history survives re-initialization "
                 "(append-only, chain valid)", d2)

        def d3():
            got = q.act(True)
            return "report_unknown", repr(got), got == "report_unknown"
        run_case("D3", "After restart (persistent layer): missing evidence "
                 "reports uncertainty", d3)

        def d4():
            got = q.act(False)
            return "answer_from_evidence", repr(got), got == "answer_from_evidence"
        run_case("D4", "After restart (persistent layer): answerable case "
                 "still answers", d4)

        T["audit_bytes_before_restart2"] = audit_p.read_bytes()
        T["snap_q"] = q.snapshot()
        q2 = PersistentRRE(state_p, audit_p)  # second restart

        def d5():
            after = audit_p.read_bytes()
            before = T["audit_bytes_before_restart2"]
            ok, msg = verify_chain(audit_p)
            prefix = after.startswith(before)
            grew = len(after.splitlines()) > len(before.splitlines())
            same_state = q2.snapshot() == T["snap_q"]
            detail = (f"byte_prefix_preserved={prefix}, event_count_grew={grew}, "
                      f"state_stable_across_restart={same_state}, "
                      f"chain=({ok}, {msg!r})")
            return ("append-only across second restart; chain valid; state "
                    "stable", detail, prefix and grew and ok and same_state)
        run_case("D5", "Second re-initialization (persistent layer): audit "
                 "still append-only, chain valid", d5)

        # ----- BASE engine probes (round-two regression scope) -----

        audit_b = tmp / "groupD_base_audit.jsonl"
        rb = RRE(audit_b)
        rb.apply(rb.propose(), approved_by=APPROVER)
        rb.act(True, "pre-restart missing probe")
        rb.act(False, "pre-restart answerable probe")
        T["base_bytes_before"] = audit_b.read_bytes()
        T["base_lines_before"] = len(
            audit_b.read_text(encoding="utf-8").splitlines())

        rb2 = RRE(audit_b)  # base-engine re-initialization

        def d6():
            after = audit_b.read_bytes()
            before = T["base_bytes_before"]
            lines_after = len(
                audit_b.read_text(encoding="utf-8").splitlines())
            ok, msg = verify_audit(audit_b)
            prefix = after.startswith(before)
            grew = lines_after > T["base_lines_before"]
            detail = (f"byte_prefix_preserved={prefix}, "
                      f"events_before={T['base_lines_before']}, "
                      f"events_after={lines_after}, chain=({ok}, {msg!r})")
            return ("prior audit bytes survive re-initialization (byte prefix), "
                    "events appended, chain valid", detail,
                    prefix and grew and ok)
        run_case("D6", "BASE ENGINE: audit history survives re-initialization",
                 d6)

        def d7():
            got = rb2.act(True, "post-restart missing probe")
            return ("report_unknown (corrected state survives restart)",
                    repr(got), got == "report_unknown")
        run_case("D7", "BASE ENGINE: corrected behavior survives "
                 "re-initialization", d7)

        def d8():
            got = rb2.act(False, "post-restart answerable probe")
            return ("answer_from_evidence", repr(got),
                    got == "answer_from_evidence")
        run_case("D8", "BASE ENGINE: answerable behavior survives "
                 "re-initialization", d8)

        T["base_bytes_before_r3"] = audit_b.read_bytes()
        rb3 = RRE(audit_b)  # second base-engine restart

        def d9():
            after = audit_b.read_bytes()
            before = T["base_bytes_before_r3"]
            ok, msg = verify_audit(audit_b)
            prefix = after.startswith(before)
            got = rb3.act(True, "second-restart missing probe")
            detail = (f"byte_prefix_preserved={prefix}, "
                      f"act={got!r}, chain=({ok}, {msg!r})")
            return ("append-only across second restart; still report_unknown; "
                    "chain valid", detail,
                    prefix and ok and got == "report_unknown")
        run_case("D9", "BASE ENGINE: second re-initialization is append-only; "
                 "corrected behavior persists", d9)

        # Probe of the c218b5f rebuild path: sidecar deleted, audit only.
        audit_c = tmp / "rebuild_audit.jsonl"
        rc = RRE(audit_c)
        rc.apply(rc.propose(), approved_by=APPROVER)
        rc.act(True, "pre-rebuild probe")
        T["rebuild_bytes_before"] = audit_c.read_bytes()
        sidecar = Path(str(audit_c) + ".state.json")
        sidecar.unlink()  # simulate a copied/moved audit file with no sidecar

        rc2 = RRE(audit_c)

        def d10():
            got = rc2.act(True, "post-rebuild missing probe")
            ok, msg = verify_audit(audit_c)
            prefix = audit_c.read_bytes().startswith(T["rebuild_bytes_before"])
            sidecar_back = sidecar.exists()
            detail = (f"act={got!r}, byte_prefix_preserved={prefix}, "
                      f"chain=({ok}, {msg!r}), sidecar_recreated={sidecar_back}")
            return ("state reconstructed from audit alone: report_unknown; "
                    "history preserved; chain valid",
                    detail, got == "report_unknown" and prefix and ok)
        run_case("D10", "BASE ENGINE: without the sidecar, state is rebuilt "
                 "from the audit history and behavior is still corrected",
                 d10)

        # Probe of the c218b5f validation path: a corrupted audit must not be
        # silently truncated, resumed, or rewritten.
        audit_d = tmp / "corrupt_audit.jsonl"
        rd = RRE(audit_d)
        rd.apply(rd.propose(), approved_by=APPROVER)
        rd.act(True, "pre-corruption probe")
        lines = audit_d.read_text(encoding="utf-8").splitlines()
        evt = json.loads(lines[2])
        evt["payload"]["evidence"] = "tampered after the fact"
        lines[2] = json.dumps(evt, sort_keys=True, separators=(",", ":"))
        corrupt_text = "\n".join(lines) + "\n"
        audit_d.write_text(corrupt_text, encoding="utf-8")
        T["corrupt_bytes"] = audit_d.read_bytes()

        def d11():
            outcome = "constructed without error"
            refused = False
            try:
                RRE(audit_d)
            except Exception as exc:
                outcome = f"raised {type(exc).__name__}: {exc}"
                refused = True
            unchanged = audit_d.read_bytes() == T["corrupt_bytes"]
            ok, msg = verify_audit(audit_d)
            detail = (f"constructor {outcome}; corrupt_bytes_unchanged="
                      f"{unchanged}; chain check on tampered log="
                      f"({ok}, {msg!r})")
            return ("constructor refuses to resume (raises); tampered audit "
                    "left byte-identical; chain check fails",
                    detail, refused and unchanged and ok is False)
        run_case("D11", "BASE ENGINE: re-initialization on a corrupted audit "
                 "refuses and preserves the evidence untouched", d11)

    total = len(RESULTS)
    failed_ids = [row["case_id"] for row in RESULTS if not row["passed"]]
    print("=" * 78)
    print(f"TOTAL: {total}  PASSED: {total - len(failed_ids)}  "
          f"FAILED: {len(failed_ids)}")
    if failed_ids:
        print("FAILED CASES: " + ", ".join(failed_ids))

    report = {
        "evaluator": "ota-independent-evaluator-round3",
        "target": ("Founder5222196/recursive-revision-engine @ fd08777 "
                   "(round-three fixed commit, verified by direct raw fetch)"),
        "method": "black-box, public interfaces only",
        "round_three_defect": ("round-two case C6: rejected empty candidate "
                               "emptied the live PersistentRRE in-memory "
                               "rules; durable state untouched; D1 caught "
                               "the divergence"),
        "import_binding": {
            "rre_minimal_file": str(Path(rre_minimal.__file__).resolve()),
            "rre_persistent_file": str(Path(rre_persistent.__file__).resolve()),
        },
        "total": total,
        "passed": total - len(failed_ids),
        "failed": len(failed_ids),
        "failed_case_ids": failed_ids,
        "cases": RESULTS,
    }
    report["import_binding"]["rre_minimal_is_root"] = (
        report["import_binding"]["rre_minimal_file"]
        == str((ROOT / "rre_minimal.py").resolve()))
    report_path = Path("ota_independent_eval_report_r3.json").resolve()
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"rre_minimal.__file__ = {report['import_binding']['rre_minimal_file']}")
    print(f"rre_persistent.__file__ = "
          f"{report['import_binding']['rre_persistent_file']}")
    print(f"Report: {report_path}")
    return 0 if not failed_ids else 1


if __name__ == "__main__":
    raise SystemExit(main())
