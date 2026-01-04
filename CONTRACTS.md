# BouzoukiLessonsPlayer – Contracts Overview

This document complements the `specs/` folder and summarizes the
"contracts" that guide how features are designed, built, and reviewed.

## 1. Design Contracts

Design contracts live in `specs/` and follow the
`specs/design-contract-template.md` structure.

**Intent**

- Capture the agreed behaviour and constraints for a feature before
  substantial implementation.  
- Make expectations explicit so both humans and agents can implement
  changes consistently.  
- Provide a reference for future maintenance and refactors.

**Rules**

- Non-trivial features or architectural changes **must** have a
  design contract in `specs/`.  
- Each spec must include a **Status** (Draft, In Review, Approved,
  Superseded).  
- Implementation should not diverge from an **Approved** contract
  without updating or superseding the spec.

## 2. Process Contracts

These are high-level agreements on how work is done in this repo:

- Follow `AGENTS.md` for agent behaviour, safety, and
  **test-driven-development** guidelines.  
- Use `ROADMAP.md` for planning milestones and feature waves.  
- Track concrete problems and tasks in `OPEN-ISSUES.mg`.  
- Apply `REVIEW.md` during code review and when auto-fixing.

Together, these documents form a process contract that helps keep
changes incremental, understandable, and safe for user data.

## 3. Data and Safety Contracts

While not formal schemas, we treat the following as implicit
contracts based on the current code:

- `lessons.db` contains valuable user data and must not be corrupted or
  silently dropped.  
  - The `lessons` table schema (as created in `core/database.py` and
    `core/database_manager.py`) is the canonical structure; changes to
    it should be documented in a spec and migration steps clearly
    described.  
  - The `folders` table records user-selected scan roots and should not
    be cleared without confirmation.
- Media files (audio, video, PDFs, etc.) are user-owned content;  
  - Features like rename/delete in `ui/widgets/detail.py` should always
    confirm with the user and keep DB records in sync.  
  - No feature should delete or move files outside explicit user
    actions.
- Metronome grooves and presets stored in `metronome/grooves.json` are
  user-editable config; they should not be modified in ways that lose
  user-created grooves without confirmation or backup.
- Application logs (e.g. `bouzouki_player.log`) may be used for
  troubleshooting but should not grow without bound; future work may
  introduce a rotation policy.

Any change that touches these areas should be called out in a design
contract and carefully reviewed.

## 4. Implementation and Test Contracts

For changes implementing a spec:

- Reference the spec file in commit messages or change descriptions.  
- Keep a small checklist in the spec and mark items complete as they
  are implemented.  
- Add or update **automated tests** under `tests/` so that the spec’s
  behaviour is enforced by test artifacts.  
- If constraints from the spec cannot be met, update the contract or
  explicitly document deviations, along with corresponding test
  changes.

