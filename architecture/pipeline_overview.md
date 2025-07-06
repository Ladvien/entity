# Pipeline Overview

The Entity Pipeline Framework executes a single pass through a series of stages. Plugins implement each stage to keep responsibilities clear.

## Stages
- **parse** – validate input and load context
- **think** – reason and plan
- **do** – execute tools and actions
- **review** – format and validate responses
- **deliver** – send output to the user
- **error** – handle failures gracefully
