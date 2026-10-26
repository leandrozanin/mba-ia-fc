from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CODEX_SKILL_ROOT = REPOSITORY_ROOT / ".agents" / "skills" / "refactor-arch"
CLAUDE_SKILL_ROOT = REPOSITORY_ROOT / ".claude" / "skills" / "refactor-arch"
PROJECTS = ("code-smells-project", "ecommerce-api-legacy", "task-manager-api")


class RefactorArchSkillAssetsTests(unittest.TestCase):
    def test_skill_declares_the_three_ordered_phases_and_confirmation_gate(self):
        content = (CODEX_SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("name: refactor-arch", content)
        analysis = content.index("Fase 1")
        audit = content.index("Fase 2")
        refactor = content.index("Fase 3")
        self.assertLess(analysis, audit)
        self.assertLess(audit, refactor)
        self.assertIn("pare e pe", content.lower())
        self.assertIn("aprov", content.lower())

    def test_skill_links_all_required_reference_areas(self):
        content = (CODEX_SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        references = CODEX_SKILL_ROOT / "references"

        for filename in (
            "project-analysis.md",
            "anti-pattern-catalog.md",
            "audit-report-template.md",
            "mvc-guidelines.md",
            "refactoring-playbook.md",
        ):
            with self.subTest(filename=filename):
                self.assertTrue((references / filename).is_file())
                self.assertIn(filename, content)

    def test_catalog_has_eight_patterns_and_all_severities(self):
        catalog = (CODEX_SKILL_ROOT / "references" / "anti-pattern-catalog.md").read_text(encoding="utf-8")
        rows = re.findall(r"\|\s*(CRITICAL|HIGH|MEDIUM|LOW)\s*\|", catalog)

        self.assertGreaterEqual(len(rows), 8)
        self.assertEqual(set(rows), {"CRITICAL", "HIGH", "MEDIUM", "LOW"})
        self.assertRegex(catalog.lower(), r"deprecated|obsolet")

    def test_playbook_has_eight_before_after_transformations(self):
        playbook = (CODEX_SKILL_ROOT / "references" / "refactoring-playbook.md").read_text(encoding="utf-8")
        patterns = re.findall(r"^### Transforma.* \d+", playbook, re.MULTILINE)

        self.assertGreaterEqual(len(patterns), 8)
        self.assertGreaterEqual(len(re.findall(r"Antes", playbook, re.IGNORECASE)), 8)
        self.assertGreaterEqual(len(re.findall(r"Depois", playbook, re.IGNORECASE)), 8)

    def test_claude_and_codex_skills_are_mirrored_at_the_repository_root(self):
        codex_files = {
            path.relative_to(CODEX_SKILL_ROOT): path.read_bytes()
            for path in CODEX_SKILL_ROOT.rglob("*")
            if path.is_file()
        }
        claude_files = {
            path.relative_to(CLAUDE_SKILL_ROOT): path.read_bytes()
            for path in CLAUDE_SKILL_ROOT.rglob("*")
            if path.is_file()
        }

        self.assertEqual(codex_files, claude_files)

    def test_each_project_has_an_identical_copy_of_the_claude_skill(self):
        expected = {
            path.relative_to(CLAUDE_SKILL_ROOT): path.read_bytes()
            for path in CLAUDE_SKILL_ROOT.rglob("*")
            if path.is_file()
        }
        for project in PROJECTS:
            copy_root = REPOSITORY_ROOT / "projects" / project / ".claude" / "skills" / "refactor-arch"
            with self.subTest(project=project):
                actual = {
                    path.relative_to(copy_root): path.read_bytes()
                    for path in copy_root.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(actual, expected)

    def test_audit_reports_exist_with_required_names(self):
        for number in (1, 2, 3):
            with self.subTest(report=number):
                report = REPOSITORY_ROOT / "reports" / f"audit-project-{number}.md"
                content = report.read_text(encoding="utf-8")
                self.assertRegex(content, r"\[(CRITICAL|HIGH)\]")
                self.assertGreaterEqual(len(re.findall(r"^### \[(CRITICAL|HIGH|MEDIUM|LOW)\]", content, re.MULTILINE)), 5)
                self.assertIn("Gate da Fase 2", content)


if __name__ == "__main__":
    unittest.main()
