"""Pipeline analyzer for optimization hints and performance insights."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext
from entity.workflow.executor import WorkflowExecutor
from entity.workflow.workflow import Workflow


@dataclass
class PipelineOptimizationHint:
    """Optimization hint for pipeline execution."""

    stage: str
    plugin: Optional[str]
    hint_type: str
    reason: str
    impact: str
    conditions: Dict[str, Any]


@dataclass
class PipelineAnalysisResult:
    """Result of pipeline analysis."""

    total_stages: int
    total_plugins: int
    skippable_stages: List[str]
    skippable_plugins: List[str]
    stage_dependencies: Dict[str, Set[str]]
    optimization_hints: List[PipelineOptimizationHint]
    estimated_savings_ms: float


class PipelineAnalyzer:
    """Analyze pipeline for optimization opportunities."""

    def __init__(self, workflow: Workflow, executor: WorkflowExecutor):
        """Initialize the analyzer.

        Args:
            workflow: The workflow to analyze
            executor: The workflow executor
        """
        self.workflow = workflow
        self.executor = executor
        self._analysis_cache: Dict[str, PipelineAnalysisResult] = {}

    def analyze(
        self, context: Optional[PluginContext] = None
    ) -> PipelineAnalysisResult:
        """Analyze the pipeline for optimization opportunities.

        Args:
            context: Optional context for conditional analysis

        Returns:
            Analysis result with optimization hints
        """
        total_stages = len(self.executor._ORDER)
        total_plugins = sum(
            len(self.workflow.plugins_for(stage)) for stage in self.executor._ORDER
        )

        skippable_stages = []
        skippable_plugins = []

        for stage in self.executor._ORDER:
            plugins = self.workflow.plugins_for(stage)

            all_skippable = True
            for plugin in plugins:
                if context and not plugin.should_execute(context):
                    plugin_name = f"{stage}.{plugin.__class__.__name__}"
                    skippable_plugins.append(plugin_name)
                else:
                    all_skippable = False

            if all_skippable and len(plugins) > 0:
                skippable_stages.append(stage)

        hints = self._generate_optimization_hints(
            skippable_stages, skippable_plugins, context
        )

        estimated_savings = self._estimate_savings(skippable_stages, skippable_plugins)

        return PipelineAnalysisResult(
            total_stages=total_stages,
            total_plugins=total_plugins,
            skippable_stages=skippable_stages,
            skippable_plugins=skippable_plugins,
            stage_dependencies=self.executor._stage_dependencies.copy(),
            optimization_hints=hints,
            estimated_savings_ms=estimated_savings,
        )

    def _generate_optimization_hints(
        self,
        skippable_stages: List[str],
        skippable_plugins: List[str],
        context: Optional[PluginContext],
    ) -> List[PipelineOptimizationHint]:
        """Generate optimization hints based on analysis.

        Args:
            skippable_stages: List of stages that can be skipped
            skippable_plugins: List of plugins that can be skipped
            context: Optional context for conditional hints

        Returns:
            List of optimization hints
        """
        hints = []

        for stage in skippable_stages:
            hints.append(
                PipelineOptimizationHint(
                    stage=stage,
                    plugin=None,
                    hint_type="skip",
                    reason=f"All plugins in {stage} stage are skippable",
                    impact=(
                        "high"
                        if stage in {WorkflowExecutor.THINK, WorkflowExecutor.DO}
                        else "medium"
                    ),
                    conditions={"context_provided": context is not None},
                )
            )

        plugin_skip_frequency = {}
        for plugin_name in skippable_plugins:
            stage, name = plugin_name.split(".", 1)
            if name not in plugin_skip_frequency:
                plugin_skip_frequency[name] = 0
            plugin_skip_frequency[name] += 1

        for plugin_name, frequency in plugin_skip_frequency.items():
            if frequency >= 2:
                hints.append(
                    PipelineOptimizationHint(
                        stage="multiple",
                        plugin=plugin_name,
                        hint_type="reorder",
                        reason=f"Plugin {plugin_name} frequently skipped",
                        impact="medium",
                        conditions={"skip_frequency": frequency},
                    )
                )

        for stage in self.executor._ORDER:
            deps = self.executor._stage_dependencies.get(stage, set())
            if len(deps) == 0 and stage != WorkflowExecutor.INPUT:
                hints.append(
                    PipelineOptimizationHint(
                        stage=stage,
                        plugin=None,
                        hint_type="parallel",
                        reason=f"Stage {stage} has no dependencies",
                        impact="low",
                        conditions={"dependencies": list(deps)},
                    )
                )

        for stage in [WorkflowExecutor.PARSE, WorkflowExecutor.THINK]:
            if stage not in skippable_stages:
                hints.append(
                    PipelineOptimizationHint(
                        stage=stage,
                        plugin=None,
                        hint_type="cache",
                        reason=f"Stage {stage} results could be cached",
                        impact="medium",
                        conditions={"cacheable": True},
                    )
                )

        return hints

    def _estimate_savings(
        self, skippable_stages: List[str], skippable_plugins: List[str]
    ) -> float:
        """Estimate time savings from skipping stages/plugins.

        Args:
            skippable_stages: List of stages that can be skipped
            skippable_plugins: List of plugins that can be skipped

        Returns:
            Estimated time savings in milliseconds
        """
        STAGE_OVERHEAD_MS = 5.0
        PLUGIN_OVERHEAD_MS = 10.0

        stage_savings = len(skippable_stages) * STAGE_OVERHEAD_MS
        plugin_savings = len(skippable_plugins) * PLUGIN_OVERHEAD_MS

        return stage_savings + plugin_savings

    def get_stage_skip_recommendations(self, context: PluginContext) -> Dict[str, bool]:
        """Get recommendations for which stages to skip.

        Args:
            context: The current plugin context

        Returns:
            Dictionary mapping stage names to skip recommendations
        """
        recommendations = {}

        all_stages = self.executor._ORDER + [self.executor.ERROR]

        for stage in all_stages:
            plugins = self.workflow.plugins_for(stage)

            would_execute = any(plugin.should_execute(context) for plugin in plugins)

            can_skip = not would_execute and self.executor._can_skip_stage(
                stage, context
            )

            recommendations[stage] = can_skip

        return recommendations

    def validate_skip_conditions(self, plugin: Plugin) -> List[str]:
        """Validate that a plugin's skip conditions are properly configured.

        Args:
            plugin: The plugin to validate

        Returns:
            List of validation warnings/errors
        """
        warnings = []

        if not hasattr(plugin, "skip_conditions"):
            warnings.append(
                f"Plugin {plugin.__class__.__name__} has no skip_conditions defined"
            )
        elif not plugin.skip_conditions:
            warnings.append(
                f"Plugin {plugin.__class__.__name__} has empty skip_conditions"
            )
        else:
            for i, condition in enumerate(plugin.skip_conditions):
                if not callable(condition):
                    warnings.append(
                        f"Skip condition {i} in {plugin.__class__.__name__} is not callable"
                    )

        if hasattr(plugin, "should_execute"):
            method = getattr(plugin, "should_execute")
            if method.__module__ != "entity.plugins.base":
                warnings.append(
                    f"Plugin {plugin.__class__.__name__} overrides should_execute() - "
                    "ensure it calls super().should_execute() if using skip_conditions"
                )

        return warnings
