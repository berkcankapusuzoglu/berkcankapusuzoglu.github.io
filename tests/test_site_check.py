import subprocess
import json
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.site_check import (
    collect_html_routes,
    validate_expected_routes,
    validate_html_document,
)


class SiteCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def document(self, body):
        path = self.root / 'page.html'
        path.write_text(body, encoding='utf-8')
        return validate_html_document(path)

    def test_collect_routes_preserves_nested_html_paths(self):
        (self.root / 'index.html').touch()
        (self.root / 'path').mkdir()
        (self.root / 'path/file.html').touch()
        (self.root / 'path/index.html').touch()
        (self.root / 'index.json').touch()
        self.assertEqual(collect_html_routes(self.root),
                         {'/', '/path/file.html', '/path/index.html'})

    def test_missing_legacy_route_is_reported(self):
        expected = self.root / 'urls.txt'
        expected.write_text('/\n/publications/legacy.html\n', encoding='utf-8')
        self.assertEqual(validate_expected_routes({'/'}, expected),
                         ['Missing route: /publications/legacy.html'])

    def test_zero_h1_is_reported(self):
        self.assertIn('Expected exactly one H1; found 0', self.document('<main></main>'))

    def test_multiple_h1_is_reported(self):
        self.assertIn('Expected exactly one H1; found 2',
                      self.document('<main><h1>A</h1><h1>B</h1></main>'))

    def test_missing_main_is_reported(self):
        self.assertIn('Missing main landmark', self.document('<h1>A</h1>'))

    def test_template_content_cannot_supply_structural_landmarks(self):
        errors = self.document('<template><main><h1>A</h1></main></template>')
        self.assertIn('Expected exactly one H1; found 0', errors)
        self.assertIn('Missing main landmark', errors)

    def test_hidden_subtrees_cannot_supply_structural_landmarks(self):
        for marker in ('hidden', 'aria-hidden="true"'):
            with self.subTest(marker=marker):
                errors = self.document(f'<section {marker}><main><h1>A</h1></main></section>')
                self.assertIn('Expected exactly one H1; found 0', errors)
                self.assertIn('Missing main landmark', errors)

    def test_hidden_headings_do_not_create_a_duplicate_h1(self):
        self.assertEqual(self.document('<main><h1>A</h1><section hidden><h1>B</h1>'
                                       '</section><template><h1>C</h1></template></main>'), [])

    def test_heading_requires_meaningful_accessible_text(self):
        for content in (' ', '<span hidden>Hidden heading</span>',
                        '<span aria-hidden="true">Hidden heading</span>'):
            with self.subTest(content=content):
                self.assertIn('H1 missing accessible text',
                              self.document(f'<main><h1>{content}</h1></main>'))

    def test_image_without_alt_is_reported(self):
        self.assertIn('Image missing useful alt text: photo.png',
                      self.document('<main><h1>A</h1><img src="photo.png"></main>'))

    def test_empty_alt_requires_explicit_decorative_marker(self):
        self.assertIn('Image missing useful alt text: line.svg',
                      self.document('<main><h1>A</h1><img src="line.svg" alt=""></main>'))

    def test_decorative_image_must_still_have_alt_attribute(self):
        self.assertIn('Image missing useful alt text: line.svg', self.document(
            '<main><h1>A</h1><img src="line.svg" aria-hidden="true"></main>'))

    def test_valid_decorative_image_is_accepted(self):
        self.assertEqual(self.document(
            '<main><h1>A</h1><img src="line.svg" alt="" aria-hidden="true"></main>'), [])

    def test_empty_icon_link_is_reported(self):
        self.assertIn('Link missing accessible text: /contact.html', self.document(
            '<main><h1>A</h1><a href="/contact.html"><i></i></a></main>'))

    def test_hidden_link_text_does_not_supply_a_name(self):
        self.assertIn('Link missing accessible text: /contact.html', self.document(
            '<main><h1>A</h1><a href="/contact.html"><span aria-hidden="true">X</span></a></main>'))

    def test_accessible_link_names_are_accepted(self):
        self.assertEqual(self.document('<main><h1>A</h1>'
            '<a href="/a">Read <span>the paper</span></a>'
            '<a href="/b" aria-label="GitHub"><i></i></a>'
            '<a href="/c"><img src="photo.png" alt="Portrait"></a>'
            '<a href="/d" aria-labelledby="link-label"><i></i></a>'
            '<span id="link-label">Contact</span></main>'), [])

    def test_explicitly_referenced_hidden_text_can_name_a_link(self):
        self.assertEqual(self.document('<main><h1>A</h1>'
            '<a href="/paper" aria-labelledby="label"><i></i></a>'
            '<span id="label" hidden>Read paper</span></main>'), [])

    def test_label_inside_hidden_ancestor_can_name_a_link(self):
        self.assertEqual(self.document('<main><h1>A</h1>'
            '<a href="/paper" aria-labelledby="label"><i></i></a>'
            '<div hidden><span id="label">Read paper</span></div></main>'), [])

    def test_invalid_label_reference_falls_back_to_aria_label(self):
        self.assertEqual(self.document('<main><h1>A</h1>'
            '<a href="/paper" aria-labelledby="missing" aria-label="Read paper">'
            '<i></i></a></main>'), [])

    def test_hidden_descendant_of_visible_label_does_not_supply_text(self):
        self.assertIn('Link missing accessible text: /paper', self.document(
            '<main><h1>A</h1><a href="/paper" aria-labelledby="label"><i></i></a>'
            '<span id="label"><span hidden>Read paper</span></span></main>'))

    def test_cli_reports_errors_and_fails(self):
        (self.root / 'index.html').write_text('<h1>A</h1>', encoding='utf-8')
        expected = self.root / 'urls.txt'
        expected.write_text('/\n/old.html\n', encoding='utf-8')
        result = subprocess.run([sys.executable, 'scripts/site_check.py',
            '--public', str(self.root), '--expected', str(expected)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Missing route: /old.html', result.stdout)
        self.assertIn('/: Missing main landmark', result.stdout)

    def run_cli(self, body, expected='/', allowlist=None):
        (self.root / 'index.html').write_text(body, encoding='utf-8')
        urls = self.root / 'urls.txt'
        urls.write_text(expected, encoding='utf-8')
        command = [sys.executable, 'scripts/site_check.py', '--public',
                   str(self.root), '--expected', str(urls)]
        if allowlist is not None:
            exceptions = self.root / 'allowlist.json'
            exceptions.write_text(json.dumps(allowlist), encoding='utf-8')
            command.extend(['--allowlist', str(exceptions)])
        return subprocess.run(command, capture_output=True, text=True)

    def test_cli_accepts_valid_output(self):
        result = self.run_cli('<main><h1>A</h1></main>')
        self.assertEqual(result.returncode, 0)

    def test_exact_allowlist_entry_accepts_known_finding(self):
        result = self.run_cli('<h1>A</h1>', allowlist=['/: Missing main landmark'])
        self.assertEqual(result.returncode, 0)

    def test_allowlist_does_not_suppress_missing_routes(self):
        result = self.run_cli('<h1>A</h1>', '/\n/old.html',
                              ['/: Missing main landmark', 'Missing route: /old.html'])
        self.assertEqual(result.returncode, 1)
        self.assertIn('Missing route: /old.html', result.stdout)

    def test_allowlist_limits_occurrences_of_each_finding(self):
        result = self.run_cli('<main><h1>A</h1><a href="/x"></a><a href="/x"></a></main>',
                              allowlist=['/: Link missing accessible text: /x'])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count('/: Link missing accessible text: /x'), 1)

    def test_stale_allowlist_entries_fail(self):
        result = self.run_cli('<main><h1>A</h1></main>',
                              allowlist=['/: Missing main landmark'])
        self.assertEqual(result.returncode, 1)
        self.assertIn('Stale allowlist finding', result.stdout)

    def test_allowlist_requires_a_list_of_strings(self):
        result = self.run_cli('<main><h1>A</h1></main>', allowlist={})
        self.assertEqual(result.returncode, 1)
        self.assertIn('Allowlist must be a JSON list of strings', result.stdout)


if __name__ == '__main__':
    unittest.main()
