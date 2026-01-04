# <Feature / Subsystem Name>

- **Status**: Draft | In Review | Approved | Superseded  
- **Owner**: <name/role or "Unassigned">  
- **Last Updated**: <YYYY-MM-DD>

## 1. Problem Statement

Describe the problem this spec is solving. Include current behaviour,
limitations, and why this change is needed.

## 2. Goals

List concrete goals for this change, for example:

- Goal 1
- Goal 2
- Goal 3

## 3. Non-Goals

Clarify what is explicitly out of scope so features do not balloon.

- Non-goal 1
- Non-goal 2

## 4. User Experience

Describe the user-facing behaviour:

- New screens, dialogs, or widgets.  
- Changes to existing flows.  
- Error messages or confirmations.

Mockups, sketches, or simple bullet lists are fine.

## 5. Architecture and Data

Explain the technical approach:

- Impact on modules in `core/`, `ui/`, or `metronome/`.  
- New classes, functions, or modules.  
- Data model and schema changes (especially anything touching
  `lessons.db`).

Include any important invariants or constraints that implementations
must respect.

## 6. API / Interfaces

If this change introduces or modifies programmatic interfaces, describe
them here:

- Function signatures.  
- Signals/slots and their parameters.  
- Configuration keys in `core/config.py`.

## 7. Risks and Mitigations

List key risks (data loss, performance, UX confusion, etc.) and how
they will be mitigated.

## 8. Rollout and Migration

- How will this change be rolled out?  
- Are migrations needed (e.g. DB schema updates)?  
- How do we roll back if something goes wrong?

## 9. Implementation Plan

Provide a high-level checklist of steps. This can be linked to items in
`ROADMAP.md` or `OPEN-ISSUES.mg`.

- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## 10. Follow-Up and Open Questions

- Open questions that need answers before implementation.  
- Potential follow-up work that is out of scope for this spec.

