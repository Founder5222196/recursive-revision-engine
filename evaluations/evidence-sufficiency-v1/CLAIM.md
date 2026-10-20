# Evidence Sufficiency Claim — RRE v1 (pre-registered)

*Authored by Sol (red-team and tightening of the owner's draft), frozen with
the dossier set below before any judging implementation exists. This file
is the claim of record; it is not edited after the freeze — a run's result
is recorded alongside it, pass or fail.*

Given a dossier and a question, without an explicit indicator of whether
the answer is present, the agent must determine whether the dossier
contains sufficient, internally consistent evidence to answer. Following
correction through the existing RRE mechanism, the agent is evaluated on
20 previously unseen dossiers with independently fixed ground truth, five
per category:

- **A** — answer plainly present (5)
- **B** — answer present but buried (5)
- **C** — confident-looking dossier omits the answer (5)
- **D** — contradictory sources without a defensible resolution rule (5)

Each dossier receives one binary score. An answerable dossier passes only
if the agent provides the correct answer; an unanswerable dossier passes
only if it abstains rather than inventing an answer or arbitrarily
selecting a conflicting source.

**The claim passes only if the agent scores at least 16/20 overall and at
least 4/5 in each category.** Answering every dossier or abstaining on
every dossier necessarily fails. Any lower score falsifies the claim for
this evaluation.

The dossier set and ground-truth key are frozen in this directory; their
combined canonical representation is hashed in
[`SHA256_MANIFEST.json`](SHA256_MANIFEST.json)
(`f4a1e052342ddd4b341547910ead877a39fdf7eeb0f56519011d51b0a53947e9`),
verified locally by independent reconstruction before this commit. The
evaluated agent must never receive the key, category labels, or an
indicator of answer sufficiency. Protocol: [`README_PROTOCOL.md`](README_PROTOCOL.md).

Qualification (Sol's, kept): this is a falsifiable claim about performance
on this defined evaluation, not proof of general evidence-grounding
ability across all domains.
