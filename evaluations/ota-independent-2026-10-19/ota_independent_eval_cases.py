"""Independent black-box test cases for the Recursive Revision Engine (RRE)
correction mechanism.

Evaluator : OTA Reacts, independent evaluator. I authored neither the
            implementation nor any of its existing tests.
Target    : https://github.com/Founder5222196/recursive-revision-engine
            fixed commit 862fa5a (862fa5a9714709980ee269b624a6308360de2ae2)
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
Run       : Place this file at the repository root, next to rre_minimal.py,
            then run:  python3 ota_independent_eval_cases.py
            Exit code 0 iff every case passes. A JSON report is written to
            ota_independent_eval_report.json.
Provenance: This case file was authored and sealed (SHA-256 published in the
            repository) before any execution against the target commit.

Case groups
-----------
A  Base engine (rre_minimal.py): the correction must change behavior through
   the public loop (acknowledge != revise; authority enforced; after the
   authorized correction: missing evidence reports uncertainty, answerable
   cases still answer; stale proposals rejected; audit chain valid).
B  Persistent layer (rre_persistent.py): a good correction candidate is
   retained and behavior is correct on both missing-evidence and answerable
   inputs.
C  Faulty proposed revisions must be rejected and rolled back, including one
   relabeled as good and carrying acknowledged/accepted labels, one that
   reverts to guessing, and one malformed candidate.
D  Restart behavior: state and audit history must survive re-initialization
   (persistent layer), plus two gap probes on the base engine, whose README
   states that audit-history reset and rule-state restore are not implemented
   there.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
for _p in (str(ROOT), str(ROOT / "rre_recovery")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

APPROVER = "ota-independent-evaluator"
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
    from rre_minimal import RRE, verify_audit
    from rre_persistent import PersistentRRE, verify_chain

    print("=" * 78)
    print("Independent black-box evaluation: RRE correction mechanism")
    print("Target: Founder5222196/recursive-revision-engine @ 862fa5a")
    print("=" * 78)

    with TemporaryDirectory() as td:
        tmp = Path(td)

        # -------------------------------------------------------------
        # Group A - base engine (rre_minimal.py)
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
        run_case("A3", "Apply without named approval is rejected; behavior unchanged", a3)

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
                 "Rich-looking text is still treated as missing when the flag says so",
                 a9)

        for i, text in enumerate(ANSWERABLE_INPUTS, 1):
            def a_answerable(text=text):
                got = r.act(False, text)
                return "answer_from_evidence", repr(got), got == "answer_from_evidence"
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
        run_case("B1", "Baseline: fresh persistent agent guesses on missing evidence",
                 b1)

        def b2():
            ok = p.commit_candidate({"missing_evidence": "report_unknown"},
                                    "ota-good-correction")
            return "True (candidate retained)", repr(ok), ok is True
        run_case("B2", "Good correction candidate passes verification and is retained",
                 b2)

        for i in range(1, 5):
            def b_missing():
                got = p.act(True)
                return "report_unknown", repr(got), got == "report_unknown"
            run_case(f"B{2 + i}",
                     f"Missing-evidence case {i}/4 after correction",
                     b_missing)

        for i in range(1, 5):
            def b_answerable():
                got = p.act(False)
                return "answer_from_evidence", repr(got), got == "answer_from_evidence"
            run_case(f"B{6 + i}",
                     f"Answerable case {i}/4 after correction",
                     b_answerable)

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
        run_case("C1",
                 "Faulty always-refuse candidate rejected despite "
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
        run_case("C3", "After rollback: missing evidence still reports uncertainty",
                 c3)

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
        run_case("C5", "Faulty revert-to-guess candidate rejected and rolled back",
                 c5)

        T["good_snap"] = p.snapshot()

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
        run_case("C6", "Malformed empty candidate cannot take effect; durable state "
                 "intact", c6)

        def c7():
            ok, msg = verify_chain(audit_p)
            return "(True, ...)", f"({ok}, {msg!r})", ok is True
        run_case("C7", "Persistent audit chain verifies after faulty-candidate group",
                 c7)

        # -------------------------------------------------------------
        # Group D - restart behavior
        # -------------------------------------------------------------
        T["audit_bytes_before_restart"] = audit_p.read_bytes()
        q = PersistentRRE(state_p, audit_p)  # re-initialization / restart

        def d1():
            snap = q.snapshot()
            same = snap == T["good_snap"]
            return ("snapshot equals the pre-restart durable snapshot",
                    f"equal={same}", same)
        run_case("D1", "Re-initialization restores state (state survives restart)",
                 d1)

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
        run_case("D2", "Audit history survives re-initialization (append-only, "
                 "chain valid)", d2)

        def d3():
            got = q.act(True)
            return "report_unknown", repr(got), got == "report_unknown"
        run_case("D3", "After restart: missing evidence reports uncertainty", d3)

        def d4():
            got = q.act(False)
            return "answer_from_evidence", repr(got), got == "answer_from_evidence"
        run_case("D4", "After restart: answerable case still answers", d4)

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
        run_case("D5", "Second re-initialization: audit still append-only, chain "
                 "valid", d5)

        # Gap probes on the base engine, whose README states that audit-history
        # reset and rule-state restore are not implemented in rre_minimal.py.
        audit_b = tmp / "groupD_base_audit.jsonl"
        rb = RRE(audit_b)
        rb.apply(rb.propose(), approved_by=APPROVER)
        rb.act(True, "pre-restart missing probe")
        rb.act(False, "pre-restart answerable probe")
        T["base_lines_before"] = len(
            audit_b.read_text(encoding="utf-8").splitlines())

        rb2 = RRE(audit_b)  # base-engine re-initialization

        def d6():
            lines_after = len(
                audit_b.read_text(encoding="utf-8").splitlines())
            ok, msg = verify_audit(audit_b)
            return ("prior audit events survive re-initialization",
                    f"events_before={T['base_lines_before']}, "
                    f"events_after={lines_after}, chain=({ok}, {msg!r})",
                    lines_after >= T["base_lines_before"])
        run_case("D6", "Base engine: audit history survives re-initialization "
                 "(gap probe)", d6)

        def d7():
            got = rb2.act(True, "post-restart missing probe")
            return ("report_unknown (corrected state survives restart)",
                    repr(got), got == "report_unknown")
        run_case("D7", "Base engine: corrected behavior survives re-initialization "
                 "(gap probe)", d7)

    total = len(RESULTS)
    failed_ids = [row["case_id"] for row in RESULTS if not row["passed"]]
    print("=" * 78)
    print(f"TOTAL: {total}  PASSED: {total - len(failed_ids)}  "
          f"FAILED: {len(failed_ids)}")
    if failed_ids:
        print("FAILED CASES: " + ", ".join(failed_ids))

    report = {
        "evaluator": "ota-independent-evaluator",
        "target": ("Founder5222196/recursive-revision-engine @ "
                   "862fa5a9714709980ee269b624a6308360de2ae2"),
        "method": "black-box, public interfaces only",
        "total": total,
        "passed": total - len(failed_ids),
        "failed": len(failed_ids),
        "failed_case_ids": failed_ids,
        "cases": RESULTS,
    }
    report_path = Path("ota_independent_eval_report.json").resolve()
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Report: {report_path}")
    return 0 if not failed_ids else 1


if __name__ == "__main__":
    raise SystemExit(main())
