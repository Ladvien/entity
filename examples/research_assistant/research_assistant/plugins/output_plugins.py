"""Output plugins for generating research reports."""

from typing import Any, Dict, List
from datetime import datetime
import json

from entity.plugins.output_adapter import OutputAdapterPlugin
from entity.workflow.executor import WorkflowExecutor
from entity.resources import LogLevel, LogCategory


class ReportGeneratorPlugin(OutputAdapterPlugin):
    """Generate comprehensive research reports in various formats."""
    
    supported_stages = [WorkflowExecutor.OUTPUT]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.templates = self.config.get("templates", {})
        self.include_toc = self.config.get("include_toc", True)
        self.include_references = self.config.get("include_references", True)
        self.include_appendices = self.config.get("include_appendices", True)
        self.export_formats = self.config.get("export_formats", ["markdown"])
    
    async def _execute_impl(self, context) -> None:
        """Generate the final research report."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Generating research report"
        )
        
        # Gather all research data
        report_data = await self._gather_report_data(context)
        
        # Get output format preference
        output_format = await context.recall("output_format", "academic")
        
        # Generate report based on format
        if output_format == "academic":
            report = await self._generate_academic_report(report_data, context)
        elif output_format == "executive":
            report = await self._generate_executive_summary(report_data, context)
        elif output_format == "blog":
            report = await self._generate_blog_post(report_data, context)
        else:
            report = await self._generate_academic_report(report_data, context)
        
        # Set the final response
        await context.say(report)
        
        # Save report metadata
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "format": output_format,
            "quality_score": report_data["quality_report"].get("overall_score", 0),
            "sources_used": len(report_data["all_papers"]),
            "word_count": len(report.split())
        }
        
        await context.remember("report_metadata", metadata)
        await logger.log(
            LogLevel.INFO,
            LogCategory.WORKFLOW_EXECUTION,
            "Research report generated",
            format=output_format,
            word_count=metadata["word_count"]
        )
    
    async def _gather_report_data(self, context) -> Dict[str, Any]:
        """Gather all data needed for the report."""
        return {
            "original_query": await context.recall("original_query", ""),
            "processed_query": await context.recall("processed_query", ""),
            "query_analysis": await context.recall("query_analysis", ""),
            "research_plan": await context.recall("research_plan", {}),
            "arxiv_papers": await context.recall("arxiv_papers", []),
            "web_results": await context.recall("web_results", []),
            "semantic_scholar_papers": await context.recall("semantic_scholar_papers", []),
            "pdf_analysis": await context.recall("pdf_analysis", {}),
            "fact_check_results": await context.recall("fact_check_results", {}),
            "validated_citations": await context.recall("validated_citations", {}),
            "quality_report": await context.recall("quality_report", {}),
            "visualizations": await context.recall("visualizations", []),
            "all_papers": await self._consolidate_papers(context)
        }
    
    async def _consolidate_papers(self, context) -> List[Dict[str, Any]]:
        """Consolidate all papers from different sources."""
        all_papers = []
        
        arxiv = await context.recall("arxiv_papers", [])
        semantic = await context.recall("semantic_scholar_papers", [])
        
        # Add source field and consolidate
        for paper in arxiv:
            paper["source"] = "arXiv"
            all_papers.append(paper)
        
        for paper in semantic:
            paper["source"] = "Semantic Scholar"
            all_papers.append(paper)
        
        # Sort by relevance/year
        all_papers.sort(key=lambda p: (
            p.get("year", 0),
            p.get("citation_count", 0)
        ), reverse=True)
        
        return all_papers
    
    async def _generate_academic_report(self, data: Dict[str, Any], context) -> str:
        """Generate an academic-style research report."""
        llm = context.get_resource("llm")
        
        # Build report sections
        sections = []
        
        # Title and metadata
        sections.append(f"# Research Report: {data['original_query']}")
        sections.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d')}")
        sections.append(f"**Quality Score**: {data['quality_report'].get('overall_score', 0):.2f}/1.0")
        sections.append(f"**Sources Analyzed**: {len(data['all_papers'])}")
        sections.append("\n---\n")
        
        # Table of Contents
        if self.include_toc:
            sections.append("## Table of Contents")
            sections.append("1. [Executive Summary](#executive-summary)")
            sections.append("2. [Introduction](#introduction)")
            sections.append("3. [Methodology](#methodology)")
            sections.append("4. [Key Findings](#key-findings)")
            sections.append("5. [Detailed Analysis](#detailed-analysis)")
            sections.append("6. [Conclusions](#conclusions)")
            sections.append("7. [References](#references)")
            if self.include_appendices:
                sections.append("8. [Appendices](#appendices)")
            sections.append("\n")
        
        # Executive Summary
        sections.append("## Executive Summary")
        summary_prompt = f"""Write a concise executive summary (200-300 words) for this research:

Query: {data['original_query']}
Key Papers: {len(data['all_papers'])}
Main Findings: {json.dumps(data.get('pdf_analysis', {}).get('key_findings', []), indent=2)}

Executive Summary:"""
        
        summary = await llm.generate(summary_prompt)
        sections.append(summary.content)
        sections.append("\n")
        
        # Introduction
        sections.append("## Introduction")
        intro_prompt = f"""Write an introduction for this research report:

Research Topic: {data['original_query']}
Analysis: {data['query_analysis']}

Introduction (150-200 words):"""
        
        intro = await llm.generate(intro_prompt)
        sections.append(intro.content)
        sections.append("\n")
        
        # Methodology
        sections.append("## Methodology")
        sections.append(await self._generate_methodology_section(data))
        sections.append("\n")
        
        # Key Findings
        sections.append("## Key Findings")
        findings = await self._generate_findings_section(data, llm)
        sections.append(findings)
        sections.append("\n")
        
        # Detailed Analysis
        sections.append("## Detailed Analysis")
        analysis = await self._generate_detailed_analysis(data, llm)
        sections.append(analysis)
        sections.append("\n")
        
        # Conclusions
        sections.append("## Conclusions")
        conclusions = await self._generate_conclusions(data, llm)
        sections.append(conclusions)
        sections.append("\n")
        
        # References
        if self.include_references:
            sections.append("## References")
            references = await self._format_references(data)
            sections.append(references)
            sections.append("\n")
        
        # Appendices
        if self.include_appendices:
            sections.append("## Appendices")
            appendices = await self._generate_appendices(data)
            sections.append(appendices)
        
        return "\n".join(sections)
    
    async def _generate_methodology_section(self, data: Dict[str, Any]) -> str:
        """Generate methodology section."""
        plan = data.get("research_plan", {})
        
        methodology = []
        methodology.append("This research employed a systematic approach with the following components:")
        methodology.append("")
        methodology.append(f"**Search Strategy**: {plan.get('strategy', 'exploratory_search')}")
        methodology.append(f"**Data Sources**: {', '.join(plan.get('sources', []))}")
        methodology.append(f"**Search Terms**: {', '.join(plan.get('search_terms', [])[:5])}")
        methodology.append("")
        methodology.append("**Inclusion Criteria**:")
        for criterion in plan.get("inclusion_criteria", [])[:3]:
            methodology.append(f"- {criterion}")
        methodology.append("")
        methodology.append("**Quality Assurance**: Fact-checking and citation validation were performed on all sources.")
        
        return "\n".join(methodology)
    
    async def _generate_findings_section(self, data: Dict[str, Any], llm) -> str:
        """Generate key findings section."""
        findings_prompt = f"""Synthesize the key findings from this research:

Papers analyzed: {len(data['all_papers'])}
PDF findings: {json.dumps(data.get('pdf_analysis', {}).get('key_findings', []))}
Top papers: {json.dumps([p['title'] for p in data['all_papers'][:5]])}

Generate 3-5 key findings with brief explanations:"""
        
        findings = await llm.generate(findings_prompt)
        return findings.content
    
    async def _generate_detailed_analysis(self, data: Dict[str, Any], llm) -> str:
        """Generate detailed analysis section."""
        # Group papers by theme/topic
        analysis_prompt = f"""Provide a detailed analysis of the research findings:

Research question: {data['original_query']}
Number of sources: {len(data['all_papers'])}
Fact-check results: {data['fact_check_results'].get('verified_claims', [])}

Organize the analysis by themes or key areas. Include:
1. Current state of research
2. Emerging trends
3. Gaps in knowledge
4. Controversies or debates

Detailed analysis (500-700 words):"""
        
        analysis = await llm.generate(analysis_prompt)
        
        # Add visualizations if available
        if data.get("visualizations"):
            analysis_text = analysis.content + "\n\n### Data Visualizations\n\n"
            for viz in data["visualizations"]:
                analysis_text += f"**{viz['title']}**: See Appendix {chr(65 + data['visualizations'].index(viz))}\n"
            return analysis_text
        
        return analysis.content
    
    async def _generate_conclusions(self, data: Dict[str, Any], llm) -> str:
        """Generate conclusions section."""
        conclusion_prompt = f"""Write conclusions for this research report:

Original query: {data['original_query']}
Papers reviewed: {len(data['all_papers'])}
Quality score: {data['quality_report'].get('overall_score', 0):.2f}
Recommendations: {data['quality_report'].get('recommendations', [])}

Include:
1. Summary of main findings
2. Implications of the research
3. Recommendations for future research
4. Limitations of this review

Conclusions (300-400 words):"""
        
        conclusions = await llm.generate(conclusion_prompt)
        return conclusions.content
    
    async def _format_references(self, data: Dict[str, Any]) -> str:
        """Format references section."""
        citations = data.get("validated_citations", {}).get("formatted_citations", [])
        
        if not citations:
            return "No references available."
        
        references = []
        for i, citation in enumerate(citations[:30], 1):  # Limit to 30 references
            references.append(f"{i}. {citation['formatted']}")
        
        return "\n".join(references)
    
    async def _generate_appendices(self, data: Dict[str, Any]) -> str:
        """Generate appendices section."""
        appendices = []
        
        # Appendix A: Search Queries
        appendices.append("### Appendix A: Search Queries Used")
        appendices.append(f"- Primary query: {data['original_query']}")
        appendices.append(f"- Search terms: {', '.join(data['research_plan'].get('search_terms', []))}")
        appendices.append("")
        
        # Appendix B: Quality Report
        appendices.append("### Appendix B: Quality Assurance Report")
        quality = data['quality_report']
        appendices.append(f"- Overall Score: {quality.get('overall_score', 0):.2f}")
        appendices.append(f"- Source Diversity: {quality['checks'].get('source_diversity', 0):.2f}")
        appendices.append(f"- Minimum Sources Met: {quality['checks'].get('minimum_sources', False)}")
        appendices.append(f"- Fact Check Passed: {quality['checks'].get('fact_check_passed', False)}")
        appendices.append("")
        
        # Appendix C+: Visualizations
        if data.get("visualizations"):
            for i, viz in enumerate(data["visualizations"]):
                appendices.append(f"### Appendix {chr(67 + i)}: {viz['title']}")
                appendices.append(f"Type: {viz['type']}")
                appendices.append(f"Data points: {len(viz.get('data', {}).get('data', []))}")
                appendices.append("")
        
        return "\n".join(appendices)
    
    async def _generate_executive_summary(self, data: Dict[str, Any], context) -> str:
        """Generate an executive summary format report."""
        llm = context.get_resource("llm")
        
        summary_prompt = f"""Create an executive summary for this research:

Topic: {data['original_query']}
Sources reviewed: {len(data['all_papers'])}
Key findings: {json.dumps(data.get('pdf_analysis', {}).get('key_findings', []))}

Format as a 1-page executive summary with:
1. Overview (1 paragraph)
2. Key Findings (3-5 bullets)
3. Implications (2-3 bullets)
4. Recommendations (2-3 bullets)

Executive Summary:"""
        
        summary = await llm.generate(summary_prompt)
        
        return f"""# Executive Summary: {data['original_query']}

**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Sources Analyzed**: {len(data['all_papers'])}

{summary.content}

---
*This executive summary is based on {len(data['all_papers'])} sources analyzed using the Entity Research Assistant.*"""
    
    async def _generate_blog_post(self, data: Dict[str, Any], context) -> str:
        """Generate a blog post format report."""
        llm = context.get_resource("llm")
        
        blog_prompt = f"""Write an engaging blog post about this research:

Topic: {data['original_query']}
Key findings: {json.dumps(data.get('pdf_analysis', {}).get('key_findings', [])[:3])}

Write in an accessible, engaging style for a general audience.
Include:
1. Catchy introduction
2. Why this matters
3. Key discoveries
4. What it means for the future
5. Call to action

Blog post (600-800 words):"""
        
        blog_post = await llm.generate(blog_prompt)
        
        return f"""# {data['original_query']}: What the Latest Research Tells Us

*{datetime.now().strftime('%B %d, %Y')}*

{blog_post.content}

---

**Sources**: This article is based on an analysis of {len(data['all_papers'])} recent research papers and publications.

**Want to learn more?** Check out the full academic report or explore the primary sources listed in our comprehensive bibliography."""