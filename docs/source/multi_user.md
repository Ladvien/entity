# Multi-User Patterns

The framework isolates conversation data by accepting a `user_id` parameter on every pipeline run.

````python
response = await agent.chat("Hi", user_id="alice")
````

All persistent keys and conversation IDs are automatically namespaced using this identifier:

````python
pipeline_id = f"{user_id}_{generate_pipeline_id()}"
await memory.save_conversation(pipeline_id, history)
````

Plugins access the active user through `ctx.user_id` and store data via the canonical `Memory` resource. The memory implementation prefixes keys with the `user_id` to prevent leaks between users.

Deploy a single agent for many users or separate deployments per organization as security requirements demand. This approach requires no extra configuration and works within the stateless worker model described in [Decision #29](../ARCHITECTURE.md#29-multi-user-support-user_id-parameter-pattern).
