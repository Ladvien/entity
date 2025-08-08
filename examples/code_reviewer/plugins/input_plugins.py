"""Input stage plugins for code review agent."""

from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel

from entity.plugins.input_adapter import InputAdapterPlugin
from entity.resources.logging import LogCategory, LogLevel
from entity.workflow.executor import WorkflowExecutor


class CodeInputPlugin(InputAdapterPlugin):
    """Process code review requests for files, directories, or repositories."""

    class ConfigModel(BaseModel):
        """Configuration for code input processing."""

        supported_extensions: list[str] = [
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".rs",
        ]
        max_file_size: int = 1024 * 1024  # 1MB
        exclude_patterns: list[str] = ["__pycache__", "node_modules", ".git", "*.pyc"]
        include_hidden: bool = False

    supported_stages = [WorkflowExecutor.INPUT]

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.validate_config()

    async def _execute_impl(self, context) -> str:
        """Process code input and prepare files for review."""
        logger = context.get_resource("logging")

        await logger.log(
            LogLevel.DEBUG,
            LogCategory.PLUGIN_LIFECYCLE,
            "Processing code input",
            plugin_name=self.__class__.__name__,
        )

        user_message = context.message or ""

        # Determine review type based on input
        review_context = await self._analyze_input(context, user_message)
        await context.remember("review_context", review_context)

        # Process files based on review type
        if review_context["type"] == "file":
            await self._process_file(context, review_context["target"])
        elif review_context["type"] == "directory":
            await self._process_directory(context, review_context["target"])
        elif review_context["type"] == "diff":
            await self._process_diff(context, review_context["target"])
        else:
            # General code review request
            await context.remember("review_request", user_message)

        await logger.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            "Code input processed",
            review_type=review_context["type"],
            files_count=len(review_context.get("files", [])),
        )

        return user_message

    async def _analyze_input(self, context, message: str) -> dict:
        """Analyze input to determine review type and target."""
        review_context = {
            "type": "general",
            "target": message,
            "files": [],
            "metadata": {},
        }

        # Check if input contains file paths
        words = message.split()
        for word in words:
            path = Path(word)
            if path.exists():
                if path.is_file():
                    review_context["type"] = "file"
                    review_context["target"] = str(path)
                    break
                elif path.is_dir():
                    review_context["type"] = "directory"
                    review_context["target"] = str(path)
                    break

        # Check for git diff or patch content
        if any(
            indicator in message.lower() for indicator in ["diff", "patch", "@@", "+++"]
        ):
            review_context["type"] = "diff"

        # Check for PR or repository URLs
        if any(
            url_part in message
            for url_part in ["github.com", "gitlab.com", "pull", "merge"]
        ):
            review_context["type"] = "pr"
            review_context["url"] = self._extract_url(message)

        return review_context

    async def _process_file(self, context, file_path: str) -> None:
        """Process a single file for review."""
        logger = context.get_resource("logging")
        path = Path(file_path)

        if not path.exists():
            await logger.log(
                LogLevel.WARNING, LogCategory.ERROR, f"File not found: {file_path}"
            )
            return

        # Check file size
        if path.stat().st_size > self.config.max_file_size:
            await logger.log(
                LogLevel.WARNING, LogCategory.ERROR, f"File too large: {file_path}"
            )
            await context.remember(
                "error", f"File {file_path} exceeds maximum size limit"
            )
            return

        # Check extension
        if path.suffix not in self.config.supported_extensions:
            await logger.log(
                LogLevel.WARNING,
                LogCategory.ERROR,
                f"Unsupported file type: {path.suffix}",
            )

        try:
            content = path.read_text(encoding="utf-8")
            file_info = {
                "path": file_path,
                "name": path.name,
                "extension": path.suffix,
                "size": path.stat().st_size,
                "lines": len(content.split("\n")),
                "content": content,
            }

            await context.remember("review_files", [file_info])
            await logger.log(
                LogLevel.INFO,
                LogCategory.USER_ACTION,
                f"Loaded file for review: {file_path}",
            )

        except Exception as e:
            await logger.log(
                LogLevel.ERROR,
                LogCategory.ERROR,
                f"Failed to read file {file_path}: {e}",
            )
            await context.remember("error", f"Could not read file: {e}")

    async def _process_directory(self, context, dir_path: str) -> None:
        """Process all code files in a directory."""
        logger = context.get_resource("logging")
        path = Path(dir_path)
        files_info = []

        try:
            for file_path in path.rglob("*"):
                if (
                    file_path.is_file()
                    and file_path.suffix in self.config.supported_extensions
                    and not self._is_excluded(file_path)
                    and file_path.stat().st_size <= self.config.max_file_size
                ):
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        file_info = {
                            "path": str(file_path),
                            "name": file_path.name,
                            "extension": file_path.suffix,
                            "size": file_path.stat().st_size,
                            "lines": len(content.split("\n")),
                            "content": content,
                            "relative_path": str(file_path.relative_to(path)),
                        }
                        files_info.append(file_info)

                    except Exception as e:
                        await logger.log(
                            LogLevel.WARNING,
                            LogCategory.ERROR,
                            f"Skipped {file_path}: {e}",
                        )

            await context.remember("review_files", files_info)
            await logger.log(
                LogLevel.INFO,
                LogCategory.USER_ACTION,
                f"Loaded {len(files_info)} files from directory: {dir_path}",
            )

        except Exception as e:
            await logger.log(
                LogLevel.ERROR,
                LogCategory.ERROR,
                f"Failed to process directory {dir_path}: {e}",
            )
            await context.remember("error", f"Could not process directory: {e}")

    async def _process_diff(self, context, diff_content: str) -> None:
        """Process git diff or patch content."""
        await context.remember("review_diff", diff_content)

        # Parse diff to extract file information
        files_changed = []
        lines = diff_content.split("\n")
        current_file = None

        for line in lines:
            if line.startswith("diff --git") or line.startswith("+++"):
                if "+++" in line:
                    # Extract filename from +++ b/filename
                    current_file = line.split("+++")[-1].strip().lstrip("b/")
                    if current_file != "/dev/null":
                        files_changed.append(current_file)

        await context.remember("files_changed", files_changed)
        await context.get_resource("logging").log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            f"Processing diff with {len(files_changed)} files changed",
        )

    def _is_excluded(self, path: Path) -> bool:
        """Check if path should be excluded based on patterns."""
        path_str = str(path)
        for pattern in self.config.exclude_patterns:
            if pattern in path_str:
                return True

        if not self.config.include_hidden and any(
            part.startswith(".") for part in path.parts
        ):
            return True

        return False

    def _extract_url(self, message: str) -> str:
        """Extract URL from message."""
        words = message.split()
        for word in words:
            if any(domain in word for domain in ["github.com", "gitlab.com"]):
                return word
        return ""
