#!/usr/bin/env python3
"""
Verification script for entity-plugin-gpt-oss package completeness.
Story 1: Verify entity-plugin-gpt-oss Package Completeness

This script creates a comparison matrix and verifies that the separate
entity-plugin-gpt-oss package contains all necessary functionality.
"""

import ast
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict


def get_file_hash(file_path: Path) -> str:
    """Get SHA256 hash of file contents."""
    if not file_path.exists():
        return "FILE_NOT_FOUND"
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def analyze_python_file(file_path: Path) -> Dict:
    """Analyze Python file for classes, functions, and imports."""
    if not file_path.exists():
        return {"error": "File not found"}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        classes = []
        functions = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        return {
            "classes": sorted(classes),
            "functions": sorted(functions),
            "imports": sorted(imports),
            "lines": len(content.split("\n")),
            "hash": hashlib.sha256(content.encode()).hexdigest(),
        }
    except Exception as e:
        return {"error": str(e)}


class GPTOSSPackageVerifier:
    """Verifies entity-plugin-gpt-oss package completeness."""

    EXPECTED_PLUGINS = [
        "ReasoningTracePlugin",
        "StructuredOutputPlugin",
        "DeveloperOverridePlugin",
        "AdaptiveReasoningPlugin",
        "GPTOSSToolOrchestrator",
        "MultiChannelAggregatorPlugin",
        "HarmonySafetyFilterPlugin",
        "FunctionSchemaRegistryPlugin",
        "ReasoningAnalyticsDashboardPlugin",
    ]

    PLUGIN_FILES = [
        "reasoning_trace.py",
        "structured_output.py",
        "developer_override.py",
        "adaptive_reasoning.py",
        "native_tools.py",
        "multi_channel_aggregator.py",
        "harmony_safety_filter.py",
        "function_schema_registry.py",
        "reasoning_analytics_dashboard.py",
    ]

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.main_gpt_oss_dir = self.base_dir / "src" / "entity" / "plugins" / "gpt_oss"
        self.package_dir = (
            self.base_dir / "entity-plugin-gpt-oss" / "src" / "entity_plugin_gpt_oss"
        )

        self.comparison_matrix = {}
        self.discrepancies = []
        self.verification_results = {}

    def create_comparison_matrix(self) -> Dict:
        """Create comparison matrix for all plugins."""
        print("Creating comparison matrix for GPT-OSS plugins...")

        matrix = {
            "plugin_files": {},
            "summary": {
                "total_plugins": len(self.PLUGIN_FILES),
                "main_repo_files": 0,
                "package_files": 0,
                "matching_files": 0,
                "different_files": 0,
            },
        }

        for plugin_file in self.PLUGIN_FILES:
            main_file = self.main_gpt_oss_dir / plugin_file
            package_file = self.package_dir / plugin_file

            main_analysis = analyze_python_file(main_file)
            package_analysis = analyze_python_file(package_file)

            # Check if files exist
            main_exists = main_file.exists()
            package_exists = package_file.exists()

            if main_exists:
                matrix["summary"]["main_repo_files"] += 1
            if package_exists:
                matrix["summary"]["package_files"] += 1

            # Compare content
            if main_exists and package_exists:
                content_match = main_analysis.get("hash") == package_analysis.get(
                    "hash"
                )
                if content_match:
                    matrix["summary"]["matching_files"] += 1
                else:
                    matrix["summary"]["different_files"] += 1

            matrix["plugin_files"][plugin_file] = {
                "main_repo": {"exists": main_exists, "analysis": main_analysis},
                "package": {"exists": package_exists, "analysis": package_analysis},
                "content_identical": main_exists
                and package_exists
                and main_analysis.get("hash") == package_analysis.get("hash"),
            }

        self.comparison_matrix = matrix
        return matrix

    def verify_plugin_exports(self) -> Dict:
        """Verify __init__.py properly exports all plugin classes."""
        print("Verifying plugin exports...")

        # Check main repo __init__.py
        main_init = self.main_gpt_oss_dir / "__init__.py"
        package_init = self.package_dir / "__init__.py"

        main_init_analysis = analyze_python_file(main_init)
        package_init_analysis = analyze_python_file(package_init)

        # Extract __all__ from package init
        package_all = []
        if package_init.exists():
            try:
                with open(package_init, "r") as f:
                    content = f.read()
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "__all__":
                                if isinstance(node.value, ast.List):
                                    package_all = [
                                        elt.s
                                        for elt in node.value.elts
                                        if isinstance(elt, ast.Str)
                                    ]
                                elif isinstance(node.value, ast.Constant):
                                    package_all = (
                                        node.value.value
                                        if isinstance(node.value.value, list)
                                        else []
                                    )
            except Exception as e:
                print(f"Error parsing package __init__.py: {e}")

        results = {
            "main_init_exists": main_init.exists(),
            "package_init_exists": package_init.exists(),
            "main_init_analysis": main_init_analysis,
            "package_init_analysis": package_init_analysis,
            "expected_plugins": self.EXPECTED_PLUGINS,
            "package_exports": package_all,
            "missing_exports": [
                p for p in self.EXPECTED_PLUGINS if p not in package_all
            ],
            "extra_exports": [p for p in package_all if p not in self.EXPECTED_PLUGINS],
        }

        return results

    def verify_dependencies(self) -> Dict:
        """Verify package dependencies are properly declared."""
        print("Verifying package dependencies...")

        pyproject_path = self.base_dir / "entity-plugin-gpt-oss" / "pyproject.toml"

        if not pyproject_path.exists():
            return {"error": "pyproject.toml not found"}

        try:
            with open(pyproject_path, "r") as f:
                content = f.read()

            # Simple parsing - look for dependencies section
            lines = content.split("\n")
            dependencies = []
            in_deps = False

            for line in lines:
                line = line.strip()
                if line == "[tool.poetry.dependencies]":
                    in_deps = True
                    continue
                elif in_deps and line.startswith("["):
                    in_deps = False
                    continue
                elif in_deps and "=" in line:
                    dep = line.split("=")[0].strip()
                    if dep and dep != "python":
                        dependencies.append(dep)

            return {
                "dependencies_found": dependencies,
                "has_entity_core": "entity-core" in dependencies,
                "has_pydantic": "pydantic" in dependencies,
                "pyproject_exists": True,
            }

        except Exception as e:
            return {"error": f"Error parsing pyproject.toml: {e}"}

    def test_package_installation(self) -> Dict:
        """Test if package can be installed via pip."""
        print("Testing package installation...")

        package_dir = self.base_dir / "entity-plugin-gpt-oss"

        if not package_dir.exists():
            return {"error": "Package directory not found"}

        # Try to build the package
        try:
            result = subprocess.run(
                ["python", "-m", "build"],
                cwd=package_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            build_success = result.returncode == 0

            # Check if dist directory was created
            dist_dir = package_dir / "dist"
            dist_files = list(dist_dir.glob("*")) if dist_dir.exists() else []

            return {
                "build_successful": build_success,
                "build_output": result.stdout,
                "build_errors": result.stderr,
                "dist_files": [f.name for f in dist_files],
                "has_wheel": any(f.name.endswith(".whl") for f in dist_files),
                "has_sdist": any(f.name.endswith(".tar.gz") for f in dist_files),
            }

        except subprocess.TimeoutExpired:
            return {"error": "Build process timed out"}
        except FileNotFoundError:
            return {"error": "Build tool not available (pip install build)"}
        except Exception as e:
            return {"error": f"Build failed: {e}"}

    def run_verification(self) -> Dict:
        """Run complete verification process."""
        print("=" * 60)
        print("GPT-OSS Package Completeness Verification")
        print("=" * 60)

        results = {
            "comparison_matrix": self.create_comparison_matrix(),
            "plugin_exports": self.verify_plugin_exports(),
            "dependencies": self.verify_dependencies(),
            "installation_test": self.test_package_installation(),
        }

        # Generate summary
        matrix = results["comparison_matrix"]
        exports = results["plugin_exports"]

        summary = {
            "total_plugins_expected": len(self.EXPECTED_PLUGINS),
            "plugin_files_in_main": matrix["summary"]["main_repo_files"],
            "plugin_files_in_package": matrix["summary"]["package_files"],
            "identical_files": matrix["summary"]["matching_files"],
            "different_files": matrix["summary"]["different_files"],
            "missing_exports": len(exports["missing_exports"]),
            "extra_exports": len(exports["extra_exports"]),
            "dependencies_ok": results["dependencies"].get("has_entity_core", False),
            "can_build": results["installation_test"].get("build_successful", False),
        }

        results["summary"] = summary

        # Determine overall status
        all_files_present = matrix["summary"]["package_files"] == len(self.PLUGIN_FILES)
        no_missing_exports = len(exports["missing_exports"]) == 0
        deps_ok = results["dependencies"].get("has_entity_core", False)
        can_build = results["installation_test"].get("build_successful", False)

        results["verification_passed"] = (
            all_files_present and no_missing_exports and deps_ok and can_build
        )

        self.verification_results = results
        return results

    def print_report(self):
        """Print verification report."""
        if not self.verification_results:
            print("No verification results available. Run verification first.")
            return

        results = self.verification_results
        summary = results["summary"]

        print("\n" + "=" * 60)
        print("VERIFICATION REPORT")
        print("=" * 60)

        print("\n📊 PLUGIN FILES ANALYSIS:")
        print(f"   Expected plugins: {summary['total_plugins_expected']}")
        print(f"   Files in main repo: {summary['plugin_files_in_main']}")
        print(f"   Files in package: {summary['plugin_files_in_package']}")
        print(f"   Identical files: {summary['identical_files']}")
        print(f"   Different files: {summary['different_files']}")

        print("\n📦 PACKAGE EXPORTS:")
        exports = results["plugin_exports"]
        print(f"   Missing exports: {len(exports['missing_exports'])}")
        if exports["missing_exports"]:
            print(f"   → Missing: {exports['missing_exports']}")
        print(f"   Extra exports: {len(exports['extra_exports'])}")
        if exports["extra_exports"]:
            print(f"   → Extra: {exports['extra_exports']}")

        print("\n🔧 DEPENDENCIES:")
        deps = results["dependencies"]
        print(f"   Has entity-core: {deps.get('has_entity_core', False)}")
        print(f"   Has pydantic: {deps.get('has_pydantic', False)}")

        print("\n🏗️  INSTALLATION TEST:")
        install = results["installation_test"]
        print(f"   Can build: {install.get('build_successful', False)}")
        if install.get("build_errors"):
            print(f"   Build errors: {install['build_errors'][:200]}...")

        print("\n✅ OVERALL STATUS:")
        status = "PASSED" if results["verification_passed"] else "FAILED"
        print(f"   Verification: {status}")

        if not results["verification_passed"]:
            print("\n⚠️  ISSUES FOUND:")
            if summary["plugin_files_in_package"] < len(self.PLUGIN_FILES):
                print("   - Missing plugin files in package")
            if summary["missing_exports"] > 0:
                print("   - Missing plugin exports in __init__.py")
            if not deps.get("has_entity_core", False):
                print("   - Missing entity-core dependency")
            if not install.get("build_successful", False):
                print("   - Package build failed")


def main():
    """Main entry point."""
    verifier = GPTOSSPackageVerifier()
    results = verifier.run_verification()
    verifier.print_report()

    # Return appropriate exit code
    sys.exit(0 if results["verification_passed"] else 1)


if __name__ == "__main__":
    main()
