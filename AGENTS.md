# Entity Pipeline Contributor Guide

This repository contains a plugin based framework for building AI agents.
Use this document when preparing changes or reviewing pull requests.

## Important Notes
- **You must adhere to architectural guidelines when making changes.** See
  `ARCHITECTURE.md` for details on the architectural design and principles.
- DO NOT change the `ARCHITECTURE.md` file!
- Refer to `CONTRIBUTING.md` for general contribution guidelines.
- The project is pre-alpha; remove unused code rather than keeping backward compatibility.
- Prefer adding `TODO:` comments when scope is unclear.
- Create `AGENT NOTE:` comments for other agents.
- Always use the Poetry environment for development.
- Run `poetry install --with dev` before executing any quality checks or tests.

## Architecture
Here is the architecture directory.  Below are references to architectural notes found in `ARCHITECTURE.md`.  Please grep the `ARCHITECTURE.md` file for the section titles to find the full text.  To find the architectural notes, search for the section titles below in `ARCHITECTURE.md`:

```
grep '^## <NUM>\. ' ARCHITECTURE.md
```

The `<NUM>` is the number in the section title above, e.g. `## 1. Core Mental Model: Plugin Taxonomy and Architecture` is section 1.
Absolutely. Here’s your architecture decision summary reformatted to your requested style:
