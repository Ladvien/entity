

## Refactoring 2025-06-22
def check_limit(self, tool_name: str) -> bool:
    """Check if a specific tool can still be used"""
    # Check global limit first (account for the pending increment)
    if (
        self._global_limit is not None
        and self.get_total_usage() + 1 > self._global_limit  # +1 for this pending call
    ):
        print(f"🚫 DEBUG: Global limit would be exceeded! Current: {self.get_total_usage()}, Limit: {self._global_limit}")
        return False

    # Check per-tool limit
    usage = self._usage_count.get(tool_name, 0)
    max_uses = self._limits.get(tool_name)
    if max_uses is not None and usage >= max_uses:
        print(f"🚫 DEBUG: Tool '{tool_name}' individual limit hit! Usage: {usage}, Limit: {max_uses}")
        return False

    return True