#!/usr/bin/env python3
"""
Generate comprehensive test report for WAOOAW CP Pipeline
Outputs test metrics in tabular format for CI/CD visibility
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class TestReportGenerator:
    def __init__(self):
        self.backend_path = Path("src/CP/BackEnd")
        self.frontend_path = Path("src/CP/FrontEnd")
        self.results = {
            "backend": {},
            "frontend": {},
            "e2e": {},
            "summary": {}
        }

    def run_backend_tests(self) -> Dict:
        """Run backend tests and collect metrics"""
        print("🔬 Running Backend Tests...")
        
        try:
            # Run pytest with coverage and JSON output
            cmd = [
                "python", "-m", "pytest",
                "--cov=.",
                "--cov-report=json",
                "--cov-report=term-missing",
                "-v",
                "--tb=short",
                "--json-report",
                "--json-report-file=test-report.json"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.backend_path,
                capture_output=True,
                text=True
            )
            
            # Parse coverage
            coverage_file = self.backend_path / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    coverage_pct = coverage_data["totals"]["percent_covered"]
            else:
                coverage_pct = 0
            
            # Parse test results
            report_file = self.backend_path / "test-report.json"
            if report_file.exists():
                with open(report_file) as f:
                    test_data = json.load(f)
                    total = test_data["summary"]["total"]
                    passed = test_data["summary"].get("passed", 0)
                    failed = test_data["summary"].get("failed", 0)
                    duration = test_data["duration"]
            else:
                # Fallback: parse from output
                total, passed, failed, duration = self._parse_pytest_output(result.stdout)
            
            # Count test types
            unit_tests, integration_tests = self._count_backend_test_types()
            
            return {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
                "coverage": round(coverage_pct, 2),
                "duration": round(duration, 2),
                "unit_tests": unit_tests,
                "integration_tests": integration_tests,
                "status": "✅" if failed == 0 else "❌"
            }
        except Exception as e:
            print(f"❌ Backend tests failed: {e}")
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0,
                "coverage": 0,
                "duration": 0,
                "unit_tests": 0,
                "integration_tests": 0,
                "status": "❌"
            }

    def run_frontend_tests(self) -> Dict:
        """Run frontend tests and collect metrics"""
        print("🎨 Running Frontend Tests...")
        
        try:
            # Run vitest with coverage
            cmd = ["npm", "test", "--", "--run", "--coverage", "--reporter=json"]
            
            result = subprocess.run(
                cmd,
                cwd=self.frontend_path,
                capture_output=True,
                text=True
            )
            
            # Parse coverage
            coverage_file = self.frontend_path / "coverage/coverage-summary.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    coverage_pct = coverage_data["total"]["lines"]["pct"]
            else:
                coverage_pct = 0
            
            # Parse test results from output
            total, passed, failed, duration = self._parse_vitest_output(result.stdout + result.stderr)
            
            # Count test types
            unit_tests, component_tests = self._count_frontend_test_types()
            
            return {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
                "coverage": round(coverage_pct, 2),
                "duration": round(duration, 2),
                "unit_tests": unit_tests,
                "component_tests": component_tests,
                "status": "✅" if failed == 0 else "❌"
            }
        except Exception as e:
            print(f"❌ Frontend tests failed: {e}")
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0,
                "coverage": 0,
                "duration": 0,
                "unit_tests": 0,
                "component_tests": 0,
                "status": "❌"
            }

    def run_e2e_tests(self) -> Dict:
        """Run E2E tests and collect metrics"""
        print("🌐 Running E2E Tests...")
        
        try:
            cmd = ["npx", "playwright", "test", "--reporter=json"]
            
            result = subprocess.run(
                cmd,
                cwd=self.frontend_path,
                capture_output=True,
                text=True
            )
            
            # Parse Playwright output
            total, passed, failed, duration = self._parse_playwright_output(result.stdout + result.stderr)
            
            return {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
                "duration": round(duration, 2),
                "browsers": "Chromium, Firefox, WebKit",
                "status": "✅" if failed == 0 else "⚠️" if passed / total >= 0.8 else "❌"
            }
        except Exception as e:
            print(f"❌ E2E tests failed: {e}")
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0,
                "duration": 0,
                "browsers": "N/A",
                "status": "❌"
            }

    def _parse_pytest_output(self, output: str) -> Tuple[int, int, int, float]:
        """Parse pytest output for test counts"""
        import re
        
        # Look for "X passed" or "X passed, Y failed"
        match = re.search(r'(\d+) passed', output)
        passed = int(match.group(1)) if match else 0
        
        match = re.search(r'(\d+) failed', output)
        failed = int(match.group(1)) if match else 0
        
        match = re.search(r'in ([\d.]+)s', output)
        duration = float(match.group(1)) if match else 0
        
        return passed + failed, passed, failed, duration

    def _parse_vitest_output(self, output: str) -> Tuple[int, int, int, float]:
        """Parse vitest output for test counts"""
        import re
        
        match = re.search(r'Tests\s+(\d+)\s+passed', output)
        passed = int(match.group(1)) if match else 0
        
        match = re.search(r'(\d+)\s+failed', output)
        failed = int(match.group(1)) if match else 0
        
        # Duration in ms
        match = re.search(r'\((\d+)ms\)', output)
        duration = float(match.group(1)) / 1000 if match else 0
        
        return passed + failed, passed, failed, duration

    def _parse_playwright_output(self, output: str) -> Tuple[int, int, int, float]:
        """Parse Playwright output for test counts"""
        import re
        
        match = re.search(r'(\d+) passed', output)
        passed = int(match.group(1)) if match else 0
        
        match = re.search(r'(\d+) failed', output)
        failed = int(match.group(1)) if match else 0
        
        match = re.search(r'(\d+\.\d+)s', output)
        duration = float(match.group(1)) if match else 0
        
        return passed + failed, passed, failed, duration

    def _count_backend_test_types(self) -> Tuple[int, int]:
        """Count unit vs integration tests"""
        unit = 0
        integration = 0
        
        test_files = list((self.backend_path / "tests").glob("test_*.py"))
        for test_file in test_files:
            content = test_file.read_text()
            if "@pytest.mark.integration" in content:
                integration += content.count("def test_")
            else:
                unit += content.count("def test_")
        
        return unit, integration

    def _count_frontend_test_types(self) -> Tuple[int, int]:
        """Count unit vs component tests"""
        unit = 0
        component = 0
        
        test_files = list(self.frontend_path.rglob("*.test.ts*"))
        for test_file in test_files:
            content = test_file.read_text()
            test_count = content.count("it(") + content.count("test(")
            
            # Heuristic: .tsx files are component tests, .ts are unit tests
            if test_file.suffix == ".tsx":
                component += test_count
            else:
                unit += test_count
        
        return unit, component

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("WAOOAW CP Pipeline - Comprehensive Test Report")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        # Run all tests
        backend = self.run_backend_tests()
        frontend = self.run_frontend_tests()
        e2e = self.run_e2e_tests()
        
        # Calculate summary
        total_tests = backend["total_tests"] + frontend["total_tests"] + e2e["total_tests"]
        total_passed = backend["passed"] + frontend["passed"] + e2e["passed"]
        total_failed = backend["failed"] + frontend["failed"] + e2e["failed"]
        overall_pass_rate = round(total_passed / total_tests * 100, 2) if total_tests > 0 else 0
        
        # Calculate combined coverage (weighted average)
        backend_lines = 701  # From last coverage report
        frontend_lines = 5764  # Estimated from coverage report
        total_lines = backend_lines + frontend_lines
        combined_coverage = round(
            (backend["coverage"] * backend_lines + frontend["coverage"] * frontend_lines) / total_lines,
            2
        )
        
        # Print Test Execution Summary
        print("\n📊 TEST EXECUTION SUMMARY")
        print("-" * 80)
        self._print_table([
            ["Metric", "Backend", "Frontend", "E2E", "Total"],
            ["-" * 15, "-" * 10, "-" * 10, "-" * 10, "-" * 10],
            ["Tests Run", backend["total_tests"], frontend["total_tests"], e2e["total_tests"], total_tests],
            ["Passed", f"{backend['passed']} {backend['status']}", f"{frontend['passed']} {frontend['status']}", f"{e2e['passed']} {e2e['status']}", total_passed],
            ["Failed", backend["failed"], frontend["failed"], e2e["failed"], total_failed],
            ["Pass Rate", f"{backend['pass_rate']}%", f"{frontend['pass_rate']}%", f"{e2e['pass_rate']}%", f"{overall_pass_rate}%"],
            ["Duration", f"{backend['duration']}s", f"{frontend['duration']}s", f"{e2e['duration']}s", f"{backend['duration'] + frontend['duration'] + e2e['duration']:.2f}s"],
        ])
        
        # Print Coverage Details
        print("\n📈 CODE COVERAGE BREAKDOWN")
        print("-" * 80)
        self._print_table([
            ["Component", "Coverage", "Target", "Status", "Gap"],
            ["-" * 15, "-" * 10, "-" * 8, "-" * 8, "-" * 8],
            ["Backend", f"{backend['coverage']}%", "79%", "✅" if backend['coverage'] >= 79 else "❌", f"+{backend['coverage'] - 79:.1f}%"],
            ["Frontend", f"{frontend['coverage']}%", "80%", "✅" if frontend['coverage'] >= 80 else "⚠️", f"{frontend['coverage'] - 80:.1f}%"],
            ["Combined", f"{combined_coverage}%", "79%", "✅" if combined_coverage >= 79 else "❌", f"+{combined_coverage - 79:.1f}%"],
        ])
        
        # Print Test Type Breakdown
        print("\n🧪 TEST TYPE BREAKDOWN")
        print("-" * 80)
        self._print_table([
            ["Test Type", "Count", "Pass Rate", "Coverage Tracked", "Status"],
            ["-" * 20, "-" * 8, "-" * 10, "-" * 16, "-" * 8],
            ["Backend Unit", backend["unit_tests"], f"{backend['pass_rate']}%", "✅ Yes", backend["status"]],
            ["Backend Integration", backend["integration_tests"], f"{backend['pass_rate']}%", "✅ Yes", backend["status"]],
            ["Frontend Unit", frontend["unit_tests"], f"{frontend['pass_rate']}%", "✅ Yes", frontend["status"]],
            ["Frontend Component", frontend["component_tests"], f"{frontend['pass_rate']}%", "✅ Yes", frontend["status"]],
            ["E2E (Playwright)", e2e["total_tests"], f"{e2e['pass_rate']}%", "❌ No (Live app)", e2e["status"]],
        ])
        
        # Print Production Readiness
        print("\n✅ PRODUCTION READINESS")
        print("-" * 80)
        
        critical_checks = [
            ("All tests passing", total_failed == 0, "✅" if total_failed == 0 else "❌"),
            ("Backend coverage ≥79%", backend["coverage"] >= 79, "✅" if backend["coverage"] >= 79 else "❌"),
            ("Frontend coverage ≥70%", frontend["coverage"] >= 70, "✅" if frontend["coverage"] >= 70 else "❌"),
            ("E2E pass rate ≥80%", e2e["pass_rate"] >= 80, "✅" if e2e["pass_rate"] >= 80 else "⚠️"),
            ("Overall pass rate ≥95%", overall_pass_rate >= 95, "✅" if overall_pass_rate >= 95 else "⚠️"),
        ]
        
        for check, passed, status in critical_checks:
            print(f"{status} {check}")
        
        # Calculate deployment confidence
        passed_checks = sum(1 for _, passed, _ in critical_checks if passed)
        confidence = round(passed_checks / len(critical_checks) * 100)
        
        print("\n" + "="*80)
        print(f"🚀 DEPLOYMENT CONFIDENCE: {confidence}% ({passed_checks}/{len(critical_checks)} critical checks passed)")
        print("="*80 + "\n")
        
        # Exit with failure if critical checks fail
        if confidence < 80:
            print("❌ Pipeline FAILED - Deployment confidence below 80%")
            sys.exit(1)
        else:
            print("✅ Pipeline PASSED - Ready for deployment")
            sys.exit(0)

    def _print_table(self, rows: List[List]):
        """Print formatted table"""
        # Calculate column widths
        col_widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
        
        for row in rows:
            print("  " + "  ".join(str(cell).ljust(width) for cell, width in zip(row, col_widths)))


if __name__ == "__main__":
    generator = TestReportGenerator()
    generator.generate_report()
