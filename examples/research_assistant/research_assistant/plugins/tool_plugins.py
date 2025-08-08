"""Tool plugins for executing research tasks."""

from typing import Any, Dict, List
import asyncio
import json
from pathlib import Path
from datetime import datetime

from entity.plugins.tool import ToolPlugin
from entity.workflow.executor import WorkflowExecutor
from entity.resources import LogLevel, LogCategory


class ArxivSearchPlugin(ToolPlugin):
    """Search and fetch papers from arXiv."""
    
    supported_stages = [WorkflowExecutor.DO]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.api_key = self.config.get("api_key", "")
        self.max_results = self.config.get("max_results", 50)
        self.sort_by = self.config.get("sort_by", "relevance")
        self.include_abstracts = self.config.get("include_abstracts", True)
    
    async def _execute_impl(self, context) -> None:
        """Search arXiv for relevant papers."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO,
            LogCategory.TOOL_USAGE,
            "Searching arXiv for papers"
        )
        
        research_plan = await context.recall("research_plan", {})
        search_terms = research_plan.get("search_terms", [])
        max_results = min(
            self.max_results, 
            research_plan.get("max_results_per_source", 20)
        )
        
        # Simulate arXiv search (in real implementation, use arxiv API)
        papers = []
        for term in search_terms[:3]:  # Search top 3 terms
            # Simulated search results
            paper_results = await self._search_arxiv(term, max_results // 3)
            papers.extend(paper_results)
            
            await logger.log(
                LogLevel.DEBUG,
                LogCategory.TOOL_USAGE,
                f"Found {len(paper_results)} papers for term: {term}"
            )
        
        # Store results
        await context.remember("arxiv_papers", papers)
        await logger.log(
            LogLevel.INFO,
            LogCategory.TOOL_USAGE,
            f"ArXiv search complete: found {len(papers)} papers"
        )
    
    async def _search_arxiv(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Simulate arXiv API search."""
        # In real implementation, use actual arXiv API
        # This is a simulation for the example
        papers = []
        for i in range(min(3, max_results)):
            papers.append({
                "id": f"arxiv:2024.{1000+i}",
                "title": f"Research on {query}: Paper {i+1}",
                "authors": ["Author A", "Author B"],
                "abstract": f"This paper investigates {query} using novel approaches...",
                "published": "2024-01-15",
                "categories": ["cs.AI", "cs.LG"],
                "url": f"https://arxiv.org/abs/2024.{1000+i}"
            })
        return papers


class WebSearchPlugin(ToolPlugin):
    """Search the web for academic content."""
    
    supported_stages = [WorkflowExecutor.DO]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.api_key = self.config.get("api_key", "")
        self.academic_focus = self.config.get("academic_focus", True)
        self.prefer_domains = self.config.get("prefer_domains", [])
        self.exclude_domains = self.config.get("exclude_domains", [])
    
    async def _execute_impl(self, context) -> None:
        """Search the web for research content."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO,
            LogCategory.TOOL_USAGE,
            "Performing web search"
        )
        
        research_plan = await context.recall("research_plan", {})
        search_terms = research_plan.get("search_terms", [])
        
        # Build search queries
        if self.academic_focus:
            queries = [f"scholarly {term}" for term in search_terms[:2]]
        else:
            queries = search_terms[:2]
        
        # Simulate web search
        web_results = []
        for query in queries:
            results = await self._search_web(query)
            web_results.extend(results)
        
        # Filter by preferred domains
        if self.prefer_domains:
            preferred = [r for r in web_results if any(
                domain in r["url"] for domain in self.prefer_domains
            )]
            other = [r for r in web_results if r not in preferred]
            web_results = preferred + other
        
        # Store results
        await context.remember("web_results", web_results)
        await logger.log(
            LogLevel.INFO,
            LogCategory.TOOL_USAGE,
            f"Web search complete: found {len(web_results)} results"
        )
    
    async def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """Simulate web search API."""
        # In real implementation, use actual search API
        results = []
        for i in range(3):
            results.append({
                "title": f"Web result for {query} - {i+1}",
                "url": f"https://example.com/{query.replace(' ', '-')}-{i+1}",
                "snippet": f"Research findings on {query} show significant progress...",
                "domain": "example.com"
            })
        return results


class PDFAnalyzerPlugin(ToolPlugin):
    """Analyze PDF documents for research content."""
    
    supported_stages = [WorkflowExecutor.DO]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.extract_figures = self.config.get("extract_figures", True)
        self.extract_tables = self.config.get("extract_tables", True)
        self.extract_references = self.config.get("extract_references", True)
        self.ocr_enabled = self.config.get("ocr_enabled", True)
    
    async def _execute_impl(self, context) -> None:
        """Analyze PDF documents."""
        logger = context.get_resource("logging")
        
        # Check if there's a PDF to analyze
        pdf_path = await context.recall("input_pdf", None)
        if not pdf_path:
            return
        
        await logger.log(
            LogLevel.INFO,
            LogCategory.TOOL_USAGE,
            f"Analyzing PDF: {Path(pdf_path).name}"
        )
        
        # Simulate PDF analysis
        pdf_analysis = await self._analyze_pdf(pdf_path)
        
        # Store analysis results
        await context.remember("pdf_analysis", pdf_analysis)
        
        # Extract key findings
        if pdf_analysis["references"]:
            await context.remember("pdf_references", pdf_analysis["references"])
        
        await logger.log(
            LogLevel.INFO,
            LogCategory.TOOL_USAGE,
            "PDF analysis complete",
            page_count=pdf_analysis["page_count"],
            reference_count=len(pdf_analysis["references"])
        )
    
    async def _analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Simulate PDF analysis."""
        # In real implementation, use PDF parsing library
        return {
            "title": "Example Research Paper",
            "authors": ["John Doe", "Jane Smith"],
            "abstract": "This paper presents groundbreaking research...",
            "page_count": 12,
            "sections": [
                "Introduction",
                "Related Work",
                "Methodology",
                "Results",
                "Discussion",
                "Conclusion"
            ],
            "key_findings": [
                "Finding 1: Novel approach shows 95% accuracy",
                "Finding 2: Significant improvement over baseline",
                "Finding 3: Scalable to large datasets"
            ],
            "references": [
                {
                    "title": "Previous Important Work",
                    "authors": ["Smith et al."],
                    "year": 2023,
                    "venue": "Nature"
                }
            ],
            "figures": ["Figure 1: System Architecture", "Figure 2: Results"],
            "tables": ["Table 1: Performance Metrics"]
        }


class SemanticScholarPlugin(ToolPlugin):
    """Search Semantic Scholar for academic papers."""
    
    supported_stages = [WorkflowExecutor.DO]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.api_key = self.config.get("api_key", "")
        self.include_citations = self.config.get("include_citations", True)
        self.include_references = self.config.get("include_references", True)
    
    async def _execute_impl(self, context) -> None:
        """Search Semantic Scholar for papers."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO,
            LogCategory.TOOL_USAGE,
            "Searching Semantic Scholar"
        )
        
        research_plan = await context.recall("research_plan", {})
        search_terms = research_plan.get("search_terms", [])
        
        # Simulate Semantic Scholar search
        papers = []
        for term in search_terms[:2]:
            paper_results = await self._search_semantic_scholar(term)
            papers.extend(paper_results)
        
        # Get citation networks if requested
        if self.include_citations and papers:
            for paper in papers[:5]:  # Top 5 papers
                paper["citations"] = await self._get_citations(paper["id"])
                paper["references"] = await self._get_references(paper["id"])
        
        await context.remember("semantic_scholar_papers", papers)
        await logger.log(
            LogLevel.INFO,
            LogCategory.TOOL_USAGE,
            f"Semantic Scholar search complete: {len(papers)} papers"
        )
    
    async def _search_semantic_scholar(self, query: str) -> List[Dict[str, Any]]:
        """Simulate Semantic Scholar API search."""
        papers = []
        for i in range(2):
            papers.append({
                "id": f"S2_{query[:5]}_{i}",
                "title": f"Semantic Scholar result: {query} Study {i+1}",
                "authors": ["Research Team A"],
                "year": 2024,
                "abstract": f"This study examines {query} from multiple perspectives...",
                "venue": "Conference on AI Research",
                "citation_count": 50 + i * 10,
                "influential_citation_count": 5 + i
            })
        return papers
    
    async def _get_citations(self, paper_id: str) -> List[str]:
        """Get papers that cite this paper."""
        return [f"Citation_{paper_id}_{i}" for i in range(3)]
    
    async def _get_references(self, paper_id: str) -> List[str]:
        """Get papers referenced by this paper."""
        return [f"Reference_{paper_id}_{i}" for i in range(5)]


class DataVisualizerPlugin(ToolPlugin):
    """Create visualizations from research data."""
    
    supported_stages = [WorkflowExecutor.DO]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.chart_types = self.config.get("chart_types", ["bar", "line", "scatter"])
        self.export_formats = self.config.get("export_formats", ["png", "svg"])
    
    async def _execute_impl(self, context) -> None:
        """Create data visualizations."""
        logger = context.get_resource("logging")
        file_storage = context.get_resource("file_storage")
        
        # Check if we have data to visualize
        arxiv_papers = await context.recall("arxiv_papers", [])
        semantic_papers = await context.recall("semantic_scholar_papers", [])
        
        if not arxiv_papers and not semantic_papers:
            return
        
        await logger.log(
            LogLevel.INFO,
            LogCategory.TOOL_USAGE,
            "Creating research visualizations"
        )
        
        visualizations = []
        
        # Create publication timeline
        if arxiv_papers or semantic_papers:
            timeline_data = await self._create_timeline_chart(
                arxiv_papers + semantic_papers
            )
            
            # Save visualization
            viz_path = await file_storage.save(
                "research_timeline.json",
                json.dumps(timeline_data)
            )
            visualizations.append({
                "type": "timeline",
                "title": "Publication Timeline",
                "path": viz_path,
                "data": timeline_data
            })
        
        # Create citation network if available
        if semantic_papers and any(p.get("citations") for p in semantic_papers):
            network_data = await self._create_citation_network(semantic_papers)
            
            viz_path = await file_storage.save(
                "citation_network.json",
                json.dumps(network_data)
            )
            visualizations.append({
                "type": "network",
                "title": "Citation Network",
                "path": viz_path,
                "data": network_data
            })
        
        await context.remember("visualizations", visualizations)
        await logger.log(
            LogLevel.INFO,
            LogCategory.TOOL_USAGE,
            f"Created {len(visualizations)} visualizations"
        )
    
    async def _create_timeline_chart(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create timeline visualization data."""
        # Extract years and count papers
        year_counts = {}
        for paper in papers:
            year = paper.get("year") or paper.get("published", "")[:4]
            if year and str(year).isdigit():
                year = int(year)
                year_counts[year] = year_counts.get(year, 0) + 1
        
        return {
            "type": "bar",
            "title": "Papers by Year",
            "x_axis": "Year",
            "y_axis": "Number of Papers",
            "data": [
                {"year": year, "count": count}
                for year, count in sorted(year_counts.items())
            ]
        }
    
    async def _create_citation_network(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create citation network visualization data."""
        nodes = []
        edges = []
        
        # Create nodes for papers
        for paper in papers[:10]:  # Limit to top 10 for clarity
            nodes.append({
                "id": paper["id"],
                "label": paper["title"][:50] + "...",
                "citations": paper.get("citation_count", 0)
            })
            
            # Add citation edges
            for cited_id in paper.get("citations", [])[:3]:
                edges.append({
                    "source": paper["id"],
                    "target": cited_id,
                    "type": "cites"
                })
        
        return {
            "type": "network",
            "nodes": nodes,
            "edges": edges,
            "layout": "force-directed"
        }