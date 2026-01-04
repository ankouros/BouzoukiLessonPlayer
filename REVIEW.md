# BouzoukiLessonsPlayer – Review Guidelines

This document describes how code changes should be reviewed in this
repository. It is intended for both humans and automated agents.

## Goals of Review

- Maintain a stable, reliable practice tool for bouzouki.  
- Keep the codebase understandable and easy to extend.  
- Protect user data (especially `lessons.db` and media paths).  
- **Base decisions on automated test artifacts**, not only on manual
  reasoning.

## What Reviewers Should Check

1. **Correctness**  
   - Does the change do what the author claims?  
   - Are edge cases considered (missing `lessons.db`, missing media
     files, invalid DB rows, unexpected user input)?  
   - For UI changes, is the behaviour consistent with other parts of
     the app (e.g. master/detail interactions)?

2. **Safety**  
   - Are database operations safe and non-destructive by default?  
   - Could this change lose or corrupt user data (e.g. renaming or
     deleting media without updating the DB)?  
   - Does any long-running work block the UI thread, or is it
     dispatched to worker threads like `FolderScannerWorker`?

3. **Style and Consistency**  
   - Does the code follow patterns in nearby files and modules?  
   - Are names descriptive and clear (avoid one-letter variables)?  
   - Is complexity kept under control (no deeply nested logic where a
     helper function would help)?  
   - Does the change respect existing separation between `core/`
     (non-UI logic) and `ui/` (presentation and interaction)?

4. **User Experience**  
   - Are error messages clear and actionable (e.g. when a file is
     missing, explain how to fix it)?  
   - Does the UI remain responsive and consistent with the rest of the
     app?  
   - Are new features discoverable and not surprising (menus, buttons,
     shortcuts)?

5. **Testing / Validation**  
   - Are there automated tests covering the new or changed behaviour?  
   - Were `make code-check` and `make test` (and optionally `make lint`)
     run, and are their results documented?  
   - For risky changes (DB schema, large refactors, file operations),
     are tests added or extended to lock in the new behaviour?  
   - If code touches metronome or tap tools, is their dependency
     handling considered (numpy, simpleaudio, PyQt5)?

## Review Checklist

Before approving a change, reviewers should be able to answer “yes” to
most of the following:

- [ ] The change is clearly described in the summary / commit message.  
- [ ] The scope is appropriate and not mixing unrelated changes.  
- [ ] The code is readable and follows existing conventions.  
- [ ] Error handling is in place for obvious failure modes (DB errors,
      missing files, invalid user input).  
- [ ] Automated tests exist or are updated where appropriate.  
- [ ] `make code-check` and `make test` have been run and their
      outcomes are known.  
- [ ] There are no obvious performance problems (e.g. heavy work on
      the main thread inside hot paths).  
- [ ] Sensitive data (user files, DB) is handled carefully.  
- [ ] New or changed behaviour is reflected in `ROADMAP.md` or
      `OPEN-ISSUES.mg` if appropriate.

## Guidance for Agents During Review

When acting as a reviewer or auto-fixer, agents should:

- Prefer minimal, targeted fixes over broad refactors.  
- Avoid reformatting large files unless asked.  
- Call out assumptions explicitly when they cannot be verified.  
- Suggest follow-up issues for non-blocking problems, and add them to
  `OPEN-ISSUES.mg` where appropriate.  
- Point out any divergence from existing design contracts under
  `specs/` and propose updates to those contracts.  
- Use automated test results as primary evidence when deciding whether
  a change is acceptable.

## Merging and Versioning

- Keep the main branch in a working state (app should start without
  errors and basic flows should work).  
- For larger changes, prefer incremental PRs that are easier to
  review.  
- When making breaking changes or important user-visible updates,
  update the roadmap (`ROADMAP.md`) and, if needed, create or revise a
  spec under `specs/`.  
- Treat the addition or improvement of tests as part of the definition
  of “done” for any substantial change.

