# RRE Evidence Sufficiency Sealed Dossier Set v1

## Freeze and hash
SHA-256: `f4a1e052342ddd4b341547910ead877a39fdf7eeb0f56519011d51b0a53947e9`

Hash scope: UTF-8 bytes of the canonical JSON object containing `title`, `dossiers`, and `ground_truth_key`, serialized with lexicographically sorted keys, separators `,` and `:`, `ensure_ascii=False`, and no trailing newline. The exact canonical bytes are in `canonical_bundle_for_hash.json`.

## Protocol
1. Commit the hash manifest to the repository before any evaluation run.
2. Keep `ground_truth_key.json` and category labels away from the evaluated agent.
3. Present only each dossier's question and content, without the ID/group label.
4. Require a single response schema: either `ANSWER: <answer>` or `ABSTAIN: <brief reason>`.
5. Score answerable items as correct only if the answer matches the key (allow harmless formatting differences). Score unanswerable items as correct only for abstention.
6. Pass only with at least 16/20 overall and at least 4/5 in each category.
7. Do not modify dossiers or key after publishing the hash. If any byte changes, create a new version and hash before evaluation.

## Categories
- A: answer plainly present (5)
- B: answer present but buried (5)
- C: confident-looking dossier omits the answer (5)
- D: contradictory sources without a defensible resolution rule (5)

## Known limitations
This is a small, synthetic, English-language benchmark with short text records. It tests retrieval, unsupported-answer abstention, and abstention under explicit unresolved contradictions. It does not test external-world fact checking, source authenticity, adversarial prompt injection, multi-hop reasoning across multiple dossiers, ambiguous or underspecified questions, calibrated confidence, long-context limits, tool use, multimodal evidence, temporal updates, domain expertise, or generalization beyond these templates. The balanced category distribution is useful for a controlled first test but does not estimate real-world prevalence.
