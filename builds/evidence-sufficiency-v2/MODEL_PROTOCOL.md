# Grounded Evidence Judge — model protocol (development build)

## Status and boundary

This package contains no bundled language model, API credential, or provider integration. The semantic extractor is an injected callable with signature `model(question: str, dossier: str) -> dict`. Consequently, no claim is made that the model adapter has been exercised against a production model. The deterministic validation and policy layers are independently testable with stubs. Record the provider, exact model identifier, prompt/template hash, decoding parameters, date, and adapter version for every real run; `unconfigured` is not a valid production identity.

## Evidence record `evidence-record/1.0`

Top-level fields: `schema_version`, exact `question`, SHA-256 `dossier_sha256`, and a `candidates` list. Every candidate requires `source_span`, `entity`, `attribute`, `value`, object-valued `scope`, `assertion_type`, and `relation`. Optional `source_start` / `source_end` offsets are zero-based half-open offsets and must exactly identify the source span. The source span must occur verbatim in the dossier. Candidate order is retained; candidates are never deduplicated or conflict-resolved during extraction.

`assertion_type` is one of `asserted`, `negated`, `hypothetical`, `estimated`, `historical`, `conditional`, or `unknown`. Keep meaningful units, negation, temporal qualifiers, modality, and conditions in `value` or `scope`; do not normalize them away. `scope` is an extensible JSON object (e.g. time, location, condition, source passage). The schema does not impose a fixed attribute vocabulary.

## Adapter instructions

The model should return all plausible candidate assertions relevant to the question, including competing values. It must not use external knowledge, assume answerability, or choose between conflicts. `relation` describes the relation actually expressed by the source span, not a free-form rationale. When subject, attribute, value, or scope is unclear, return the candidate with the uncertainty represented or return no candidate; never fabricate a quote. The model output is untrusted until deterministic validation passes.

## Sufficiency policy `sufficiency/1.0`

Only asserted candidates are eligible by default. The caller supplies question-conditioned `target_entity` and `target_attribute` where the semantic adapter can reliably bind them; the policy does not infer them from a hard-coded alias list. Same entity + attribute + scope + assertion type with non-equivalent values is an unresolved contradiction and mandates abstention. Multiple different values that cannot be unambiguously attributed to the target also mandate abstention. No source is privileged by apparent authority. Compatible evidence can be represented as multiple candidates, but this minimal policy returns a value only when eligible candidates agree. This is intentionally conservative; semantic compatibility and complex multi-hop synthesis still require a model-conditioned adjudication extension and must not be claimed solved by this baseline.

## Response contract

Exactly `ANSWER: <nonempty answer>` or `ABSTAIN: <nonempty reason>`. The deterministic gate rejects lower-case labels, missing spaces, empty payloads, extra lines, and any other form. It does not repair malformed output. Evidence-record rejection becomes an explicit abstention; malformed externally supplied response text raises `ValueError`.

## Versioning and authorization

`VersionedPolicyExtension` is an explicit sidecar extension to the canonical RRE, not a fork. Initialization only creates the separate policy state and audit records; it does not change canonical engine rules. Proposals bind current/target version, previous policy, new policy, rationale, provenance, model configuration, and a proposal digest. Applying requires a current proposal and nonblank named reviewer. Policy/model configuration is persisted separately from RRE's legacy `missing_evidence` rule; changing policy does not train or modify model weights. Audit integrity is hash-chain checked with the canonical verifier. Rollback is an explicit named-authority action. Independent verification/sign-off remains a human/evaluator responsibility.
