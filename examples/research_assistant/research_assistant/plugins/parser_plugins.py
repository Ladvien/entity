"""Parser plugins for extracting information from research queries."""

from typing import Any, Dict, List
import re
from datetime import datetime, timedelta

from entity.plugins.prompt import PromptPlugin
from entity.workflow.executor import WorkflowExecutor
from entity.resources import LogLevel, LogCategory


class QueryParserPlugin(PromptPlugin):
    """Parse research queries to extract key information."""
    
    supported_stages = [WorkflowExecutor.PARSE]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.extract_entities = self.config.get("extract_entities", True)
        self.detect_language = self.config.get("detect_language", True)
        self.identify_timeframe = self.config.get("identify_timeframe", True)
    
    async def _execute_impl(self, context) -> None:
        """Parse the research query to extract structured information."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Parsing research query"
        )
        
        query = await context.recall("processed_query", context.message)
        
        # Extract timeframe references
        if self.identify_timeframe:
            timeframe = self._extract_timeframe(query)
            await context.remember("query_timeframe", timeframe)
            await logger.log(
                LogLevel.DEBUG,
                LogCategory.PLUGIN_LIFECYCLE,
                f"Extracted timeframe: {timeframe}"
            )
        
        # Use LLM to parse query structure
        llm = context.get_resource("llm")
        
        parse_prompt = f"""Analyze this research query and extract:
1. Main research topic
2. Specific research questions (if any)
3. Methodology preferences (systematic review, meta-analysis, etc.)
4. Output requirements
5. Domain/field of study

Query: {query}

Provide a structured analysis:"""
        
        analysis = await llm.generate(parse_prompt)
        
        # Store parsed information
        await context.remember("query_analysis", analysis.content)
        await context.remember("parsed_query", {
            "original": query,
            "timeframe": await context.recall("query_timeframe", {}),
            "analysis": analysis.content
        })
        
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Query parsing complete"
        )
    
    def _extract_timeframe(self, query: str) -> Dict[str, Any]:
        """Extract time-related information from query."""
        timeframe = {}
        
        # Check for year patterns
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, query)
        if years:
            timeframe["years"] = [int(y) for y in years]
        
        # Check for relative time phrases
        if "recent" in query.lower() or "latest" in query.lower():
            timeframe["start_date"] = (datetime.now() - timedelta(days=365)).isoformat()
            timeframe["focus"] = "recent"
        elif "last decade" in query.lower():
            timeframe["start_date"] = (datetime.now() - timedelta(days=3650)).isoformat()
            timeframe["focus"] = "decade"
        elif "historical" in query.lower():
            timeframe["focus"] = "historical"
        
        return timeframe


class EntityExtractorPlugin(PromptPlugin):
    """Extract named entities and key concepts from the query."""
    
    supported_stages = [WorkflowExecutor.PARSE]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.entity_types = self.config.get(
            "types", 
            ["person", "organization", "technology", "concept"]
        )
        self.use_ner = self.config.get("use_ner", True)
    
    async def _execute_impl(self, context) -> None:
        """Extract entities and concepts from the research query."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Extracting entities from query"
        )
        
        query = await context.recall("processed_query", context.message)
        llm = context.get_resource("llm")
        
        # Use LLM for entity extraction
        entity_prompt = f"""Extract key entities and concepts from this research query.

Categories to identify:
- People/Researchers
- Organizations/Institutions
- Technologies/Methods
- Scientific Concepts
- Locations (if relevant)

Query: {query}

List the entities in each category:"""
        
        entity_result = await llm.generate(entity_prompt)
        
        # Extract keywords for search
        keyword_prompt = f"""Generate search keywords for this research query.
Include:
- Primary keywords (most important terms)
- Secondary keywords (related terms)
- Alternative terms/synonyms

Query: {query}

Keywords:"""
        
        keyword_result = await llm.generate(keyword_prompt)
        
        # Store extracted information
        entities = {
            "raw_extraction": entity_result.content,
            "keywords": keyword_result.content,
            "query_terms": self._extract_key_terms(query)
        }
        
        await context.remember("extracted_entities", entities)
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Entity extraction complete",
            entity_count=len(entities["query_terms"])
        )
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms using simple heuristics."""
        # Remove common words and extract potential key terms
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", 
                     "to", "for", "of", "with", "by", "from", "about", "what",
                     "are", "is", "how", "why", "when", "where"}
        
        words = re.findall(r'\b\w+\b', text.lower())
        key_terms = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Also extract multi-word terms (bigrams)
        bigrams = []
        for i in range(len(words) - 1):
            if words[i] not in stop_words and words[i+1] not in stop_words:
                bigrams.append(f"{words[i]} {words[i+1]}")
        
        return list(set(key_terms + bigrams))