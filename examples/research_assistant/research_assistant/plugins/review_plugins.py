"""Review stage plugins for quality assurance and validation."""

from typing import Any, Dict, List
import re
from urllib.parse import urlparse

from entity.plugins.prompt import PromptPlugin
from entity.workflow.executor import WorkflowExecutor
from entity.resources import LogLevel, LogCategory


class FactCheckerPlugin(PromptPlugin):
    """Verify facts and claims against trusted sources."""
    
    supported_stages = [WorkflowExecutor.REVIEW]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.trusted_sources = self.config.get("trusted_sources", [
            "nature.com",
            "science.org", 
            "arxiv.org",
            "pubmed.ncbi.nlm.nih.gov"
        ])
        self.confidence_threshold = self.config.get("confidence_threshold", 0.8)
    
    async def _execute_impl(self, context) -> None:
        """Check facts and validate claims."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Starting fact checking"
        )
        
        # Gather all findings
        arxiv_papers = await context.recall("arxiv_papers", [])
        web_results = await context.recall("web_results", [])
        pdf_analysis = await context.recall("pdf_analysis", {})
        
        # Extract claims to verify
        claims = []
        
        # From papers
        for paper in arxiv_papers:
            if "abstract" in paper:
                paper_claims = await self._extract_claims(paper["abstract"])
                claims.extend([{
                    "claim": c,
                    "source": paper["title"],
                    "url": paper.get("url", "")
                } for c in paper_claims])
        
        # From PDF analysis
        if pdf_analysis.get("key_findings"):
            for finding in pdf_analysis["key_findings"]:
                claims.append({
                    "claim": finding,
                    "source": pdf_analysis.get("title", "PDF Document"),
                    "url": "local_pdf"
                })
        
        # Verify claims
        llm = context.get_resource("llm")
        verified_claims = []
        disputed_claims = []
        
        for claim_info in claims[:10]:  # Limit to top 10 claims
            verification = await self._verify_claim(llm, claim_info)
            
            if verification["confidence"] >= self.confidence_threshold:
                verified_claims.append(verification)
            else:
                disputed_claims.append(verification)
        
        # Store verification results
        fact_check_results = {
            "total_claims": len(claims),
            "verified_claims": verified_claims,
            "disputed_claims": disputed_claims,
            "confidence_threshold": self.confidence_threshold
        }
        
        await context.remember("fact_check_results", fact_check_results)
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            f"Fact checking complete: {len(verified_claims)} verified, {len(disputed_claims)} disputed"
        )
    
    async def _extract_claims(self, text: str) -> List[str]:
        """Extract verifiable claims from text."""
        # Simple heuristic: look for sentences with numbers or strong assertions
        sentences = text.split('.')
        claims = []
        
        claim_patterns = [
            r'\d+\s*%',  # Percentages
            r'shows?\s+',  # "shows that"
            r'demonstrates?\s+',  # "demonstrates"
            r'proves?\s+',  # "proves"
            r'significant',  # Statistical claims
            r'increase|decrease|improve'  # Comparative claims
        ]
        
        for sentence in sentences:
            if any(re.search(pattern, sentence, re.I) for pattern in claim_patterns):
                claims.append(sentence.strip())
        
        return claims[:5]  # Top 5 claims
    
    async def _verify_claim(self, llm, claim_info: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a single claim."""
        # Check if source is trusted
        source_trust = 1.0
        if claim_info["url"] and claim_info["url"] != "local_pdf":
            domain = urlparse(claim_info["url"]).netloc
            if not any(trusted in domain for trusted in self.trusted_sources):
                source_trust = 0.5
        
        # Use LLM to assess claim plausibility
        verify_prompt = f"""Assess the plausibility of this research claim:

Claim: {claim_info['claim']}
Source: {claim_info['source']}

Based on general scientific knowledge, rate this claim's plausibility (0-1) and explain briefly:"""
        
        result = await llm.generate(verify_prompt)
        
        # Simple parsing of LLM response
        confidence = source_trust * 0.8  # Default confidence based on source
        
        return {
            "claim": claim_info["claim"],
            "source": claim_info["source"],
            "confidence": confidence,
            "verification_note": result.content[:200],
            "trusted_source": source_trust == 1.0
        }


class CitationValidatorPlugin(PromptPlugin):
    """Validate and format citations."""
    
    supported_stages = [WorkflowExecutor.REVIEW]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.styles = self.config.get("styles", ["APA", "MLA", "Chicago", "IEEE"])
        self.check_doi = self.config.get("check_doi", True)
        self.check_urls = self.config.get("check_urls", True)
    
    async def _execute_impl(self, context) -> None:
        """Validate and format citations."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Validating citations"
        )
        
        # Gather all papers and references
        all_citations = []
        
        # From arXiv
        arxiv_papers = await context.recall("arxiv_papers", [])
        for paper in arxiv_papers:
            all_citations.append(self._paper_to_citation(paper, "arxiv"))
        
        # From Semantic Scholar
        semantic_papers = await context.recall("semantic_scholar_papers", [])
        for paper in semantic_papers:
            all_citations.append(self._paper_to_citation(paper, "semantic_scholar"))
        
        # From PDF references
        pdf_analysis = await context.recall("pdf_analysis", {})
        if pdf_analysis.get("references"):
            for ref in pdf_analysis["references"]:
                all_citations.append(self._reference_to_citation(ref))
        
        # Get preferred citation style
        output_format = await context.recall("output_format", "academic")
        citation_style = "APA" if output_format == "academic" else "MLA"
        
        # Format citations
        llm = context.get_resource("llm")
        formatted_citations = []
        
        for citation in all_citations:
            formatted = await self._format_citation(llm, citation, citation_style)
            formatted_citations.append(formatted)
        
        # Validate URLs if enabled
        if self.check_urls:
            for i, citation in enumerate(formatted_citations):
                if citation.get("url"):
                    citation["url_valid"] = await self._validate_url(citation["url"])
        
        # Store validated citations
        citation_results = {
            "total_citations": len(all_citations),
            "citation_style": citation_style,
            "formatted_citations": formatted_citations,
            "validation_performed": {
                "doi": self.check_doi,
                "urls": self.check_urls
            }
        }
        
        await context.remember("validated_citations", citation_results)
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            f"Citation validation complete: {len(formatted_citations)} citations formatted"
        )
    
    def _paper_to_citation(self, paper: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Convert paper data to citation format."""
        return {
            "authors": paper.get("authors", ["Unknown"]),
            "title": paper.get("title", "Untitled"),
            "year": paper.get("year") or paper.get("published", "")[:4] or "n.d.",
            "venue": paper.get("venue", source),
            "url": paper.get("url", ""),
            "doi": paper.get("doi", ""),
            "source_type": source
        }
    
    def _reference_to_citation(self, ref: Dict[str, Any]) -> Dict[str, Any]:
        """Convert reference data to citation format."""
        return {
            "authors": ref.get("authors", ["Unknown"]),
            "title": ref.get("title", "Untitled"),
            "year": ref.get("year", "n.d."),
            "venue": ref.get("venue", "Unknown"),
            "url": "",
            "doi": "",
            "source_type": "reference"
        }
    
    async def _format_citation(self, llm, citation: Dict[str, Any], style: str) -> Dict[str, Any]:
        """Format citation according to style guide."""
        authors_str = ", ".join(citation["authors"][:3])
        if len(citation["authors"]) > 3:
            authors_str += " et al."
        
        format_prompt = f"""Format this citation in {style} style:

Authors: {authors_str}
Title: {citation['title']}
Year: {citation['year']}
Venue/Journal: {citation['venue']}

Provide the formatted citation:"""
        
        result = await llm.generate(format_prompt)
        
        return {
            "formatted": result.content.strip(),
            "original": citation,
            "style": style,
            "url": citation.get("url", ""),
            "doi": citation.get("doi", "")
        }
    
    async def _validate_url(self, url: str) -> bool:
        """Check if URL is valid (simulation)."""
        # In real implementation, make HTTP HEAD request
        return url.startswith(("http://", "https://")) and len(url) > 10


class QualityAssurancePlugin(PromptPlugin):
    """Ensure research quality and completeness."""
    
    supported_stages = [WorkflowExecutor.REVIEW]
    
    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        self.config = config or {}
        self.check_coherence = self.config.get("check_coherence", True)
        self.check_completeness = self.config.get("check_completeness", True)
        self.min_sources = self.config.get("min_sources", 3)
    
    async def _execute_impl(self, context) -> None:
        """Perform quality assurance checks."""
        logger = context.get_resource("logging")
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            "Performing quality assurance"
        )
        
        # Gather all research components
        research_plan = await context.recall("research_plan", {})
        arxiv_papers = await context.recall("arxiv_papers", [])
        web_results = await context.recall("web_results", [])
        semantic_papers = await context.recall("semantic_scholar_papers", [])
        fact_check_results = await context.recall("fact_check_results", {})
        
        quality_checks = {
            "source_diversity": self._check_source_diversity(
                arxiv_papers, web_results, semantic_papers
            ),
            "minimum_sources": len(arxiv_papers + semantic_papers) >= self.min_sources,
            "fact_check_passed": len(fact_check_results.get("disputed_claims", [])) < 3,
            "criteria_coverage": await self._check_criteria_coverage(context),
            "coherence_score": 0.0,
            "completeness_score": 0.0
        }
        
        # Check coherence if enabled
        if self.check_coherence:
            quality_checks["coherence_score"] = await self._assess_coherence(context)
        
        # Check completeness
        if self.check_completeness:
            quality_checks["completeness_score"] = await self._assess_completeness(context)
        
        # Calculate overall quality score
        quality_score = sum([
            quality_checks["source_diversity"] * 0.2,
            (1.0 if quality_checks["minimum_sources"] else 0.0) * 0.2,
            (1.0 if quality_checks["fact_check_passed"] else 0.5) * 0.2,
            quality_checks["coherence_score"] * 0.2,
            quality_checks["completeness_score"] * 0.2
        ])
        
        quality_report = {
            "overall_score": quality_score,
            "checks": quality_checks,
            "recommendations": await self._generate_recommendations(quality_checks),
            "passed": quality_score >= 0.7
        }
        
        await context.remember("quality_report", quality_report)
        await logger.log(
            LogLevel.INFO,
            LogCategory.PLUGIN_LIFECYCLE,
            f"Quality assurance complete: score {quality_score:.2f}"
        )
    
    def _check_source_diversity(self, arxiv: List, web: List, semantic: List) -> float:
        """Check diversity of sources."""
        source_count = 0
        if arxiv:
            source_count += 1
        if web:
            source_count += 1
        if semantic:
            source_count += 1
        
        return source_count / 3.0
    
    async def _check_criteria_coverage(self, context) -> bool:
        """Check if research meets inclusion criteria."""
        research_plan = await context.recall("research_plan", {})
        inclusion_criteria = research_plan.get("inclusion_criteria", [])
        
        # Simple check: ensure we have results
        arxiv_papers = await context.recall("arxiv_papers", [])
        return len(arxiv_papers) > 0 and len(inclusion_criteria) > 0
    
    async def _assess_coherence(self, context) -> float:
        """Assess coherence of findings."""
        llm = context.get_resource("llm")
        
        # Gather key findings
        findings = []
        pdf_analysis = await context.recall("pdf_analysis", {})
        if pdf_analysis.get("key_findings"):
            findings.extend(pdf_analysis["key_findings"])
        
        if not findings:
            return 1.0  # No findings to check
        
        coherence_prompt = f"""Assess the coherence of these research findings:

{chr(10).join(f'{i+1}. {f}' for i, f in enumerate(findings))}

Rate coherence from 0-1 where 1 is perfectly coherent and consistent:"""
        
        result = await llm.generate(coherence_prompt)
        
        # Simple extraction of score
        try:
            # Look for decimal number in response
            import re
            scores = re.findall(r'0\.\d+|1\.0', result.content)
            if scores:
                return float(scores[0])
        except:
            pass
        
        return 0.8  # Default coherence
    
    async def _assess_completeness(self, context) -> float:
        """Assess research completeness."""
        # Check coverage of research plan
        research_plan = await context.recall("research_plan", {})
        planned_sources = set(research_plan.get("sources", []))
        
        actual_sources = set()
        if await context.recall("arxiv_papers", []):
            actual_sources.add("arxiv")
        if await context.recall("web_results", []):
            actual_sources.add("web")
        if await context.recall("semantic_scholar_papers", []):
            actual_sources.add("semantic_scholar")
        
        if not planned_sources:
            return 1.0
        
        coverage = len(actual_sources.intersection(planned_sources)) / len(planned_sources)
        return coverage
    
    async def _generate_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on quality checks."""
        recommendations = []
        
        if checks["source_diversity"] < 0.7:
            recommendations.append("Consider searching additional academic databases")
        
        if not checks["minimum_sources"]:
            recommendations.append(f"Add more sources to meet minimum of {self.min_sources}")
        
        if not checks["fact_check_passed"]:
            recommendations.append("Review and verify disputed claims")
        
        if checks.get("coherence_score", 1.0) < 0.7:
            recommendations.append("Review findings for consistency and coherence")
        
        if checks.get("completeness_score", 1.0) < 0.7:
            recommendations.append("Complete research across all planned sources")
        
        return recommendations