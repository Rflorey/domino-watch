# Briefing Spec Changelog

Track changes to `prompts/daily-brief.md` here. Each entry: date, what
changed, why. This gives the grade history an audit trail when the
spec evolves.

## 2026-04-24
- Initial spec captured. No changes yet.

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
