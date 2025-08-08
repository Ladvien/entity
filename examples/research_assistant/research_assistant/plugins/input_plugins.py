"""Input plugins for the research assistant."""

from pathlib import Path
from typing import Any, Dict
import mimetypes

from entity.plugins.input_adapter import InputAdapterPlugin
from entity.workflow.executor import WorkflowExecutor
from entity.resources import LogLevel, LogCategory


class MultiModalInputPlugin(InputAdapterPlugin):
    """Handle various input formats for research queries."""
    
    supported_stages = [WorkflowExecutor.INPUT]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.supported_formats = self.config.get(
            "supported_formats", 
            ["text", "pdf", "url", "image"]
        )
        self.max_file_size = self.config.get("max_file_size", 50 * 1024 * 1024)  # 50MB
    
    async def _execute_impl(self, context) -> None:
        """Process multi-modal input and prepare for research."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO, 
            LogCategory.PLUGIN_LIFECYCLE,
            "Processing multi-modal research input"
        )
        
        # Get the base message
        message = context.message or ""
        
        # Check if there's a research context with additional inputs
        research_context = await context.recall("research_context", {})
        
        # Process PDF if provided
        if "pdf_path" in research_context:
            pdf_path = Path(research_context["pdf_path"])
            if pdf_path.exists() and pdf_path.stat().st_size <= self.max_file_size:
                await logger.log(
                    LogLevel.DEBUG,
                    LogCategory.RESOURCE_ACCESS,
                    f"Loading PDF file: {pdf_path.name}",
                    file_size=pdf_path.stat().st_size
                )
                
                # Store PDF path for later processing
                await context.remember("input_pdf", str(pdf_path))
                await context.remember("input_type", "pdf_query")
                
                # Enhance message with PDF context
                message = f"Analyze the PDF '{pdf_path.name}' with focus on: {message}"
            else:
                await logger.log(
                    LogLevel.WARNING,
                    LogCategory.ERROR,
                    f"PDF file too large or not found: {pdf_path}"
                )
        
        # Detect if message contains URLs
        if "http://" in message or "https://" in message:
            urls = self._extract_urls(message)
            if urls:
                await context.remember("input_urls", urls)
                await context.remember("input_type", "url_query")
                await logger.log(
                    LogLevel.DEBUG,
                    LogCategory.RESOURCE_ACCESS,
                    f"Detected {len(urls)} URLs in query"
                )
        
        # Store processed input
        await context.remember("processed_query", message)
        await context.remember("original_query", context.message or "")
        
        # Store research parameters
        await context.remember("sources", research_context.get("sources", ["arxiv", "web"]))
        await context.remember("output_format", research_context.get("output_format", "academic"))
        await context.remember("max_papers", research_context.get("max_papers", 20))
        
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Input processing complete",
            input_type=await context.recall("input_type", "text_query"),
            sources=research_context.get("sources", [])
        )
    
    def _extract_urls(self, text: str) -> list[str]:
        """Extract URLs from text."""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)