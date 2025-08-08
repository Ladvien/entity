"""Thinking stage plugins for research planning and strategy."""

from typing import Any, Dict, List
import json
import re

from entity.plugins.prompt import PromptPlugin
from entity.workflow.executor import WorkflowExecutor
from entity.resources import LogLevel, LogCategory


class ResearchPlannerPlugin(PromptPlugin):
    """Plan research strategy based on query analysis."""
    
    supported_stages = [WorkflowExecutor.THINK]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.strategies = self.config.get("strategies", [
            "systematic_review",
            "exploratory_search",
            "focused_analysis"
        ])
        self.max_search_depth = self.config.get("max_search_depth", 3)
        self.prioritize_recent = self.config.get("prioritize_recent", True)
    
    async def _execute_impl(self, context) -> None:
        """Create a comprehensive research plan."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Creating research plan"
        )
        
        # Gather all parsed information
        query_analysis = await context.recall("query_analysis", "")
        entities = await context.recall("extracted_entities", {})
        sources = await context.recall("sources", ["arxiv", "web"])
        max_papers = await context.recall("max_papers", 20)
        timeframe = await context.recall("query_timeframe", {})
        
        llm = context.get_resource("llm")
        
        # Create research plan
        plan_prompt = f"""Create a detailed research plan based on this analysis:

Query Analysis: {query_analysis}
Available Sources: {', '.join(sources)}
Maximum Papers to Analyze: {max_papers}
Timeframe Focus: {json.dumps(timeframe)}
Key Terms: {entities.get('keywords', '')}

Create a research plan that includes:
1. Search strategy for each source
2. Priority ranking of search terms
3. Inclusion/exclusion criteria
4. Analysis approach
5. Expected outputs

Consider the research depth needed and time constraints.
Format as a structured plan:"""
        
        plan_result = await llm.generate(plan_prompt)
        
        # Determine research strategy
        strategy = await self._determine_strategy(context, query_analysis)
        
        # Create structured research plan
        research_plan = {
            "strategy": strategy,
            "search_plan": plan_result.content,
            "sources": sources,
            "search_terms": self._prioritize_search_terms(entities),
            "max_results_per_source": max(10, max_papers // len(sources)),
            "timeframe": timeframe,
            "inclusion_criteria": await self._generate_criteria(context, "inclusion"),
            "exclusion_criteria": await self._generate_criteria(context, "exclusion"),
            "analysis_depth": self._determine_depth(max_papers, strategy)
        }
        
        await context.remember("research_plan", research_plan)
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Research plan created",
            strategy=strategy,
            source_count=len(sources)
        )
    
    async def _determine_strategy(self, context, analysis: str) -> str:
        """Determine the best research strategy."""
        llm = context.get_resource("llm")
        
        strategy_prompt = f"""Based on this query analysis, recommend the best research strategy:

Analysis: {analysis}

Available strategies:
- systematic_review: Comprehensive, methodical search following PRISMA guidelines
- exploratory_search: Broad search to understand the landscape
- focused_analysis: Deep dive into specific papers/topics

Which strategy is most appropriate? Respond with just the strategy name:"""
        
        result = await llm.generate(strategy_prompt)
        strategy = result.content.strip().lower()
        
        # Validate and default to exploratory if unclear
        if strategy not in self.strategies:
            strategy = "exploratory_search"
        
        return strategy
    
    def _prioritize_search_terms(self, entities: Dict[str, Any]) -> List[str]:
        """Prioritize search terms based on extracted entities."""
        terms = []
        
        # Extract terms from keywords
        if "keywords" in entities:
            # Simple parsing of keyword output
            keyword_text = entities["keywords"]
            lines = keyword_text.split('\n')
            for line in lines:
                if ':' in line:
                    # Extract terms after colon
                    term_part = line.split(':', 1)[1].strip()
                    terms.extend([t.strip() for t in term_part.split(',') if t.strip()])
        
        # Add query terms
        if "query_terms" in entities:
            terms.extend(entities["query_terms"])
        
        # Remove duplicates while preserving order
        seen = set()
        prioritized = []
        for term in terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                prioritized.append(term)
        
        return prioritized[:10]  # Top 10 terms
    
    async def _generate_criteria(self, context, criteria_type: str) -> List[str]:
        """Generate inclusion or exclusion criteria."""
        llm = context.get_resource("llm")
        query = await context.recall("original_query", "")
        
        criteria_prompt = f"""Generate {criteria_type} criteria for research papers on this topic:

Query: {query}

List 3-5 clear {criteria_type} criteria:"""
        
        result = await llm.generate(criteria_prompt)
        
        # Parse criteria from response
        criteria = []
        lines = result.content.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove bullet points or numbers
                criterion = re.sub(r'^[\d\-•.\s]+', '', line).strip()
                if criterion:
                    criteria.append(criterion)
        
        return criteria[:5]
    
    def _determine_depth(self, max_papers: int, strategy: str) -> str:
        """Determine analysis depth based on paper count and strategy."""
        if strategy == "systematic_review":
            return "comprehensive"
        elif max_papers <= 10:
            return "detailed"
        elif max_papers <= 30:
            return "moderate"
        else:
            return "summary"