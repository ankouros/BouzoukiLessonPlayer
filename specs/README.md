# Specs Folder

This directory contains design contracts and specs for features or
subsystems of BouzoukiLessonsPlayer.

## Purpose

- Capture **design decisions** before significant coding work.  
- Provide a **single place** to track the status of each design.  
- Help both humans and agents reason about changes over time.

## Workflow

For any non-trivial change:

1. **Create a design contract**
   - Copy `design-contract-template.md` to a new file under `specs/`.  
   - Use a descriptive name, e.g.:
     - `specs/lesson-library-v2.md`
     - `specs/metronome-integration.md`

2. **Fill in the contract**
   - Clarify problem, goals, non-goals, and the proposed approach.  
   - Describe any UI changes (screens, widgets, behaviours).  
   - Describe any data or schema changes.

3. **Review and iterate**
   - Update the spec based on review feedback.  
   - Once accepted, mark its status as **Approved**.

4. **Implementation and follow-up**
   - Reference the spec from PRs / change descriptions.  
   - Keep a short checklist in the spec and tick items as they are
     implemented.  
   - If implementation diverges, update the spec or clearly note the
     differences.

## Naming and Status

- File names should be **kebab-case** and descriptive.  
- Each spec must contain a **Status** field (e.g. Draft, In Review,
  Approved, Superseded).

## Relationship to Other Docs

- Use `ROADMAP.md` for **high-level planning** and milestones.  
- Use `OPEN-ISSUES.mg` for **granular tasks** and bugs.  
- Use `AGENTS.md` for **process and behaviour** guidelines.  
- Use files in `specs/` to describe **how** a particular feature or
  subsystem should work in more detail.

