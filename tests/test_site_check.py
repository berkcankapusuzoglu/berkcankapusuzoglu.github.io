import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urljoin, urlparse

from scripts.site_check import (
    collect_html_routes,
    validate_expected_routes,
    validate_html_document,
    _Document,
    _accessible_name,
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

    def run_cli(self, body, expected='/'):
        (self.root / 'index.html').write_text(body, encoding='utf-8')
        (self.root / 'assets').mkdir(exist_ok=True)
        (self.root / 'assets/main.css').write_text(':focus-visible { outline: 3px solid blue; }', encoding='utf-8')
        urls = self.root / 'urls.txt'
        urls.write_text(expected, encoding='utf-8')
        command = [sys.executable, 'scripts/site_check.py', '--public',
                   str(self.root), '--expected', str(urls)]
        return subprocess.run(command, capture_output=True, text=True)

    def test_cli_accepts_valid_output(self):
        result = self.run_cli('''<a href="#main-content">Skip</a><header><nav aria-label="Primary">
          <button data-nav-toggle aria-controls="menu"></button><ul id="menu" data-nav-menu></ul>
          </nav></header><main id="main-content"><h1>A</h1></main><footer></footer>
          <link rel="canonical" href="https://example.org/"><meta name="description" content="Page">
          <link rel="stylesheet" href="/assets/main.css">''')
        self.assertEqual(result.returncode, 0)


class GeneratedShellTests(unittest.TestCase):
    """Exercise generated pages: removing a shell feature must break its contract."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.public = Path(cls.temp.name)
        result = subprocess.run(['hugo', '--minify', '--panicOnWarning',
                                 '--printPathWarnings', '--destination', str(cls.public)],
                                capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        cls.pages = {}
        for route in ('index.html', 'publications.html',
                      'publications/2024_sarwar_neurips_efficient_natural_language_and_speech_processing_workshop.html',
                      '404.html'):
            document = _Document()
            document.feed((cls.public / route).read_text(encoding='utf-8'))
            cls.pages[route] = document

    def visible(self, document):
        return [node for node in document.nodes if not node['hidden'] and not node['in_template']]

    def test_representative_pages_have_one_meaningful_h1(self):
        for route, document in self.pages.items():
            with self.subTest(route=route):
                headings = [n for n in self.visible(document) if n['tag'] == 'h1']
                self.assertEqual(len(headings), 1)
                self.assertTrue(_accessible_name(headings[0], {}).strip())

    def test_skip_link_targets_visible_main_content(self):
        for route, document in self.pages.items():
            with self.subTest(route=route):
                nodes = self.visible(document)
                self.assertTrue(any(n['tag'] == 'a' and n['attrs'].get('href') == '#main-content'
                                    for n in nodes), 'Missing skip link')
                self.assertTrue(any(n['tag'] == 'main' and n['attrs'].get('id') == 'main-content'
                                    for n in nodes), 'Missing main-content landmark')

    def test_primary_navigation_has_a_label_and_real_mobile_button(self):
        for route, document in self.pages.items():
            with self.subTest(route=route):
                nodes = self.visible(document)
                self.assertTrue(any(n['tag'] == 'nav' and n['attrs'].get('aria-label') == 'Primary'
                                    for n in nodes), 'Missing labelled primary navigation')
                toggles = [n for n in nodes if 'data-nav-toggle' in n['attrs']]
                self.assertEqual(len(toggles), 1, 'Missing mobile navigation toggle')
                self.assertEqual(toggles[0]['tag'], 'button')
                menus = [n for n in nodes if 'data-nav-menu' in n['attrs']]
                self.assertEqual(len(menus), 1)
                self.assertEqual(toggles[0]['attrs'].get('aria-controls'), menus[0]['attrs'].get('id'))

    def test_every_link_has_an_accessible_name(self):
        for route, document in self.pages.items():
            ids = {n['attrs']['id']: n for n in document.nodes if n['attrs'].get('id')}
            for node in document.nodes:
                if node['tag'] == 'a' and 'href' in node['attrs']:
                    with self.subTest(route=route, href=node['attrs']['href']):
                        self.assertTrue(_accessible_name(node, ids).strip())

    def test_canonical_and_description_are_nonempty(self):
        for route, document in self.pages.items():
            with self.subTest(route=route):
                canonicals = [n for n in document.nodes if n['tag'] == 'link'
                              and n['attrs'].get('rel') == 'canonical']
                self.assertEqual(len(canonicals), 1)
                self.assertTrue(canonicals[0]['attrs'].get('href', '').startswith(
                    'https://berkcankapusuzoglu.github.io/'))
                self.assertTrue(any(n['tag'] == 'meta' and n['attrs'].get('name') == 'description'
                                    and n['attrs'].get('content', '').strip() for n in document.nodes))

    def test_linked_local_stylesheet_has_keyboard_visible_focus(self):
        for route, document in self.pages.items():
            with self.subTest(route=route):
                styles = [n['attrs'].get('href', '') for n in document.nodes if n['tag'] == 'link'
                          and n['attrs'].get('rel') == 'stylesheet']
                local = [href for href in styles if not urlparse(href).netloc]
                self.assertTrue(local, 'Missing local stylesheet')
                css = ''.join((self.public / urlparse(urljoin('/' + route, href)).path.lstrip('/'))
                              .read_text(encoding='utf-8') for href in local)
                self.assertIn(':focus-visible', css)

    def test_no_remote_runtime_assets_or_wowchemy(self):
        for route, document in self.pages.items():
            for node in document.nodes:
                if node['tag'] == 'script' or (node['tag'] == 'link' and
                        node['attrs'].get('rel') in {'stylesheet', 'preconnect', 'preload'}):
                    asset = node['attrs'].get('src', node['attrs'].get('href', ''))
                    with self.subTest(route=route, asset=asset):
                        self.assertFalse(urlparse(asset).netloc, 'Remote runtime asset')
                        self.assertNotIn('wowchemy', asset.lower())


if __name__ == '__main__':
    unittest.main()
