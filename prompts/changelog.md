# Briefing Spec Changelog

Track changes to `prompts/daily-brief.md` here. Each entry: date, what
changed, why. This gives the grade history an audit trail when the
spec evolves.

## 2026-04-24
- Initial spec captured. No changes yet.

## 2026-04-24 (v2.1)
- Tightened verbosity:
  - Stack capped at 8–12 rows; explicit Tier 1 (mandatory) /
    Tier 2 (if available) priority within each domino group.
  - Trigger Map capped at 6 rows; suppress `latent` rows once
    4+ non-latent triggers are present.
  - Schema enforces stack maxItems=12, trigger_map maxItems=6.
  - Stack omits unavailable data instead of emitting null rows;
    misses noted in `narrative.p2`.
- Discipline note added: depth belongs in narrative and horizon
  rationale, not in tables.

## 2026-04-24 (v2)
- Major spec expansion:
  - Added explicit **Domino Sequence** (Stages 0–5) and required
    `domino_stage` field; regime flag must align with stage.
  - Added **Trigger Map** with 8 mandatory triggers + status
    (latent/armed/cocked/firing); new `trigger_map` field.
  - Reorganized Mandatory Data Pulls into 5 groups: Carry Mechanics,
    Policy Reaction Function, Cross-Asset Stress, Geopolitics/Energy,
    Crypto Liquidity. Added: USDJPY 5d %, 1M IV, 1M risk reversal,
    3M FX swap basis, TOPIX Banks, MOVE, VIX, HY credit, gold, BTC OI.
  - Added **Analytical Prior** ("unwind-leaning tiebreaker") with
    explicit declaration requirement in `narrative.p2`.
  - Added USDJPY 5d % (pace) as a computed anchor — MOF reacts to
    pace, not level.
- Schema: added `domino_stage` and `trigger_map` as required.
  Existing briefs predating this version will fail validation;
  re-run them to regenerate.
