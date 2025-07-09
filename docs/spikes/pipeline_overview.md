# Pipeline Overview

The Entity Pipeline Framework executes a single pass through a series of stages. Plugins implement each stage to keep responsibilities clear.

## Stages
- **parse** – validate input and load context
- **think** – reason and plan
- **do** – execute tools and actions
- **review** – format and validate responses
- **deliver** – send output to the user
- **error** – handle failures gracefully

After completing these stages, the pipeline checks `state.response`. If no
response has been produced, the same stages run again until a response exists or
`max_iterations` is reached. The default limit is five iterations. When the
limit is exceeded the pipeline triggers the `error` stage. Pass a different
`max_iterations` value to `execute_pipeline` to adjust this limit.
