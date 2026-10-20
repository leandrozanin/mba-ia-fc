from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1] / "projects" / "code-smells-project" / ".agents" / "skills" / "refactor-arch"


class RefactorArchSkillAssetsTests(unittest.TestCase):
    def test_skill_declares_the_three_ordered_phases_and_confirmation_gate(self):
        content = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("name: refactor-arch", content)
        analysis = content.index("Fase 1")
        audit = content.index("Fase 2")
        refactor = content.index("Fase 3")
        self.assertLess(analysis, audit)
        self.assertLess(audit, refactor)
        self.assertIn("pare e pe", content.lower())
        self.assertIn("aprov", content.lower())

    def test_skill_links_all_required_reference_areas(self):
        content = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        references = SKILL_ROOT / "references"

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
        catalog = (SKILL_ROOT / "references" / "anti-pattern-catalog.md").read_text(encoding="utf-8")
        rows = re.findall(r"\|\s*(CRITICAL|HIGH|MEDIUM|LOW)\s*\|", catalog)

        self.assertGreaterEqual(len(rows), 8)
        self.assertEqual(set(rows), {"CRITICAL", "HIGH", "MEDIUM", "LOW"})
        self.assertRegex(catalog.lower(), r"deprecated|obsolet")

    def test_playbook_has_eight_before_after_transformations(self):
        playbook = (SKILL_ROOT / "references" / "refactoring-playbook.md").read_text(encoding="utf-8")
        patterns = re.findall(r"^### Transforma.* \d+", playbook, re.MULTILINE)

        self.assertGreaterEqual(len(patterns), 8)
        self.assertGreaterEqual(len(re.findall(r"Antes", playbook, re.IGNORECASE)), 8)
        self.assertGreaterEqual(len(re.findall(r"Depois", playbook, re.IGNORECASE)), 8)


if __name__ == "__main__":
    unittest.main()
