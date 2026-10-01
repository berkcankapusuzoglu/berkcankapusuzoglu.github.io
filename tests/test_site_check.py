import subprocess
import sys
import tempfile
import unittest
import re
import json
import html
from pathlib import Path
from urllib.parse import urljoin, urlparse

from scripts.site_check import (
    collect_html_routes,
    validate_expected_routes,
    validate_html_document,
    _Document,
    _accessible_name,
    _accessible_text,
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

    def test_arbitrary_meta_refresh_does_not_bypass_structural_checks(self):
        errors = self.document('<meta http-equiv="refresh" content="0;url=/">')
        self.assertIn('Expected exactly one H1; found 0', errors)

    def test_exact_hugo_paginator_redirect_shape_is_accepted(self):
        route = '/about/page/1.html'
        target = 'https://berkcankapusuzoglu.github.io/about.html'
        redirect = (self.root / 'about/page/1.html')
        redirect.parent.mkdir(parents=True)
        redirect.write_text(f'''<!doctype html><html lang="en-us"><head><title>{target}</title>
          <link rel="canonical" href="{target}"><meta name="robots" content="noindex">
          <meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}">
          </head></html>''', encoding='utf-8')
        self.assertEqual(validate_html_document(redirect, route), [])

    def test_new_local_renderer_paginator_redirect_routes_are_recognized(self):
        routes = ('/leadership/page/1.html', '/research/page/1.html',
                  '/writing/page/1.html')
        for route in routes:
            target_path = route.removesuffix('page/1.html').rstrip('/') + '.html'
            target = f'https://berkcankapusuzoglu.github.io{target_path}'
            redirect = self.root / route.lstrip('/')
            redirect.parent.mkdir(parents=True, exist_ok=True)
            redirect.write_text(f'''<!doctype html><html lang="en-us"><head><title>{target}</title>
              <link rel="canonical" href="{target}"><meta name="robots" content="noindex">
              <meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}">
              </head></html>''', encoding='utf-8')
            with self.subTest(route=route):
                self.assertEqual(validate_html_document(redirect, route), [])

    def test_local_news_redirect_routes_are_recognized(self):
        redirects = {'/news.html': '/writing.html',
                     '/news/job/job.html': '/about.html',
                     '/news/personal/personal.html': '/research/efficient-model-systems.html'}
        for route, target_path in redirects.items():
            target = f'https://berkcankapusuzoglu.github.io{target_path}'
            redirect = self.root / route.lstrip('/')
            redirect.parent.mkdir(parents=True, exist_ok=True)
            redirect.write_text(f'''<!doctype html><html lang="en-us"><head><title>{target}</title>
              <link rel="canonical" href="{target}"><meta name="robots" content="noindex">
              <meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}">
              </head></html>''', encoding='utf-8')
            with self.subTest(route=route):
                self.assertEqual(validate_html_document(redirect, route), [])

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

    def run_cli(self, body, expected='/', css=':focus-visible { outline: 3px solid blue; }'):
        (self.root / 'index.html').write_text(body, encoding='utf-8')
        (self.root / 'assets').mkdir(exist_ok=True)
        (self.root / 'assets/main.css').write_text(css, encoding='utf-8')
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

    def test_cli_rejects_remote_css_resource_syntax(self):
        shell = '''<a href="#main-content">Skip</a><nav aria-label="Primary"><button data-nav-toggle aria-controls="menu"></button><ul id="menu" data-nav-menu></ul></nav><main id="main-content"><h1>A</h1></main><link rel="canonical" href="https://example.org/"><meta name="description" content="Page"><link rel="stylesheet" href="/assets/main.css">'''
        for css in (":focus-visible{outline:2px solid blue}a{background:url('https://example.org/font.woff2')}",
                    ':focus-visible{outline:2px solid blue}a{background:url( https://example.org/font.woff2)}',
                    ':focus-visible{outline:2px solid blue}a{background:url("http://example.org/font.woff2")}',
                    ":focus-visible{outline:2px solid blue}@import 'https://example.org/theme.css';"):
            with self.subTest(css=css):
                result = self.run_cli(shell, css=css)
                self.assertEqual(result.returncode, 1)
                self.assertIn('Remote', result.stdout)


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
        cls.all_pages = {}
        for path in cls.public.rglob('*.html'):
            document = _Document()
            document.feed(path.read_text(encoding='utf-8'))
            cls.all_pages[path.relative_to(cls.public).as_posix()] = document
        cls.pages = {}
        for route in ('index.html', 'publications.html',
                      'publications/2024_sarwar_neurips_efficient_natural_language_and_speech_processing_workshop.html',
                      'publications/2021_witherell_paul_witherell_berkcan_kapusuzoglu_matthew_sato_sankaran_mahadevan.html',
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

    def test_fresh_build_matches_complete_expected_route_contract(self):
        expected = {line.strip() for line in Path('tests/expected-urls.txt').read_text(
            encoding='utf-8').splitlines() if line.strip()}
        self.assertEqual(collect_html_routes(self.public), expected)

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

    def test_home_and_404_include_all_professional_footer_links(self):
        expected = {'Email', 'GitHub', 'LinkedIn', 'Google Scholar', 'CV (PDF)'}
        for route in ('index.html', '404.html'):
            with self.subTest(route=route):
                document = self.pages[route]
                ids = {n['attrs']['id']: n for n in document.nodes if n['attrs'].get('id')}
                labels = {_accessible_name(n, ids).strip() for n in document.nodes
                          if n['tag'] == 'a'}
                self.assertTrue(expected <= labels, expected - labels)

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

    def test_indexed_pages_have_unique_titles_descriptions_and_open_graph_metadata(self):
        titles = []
        title_routes = {}
        indexable = {}
        for route, document in self.all_pages.items():
            noindex = any(node['tag'] == 'meta' and node['attrs'].get('name') == 'robots' and
                          'noindex' in node['attrs'].get('content', '').lower()
                          for node in document.nodes)
            if not noindex:
                indexable[route] = document
        for route, document in indexable.items():
            with self.subTest(route=route):
                title_node = next((node for node in document.nodes
                                   if node['tag'] == 'title'), None)
                title = _accessible_text(title_node).strip() if title_node else ''
                titles.append(title)
                title_routes.setdefault(title, []).append(route)
                self.assertTrue(title)
                descriptions = [node['attrs'].get('content', '').strip() for node in document.nodes
                                if node['tag'] == 'meta' and node['attrs'].get('name') == 'description']
                self.assertEqual(len(descriptions), 1)
                self.assertGreaterEqual(len(descriptions[0]), 40)
                self.assertNotIn('research and engineering for efficient, reliable language models',
                                 descriptions[0].lower())
                for prop in ('og:title', 'og:description'):
                    self.assertEqual(sum(node['tag'] == 'meta' and
                                     node['attrs'].get('property') == prop for node in document.nodes), 1)
        self.assertEqual(len(titles), len(set(titles)),
                         {title: routes for title, routes in title_routes.items() if len(routes) > 1})

    def test_supported_json_ld_is_valid_and_complete(self):
        for route, document in self.all_pages.items():
            with self.subTest(route=route):
                blocks = [node for node in document.nodes if node['tag'] == 'script' and
                          node['attrs'].get('type') == 'application/ld+json']
                decoded = [json.loads(''.join(child for child in node['children']
                                               if isinstance(child, str))) for node in blocks]
                types = [item.get('@type') for item in decoded]
                self.assertLessEqual(types.count('Person'), 1)
                self.assertLessEqual(types.count('ScholarlyArticle'), 1)
                if route == 'index.html':
                    self.assertEqual(types.count('Person'), 1)
                    person = next(item for item in decoded if item.get('@type') == 'Person')
                    self.assertIn('Berkcan', person.get('name', ''))
                if (route.startswith('publications/') and '/page/' not in route and
                        'data-publication-duplicate' not in str(document.nodes)):
                    self.assertEqual(types.count('ScholarlyArticle'), 1)
                    article = next(item for item in decoded if item.get('@type') == 'ScholarlyArticle')
                    self.assertTrue(article.get('headline'))
                    self.assertTrue(article.get('author'))
                    self.assertTrue(article.get('datePublished'))
                    self.assertTrue(article.get('url'))

    def test_scholarly_article_schema_uses_applicable_relationships(self):
        cases = {
            '2026-critique-guided-distillation.html': {
                'sameAs': ['https://proceedings.mlr.press/v306/kapusuzoglu26a.html'],
                'part_type': 'CreativeWorkSeries',
                'part_name': 'Proceedings of the 43rd International Conference on Machine Learning, PMLR 306',
            },
            '2026-load-balancing-expert-pruning.html': {
                'sameAs': ['https://arxiv.org/abs/2609.04453'],
                'part_type': None,
                'part_name': None,
            },
            '2020_kapusuzoglu_jom.html': {
                'sameAs': ['https://link.springer.com/article/10.1007/s11837-020-04438-4'],
                'part_type': 'Periodical',
                'part_name': 'Journal of Metals',
            },
        }
        for route, expected in cases.items():
            with self.subTest(route=route):
                document = self.all_pages[f'publications/{route}']
                block = next(node for node in document.nodes if node['tag'] == 'script' and
                             node['attrs'].get('type') == 'application/ld+json')
                schema = json.loads(''.join(child for child in block['children']
                                            if isinstance(child, str)))
                visible_text = ' '.join(_accessible_text(node) for node in self.visible(document))
                self.assertEqual(schema.get('sameAs'), expected['sameAs'])
                self.assertNotIn('additionalProperty', schema)
                self.assertNotIn('citation', schema)
                self.assertNotIn('status', schema)
                self.assertIn('preprint' if route.startswith('2026-load') else 'published',
                              visible_text.lower())
                if expected['part_type']:
                    self.assertEqual(schema['isPartOf'], {
                        '@type': expected['part_type'], 'name': expected['part_name']})
                else:
                    self.assertNotIn('isPartOf', schema)

    def test_global_paginator_does_not_create_duplicated_document_routes(self):
        routes = collect_html_routes(self.public)
        for route in ('/page/2.html', '/page/3.html', '/404/page/2.html', '/404/page/3.html'):
            with self.subTest(route=route):
                self.assertNotIn(route, routes)

    def test_home_description_is_not_double_encoded(self):
        document = self.pages['index.html']
        description = next(node['attrs']['content'] for node in document.nodes
                           if node['tag'] == 'meta' and node['attrs'].get('name') == 'description')
        og_description = next(node['attrs']['content'] for node in document.nodes
                              if node['tag'] == 'meta' and
                              node['attrs'].get('property') == 'og:description')
        for value in (description, og_description):
            with self.subTest(value=value):
                self.assertIn("Kapusuzoglu's", html.unescape(value))
                self.assertNotIn('&amp;#39;', value)
        template = (Path(__file__).parents[1] / 'layouts/partials/seo.html').read_text(
            encoding='utf-8')
        self.assertNotIn('| htmlEscape', template)
        self.assertNotIn('.Paginator', template)

    def test_linked_local_stylesheet_has_keyboard_visible_focus(self):
        for route, document in self.pages.items():
            with self.subTest(route=route):
                canonicals = [n for n in document.nodes if n['tag'] == 'link'
                              and n['attrs'].get('rel') == 'canonical']
                canonical_host = urlparse(canonicals[0]['attrs']['href']).netloc
                styles = [n['attrs'].get('href', '') for n in document.nodes if n['tag'] == 'link'
                          and n['attrs'].get('rel') == 'stylesheet']
                local = [href for href in styles if not urlparse(href).netloc or
                         urlparse(href).netloc == canonical_host]
                self.assertTrue(local, 'Missing local stylesheet')
                css = ''.join((self.public / urlparse(urljoin('/' + route, href)).path.lstrip('/'))
                              .read_text(encoding='utf-8') for href in local)
                self.assertIn(':focus-visible', css)

    def test_no_remote_runtime_assets_or_wowchemy(self):
        for route, document in self.pages.items():
            canonicals = [n for n in document.nodes if n['tag'] == 'link'
                          and n['attrs'].get('rel') == 'canonical']
            canonical_host = urlparse(canonicals[0]['attrs']['href']).netloc
            for node in document.nodes:
                if node['tag'] == 'script' or (node['tag'] == 'link' and
                        node['attrs'].get('rel') in {'stylesheet', 'preconnect', 'preload'}):
                    asset = node['attrs'].get('src', node['attrs'].get('href', ''))
                    with self.subTest(route=route, asset=asset):
                        self.assertIn(urlparse(asset).netloc, {'', canonical_host}, 'Remote runtime asset')
                        self.assertNotIn('wowchemy', asset.lower())

    def test_all_legacy_publication_details_retain_front_matter(self):
        pages = sorted((self.public / 'publications').glob('*.html'))
        self.assertGreaterEqual(len(pages), 14)
        for path in pages:
            with self.subTest(page=path.name):
                document = _Document()
                document.feed(path.read_text(encoding='utf-8'))
                if any('data-publication-duplicate' in node['attrs'] for node in document.nodes):
                    self.assertTrue(any(node['attrs'].get('data-canonical-record') ==
                                        '/publications/2020_kapusuzoglu_journal_of_manufacturing_science_and_engineering.html'
                                        for node in document.nodes))
                    continue
                self.assertTrue(any('data-publication-abstract' in node['attrs'] and
                                    _accessible_name(node, {}).strip() for node in document.nodes))
                self.assertTrue(any('data-publication-authors' in node['attrs'] and
                                    _accessible_name(node, {}).strip() for node in document.nodes))
                authors = next(node for node in document.nodes
                               if 'data-publication-authors' in node['attrs'])
                author_text = _accessible_name(authors, {})
                self.assertNotIn('**', author_text)
                self.assertIn('Berkcan Kapusuzoglu', author_text)
                self.assertTrue(any('data-publication-venue' in node['attrs'] and
                                    _accessible_name(node, {}).strip() for node in document.nodes))
                self.assertTrue(any('data-paper-link' in node['attrs'] and
                                    node['attrs'].get('href', '').startswith(('https://', 'http://'))
                                    for node in document.nodes))

    def test_legacy_news_routes_redirect_to_current_context(self):
        targets = {'news.html': '/writing.html', 'news/job/job.html': '/about.html',
                   'news/personal/personal.html': '/research/efficient-model-systems.html'}
        for route, target in targets.items():
            with self.subTest(route=route):
                output = (self.public / route).read_text(encoding='utf-8')
                self.assertIn('name="robots" content="noindex"', output)
                self.assertIn(f'url=https://berkcankapusuzoglu.github.io{target}', output)

    def test_publications_have_complete_unambiguous_metadata(self):
        for path in (self.public / 'publications').glob('*.html'):
            with self.subTest(page=path.name):
                doc = _Document()
                doc.feed(path.read_text(encoding='utf-8'))
                if any('data-publication-duplicate' in node['attrs'] for node in doc.nodes):
                    continue
                text = ' '.join(_accessible_name(n, {}) for n in doc.nodes if n['tag'] == 'main')
                self.assertNotIn('Unknown Journal', text)
                self.assertNotIn('…', text)
                self.assertNotIn('...', text)
                papers = [n for n in doc.nodes if 'data-publication' in n['attrs']]
                self.assertEqual(len(papers), 1)
                self.assertIn(papers[0]['attrs'].get('data-status'), {'published', 'accepted', 'preprint', 'under review'})
                self.assertTrue(papers[0]['attrs'].get('data-topic'))
                venue = [n for n in doc.nodes if 'data-venue-type' in n['attrs']]
                self.assertEqual(len(venue), 1)
                self.assertIn(venue[0]['attrs']['data-venue-type'], {'journal', 'conference', 'workshop', 'proceedings', 'preprint'})
                resources = [n for n in doc.nodes if 'data-paper-link' in n['attrs']]
                self.assertTrue(resources)
                for link in resources:
                    self.assertNotIn(_accessible_name(link, {}).strip().lower(), {'', 'link', 'here', 'paper'})

    def test_duplicate_legacy_record_points_to_canonical_and_is_not_listed(self):
        duplicate_path = (self.public / 'publications' /
                          '2021_witherell_paul_witherell_berkcan_kapusuzoglu_matthew_sato_sankaran_mahadevan.html')
        duplicate = _Document()
        duplicate.feed(duplicate_path.read_text(encoding='utf-8'))
        self.assertTrue(any('data-publication-duplicate' in n['attrs'] for n in duplicate.nodes))
        self.assertTrue(any(n['attrs'].get('data-canonical-record') ==
                            '/publications/2020_kapusuzoglu_journal_of_manufacturing_science_and_engineering.html'
                            for n in duplicate.nodes))
        self.assertTrue(any(n['tag'] == 'a' and n['attrs'].get('href', '').endswith(
                            '2020_kapusuzoglu_journal_of_manufacturing_science_and_engineering.html')
                            for n in duplicate.nodes))
        listing = _Document()
        listing.feed((self.public / 'publications.html').read_text(encoding='utf-8'))
        self.assertFalse(any(n['attrs'].get('href', '').endswith(
            '2021_witherell_paul_witherell_berkcan_kapusuzoglu_matthew_sato_sankaran_mahadevan.html')
            for n in listing.nodes))
        canonical = (Path('content/publications') /
                     '2020_Kapusuzoglu_Journal_of_Manufacturing_Science_and_Engineering' / 'index.md').read_text(encoding='utf-8')
        legacy = (Path('content/publications') /
                  '2021_Witherell_Paul_Witherell_Berkcan_Kapusuzoglu_Matthew_Sato_Sankaran_Mahadevan' / 'index.md').read_text(encoding='utf-8')
        self.assertIn('legacy_duplicate: true', legacy)
        self.assertIn('canonical_record:', legacy)
        self.assertIn('authors: ["Berkcan Kapusuzoglu", "Matthew Sato", "Sankaran Mahadevan", "Paul Witherell"]', canonical)
        self.assertIn('authors: ["Berkcan Kapusuzoglu", "Matthew Sato", "Sankaran Mahadevan", "Paul Witherell"]', legacy)
        self.assertIn('url: "https://asmedigitalcollection.asme.org/manufacturingscience/article-abstract/143/2/021007/1086236"', legacy)
        self.assertIn('date: 2020-01-01', legacy)

    def test_summaries_and_contributions_end_on_complete_phrases(self):
        dangling = re.compile(r'\b(?:the|of|in|to|and|or|but|for|with|at|from|by|over|within|through|using|that|which|as|including|based on|such as)$', re.I)
        for path in Path('content/publications').glob('*/index.md'):
            source = path.read_text(encoding='utf-8')
            for field in ('summary', 'contribution'):
                match = re.search(rf'^{field}:\s*"(.*)"\s*$', source, re.M)
                self.assertIsNotNone(match, f'{path}: missing {field}')
                value = match.group(1)
                self.assertNotRegex(value, r'(?:…|\.\.\.)')
                self.assertRegex(value, r'[.!?]$', f'{path}: incomplete {field}')
                self.assertFalse(dangling.search(value), f'{path}: incomplete {field} ending: {value[-40:]}')

    def test_publication_list_has_unique_sources_and_complete_cards(self):
        doc = self.pages['publications.html']
        cards = [n for n in doc.nodes if 'data-publication-card' in n['attrs']]
        self.assertTrue(cards)
        for card in cards:
            self.assertTrue(card['attrs'].get('data-status'))
            self.assertTrue(card['attrs'].get('data-topic'))
        urls = [n['attrs']['href'] for n in doc.nodes if 'data-paper-link' in n['attrs']]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertGreaterEqual(len(urls), len(cards))

    def test_publication_layout_wraps_long_content(self):
        css = ''.join(p.read_text(encoding='utf-8') for p in self.public.glob('css/main*.css'))
        self.assertRegex(css, r'\.publication[^}]*overflow-wrap:\s*anywhere')

    def test_featured_fixture_uses_explicit_weights_not_dates(self):
        expected = ['2026-critique-guided-distillation',
                    '2026-load-balancing-expert-pruning', '2025-spear-mm']
        selector = Path('layouts/partials/featured-publications.html').read_text(encoding='utf-8')
        self.assertIn('"Params.featured" true', selector)
        self.assertIn('"Params.featured_weight" "asc"', selector)
        selected = []
        for name in expected:
            source = (Path('content/publications') / name / 'index.md').read_text(encoding='utf-8')
            self.assertIn('\nfeatured: true\n', source, msg=name)
            weight = re.search(r'^featured_weight:\s*(\d+)$', source, re.M)
            self.assertIsNotNone(weight, name)
            selected.append((int(weight.group(1)), name))
        self.assertEqual([name for _, name in sorted(selected)], expected)

    def test_404_uses_root_relative_navigation_and_assets(self):
        document = self.pages['404.html']
        links = [node['attrs'].get('href', '') for node in document.nodes
                 if node['tag'] == 'a' or (node['tag'] == 'link' and
                                           node['attrs'].get('rel') == 'stylesheet')]
        scripts = [node['attrs'].get('src', '') for node in document.nodes if node['tag'] == 'script']
        self.assertTrue(links)
        self.assertTrue(all(href.startswith(('/', '#', 'https://', 'mailto:')) for href in links), links)
        self.assertTrue(scripts)
        self.assertTrue(all(src.startswith(('/', 'https://')) for src in scripts))

    def test_mobile_navigation_remains_available_without_javascript(self):
        css_files = list(self.public.glob('css/main*.css'))
        js_files = list(self.public.glob('js/navigation*.js'))
        self.assertEqual(len(css_files), 1)
        self.assertEqual(len(js_files), 1)
        css = css_files[0].read_text(encoding='utf-8')
        js = js_files[0].read_text(encoding='utf-8')
        self.assertIn('.js .nav-menu', css)
        self.assertIn('display:none', css.replace(' ', ''))
        self.assertIn('document.documentElement.classList.add("js")', js)

    def test_admin_and_blank_gallery_routes_are_retired(self):
        routes = collect_html_routes(self.public)
        self.assertNotIn('/admin.html', routes)
        self.assertFalse(any(route.startswith('/gallery') for route in routes))

    def test_generated_output_has_no_legacy_integrations_or_assets(self):
        html = '\n'.join(path.read_text(encoding='utf-8').lower()
                         for path in self.public.rglob('*.html'))
        for marker in ('netlify identity', 'wowchemy', 'jquery', 'codefolding',
                       'themes/matteo-custom', 'themes/starter-hugo-academic',
                       'themes/github.com/wowchemy', '.submodule/scholar-collector'):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, html)
        for route, document in self.all_pages.items():
            for node in document.nodes:
                if node['tag'] == 'script' or (node['tag'] == 'link' and
                                                node['attrs'].get('rel') == 'stylesheet'):
                    asset = node['attrs'].get('src', node['attrs'].get('href', '')).lower()
                    with self.subTest(route=route, asset=asset):
                        self.assertNotRegex(asset, r'jquery|codefold|rmarkdown|wowchemy|netlify')
        self.assertFalse(any('/gallery' in node['attrs'].get('href', '').lower()
                             for document in self.all_pages.values()
                             for node in document.nodes if node['tag'] == 'a'))

    def test_professional_social_links_are_never_hidden(self):
        for route, document in self.all_pages.items():
            for node in document.nodes:
                href = node['attrs'].get('href', '').lower()
                if node['tag'] == 'a' and any(marker in href for marker in
                                               ('linkedin.com', 'github.com', 'scholar.google.com')):
                    with self.subTest(route=route, href=href):
                        self.assertFalse(node['hidden'])
                        self.assertFalse(node['in_template'])

    def test_homepage_has_research_leadership_positioning_and_public_links(self):
        document = self.pages['index.html']
        visible = self.visible(document)
        headings = [node for node in visible if node['tag'] == 'h1']
        self.assertEqual(len(headings), 1)
        self.assertEqual(_accessible_name(headings[0], {}).casefold(),
                         'I lead research and engineering for efficient, reliable language models.'.casefold())
        title = next(node for node in document.nodes if node['tag'] == 'title')
        self.assertEqual(_accessible_name(title, {}).casefold(), 'Staff Applied Researcher - AI Foundations'.casefold())
        links = [node for node in visible if node['tag'] == 'a']
        names = {_accessible_name(node, {}).casefold() for node in links}
        self.assertTrue({name.casefold() for name in
                         ('Publications', 'Google Scholar', 'GitHub', 'LinkedIn', 'Email')} <= names)
        self.assertIn('Explore the research'.casefold(), names)
        research_cta = next(node for node in links if _accessible_name(node, {}).strip() ==
                            'Explore the research')
        self.assertIn(research_cta['attrs'].get('href'), ('/research.html', './research.html'))
        self.assertIn('Read the CV'.casefold(), names)
        self.assertIn('Get in touch'.casefold(), names)

    def test_homepage_has_three_focus_areas_and_ordered_featured_papers(self):
        document = self.pages['index.html']
        visible = self.visible(document)
        focus = [node for node in visible if 'data-focus-area' in node['attrs']]
        self.assertEqual(len(focus), 3)
        cards = [node for node in visible if 'data-publication-card' in node['attrs']]
        self.assertEqual(len(cards), 3)
        headings = [_accessible_name(node, {}) for card in cards for node in card.get('children', [])
                    if node['tag'] == 'h2']
        self.assertEqual(headings, [
            'Critique-Guided Distillation for Robust Reasoning via Refinement',
            'When Load-Balancing Goes Too Far: Expert Pruning in Over-Dispersed Mixture-of-Experts Models',
            'SPEAR-MM: Selective Parameter Evaluation and Restoration via Model Merging for Efficient Financial LLM Adaptation',
        ])

    def test_homepage_proof_strip_uses_verified_publication_facts(self):
        text = ' '.join(_accessible_text(node) for node in self.visible(self.pages['index.html']))
        self.assertIn('PMLR 306', text)
        self.assertIn('arXiv preprint', text)
        self.assertIn('IEEE Big Data 2025', text)
        self.assertNotIn('Paper-backed research connected to engineering practice', text)

    def test_about_page_states_doctoral_field(self):
        about = (self.public / 'about.html').read_text(encoding='utf-8')
        self.assertIn('Ph.D. in Civil Engineering', about)

    def test_homepage_reuses_portrait_with_accessible_alt_text(self):
        document = self.pages['index.html']
        portraits = [node for node in document.nodes if node['tag'] == 'img' and
                     'avatar.jpg' in node['attrs'].get('src', '')]
        self.assertEqual(len(portraits), 1)
        self.assertEqual(portraits[0]['attrs'].get('alt'), 'Portrait of Berkcan Kapusuzoglu')
        h1 = next(node for node in document.nodes if node['tag'] == 'h1')
        self.assertLess(document.nodes.index(h1), document.nodes.index(portraits[0]))
        portrait_file = self.public / 'authors/admin/avatar.jpg'
        self.assertTrue(portrait_file.is_file())
        self.assertGreater(portrait_file.stat().st_size, 0)

    def test_homepage_shows_professional_arc_beyond_education(self):
        text = ' '.join(_accessible_text(node) for node in self.visible(self.pages['index.html'])).casefold()
        self.assertIn('scientific', text)
        self.assertIn('physics-informed', text)
        self.assertIn('language-model research', text)
        self.assertIn('research-led production ai leadership', text)
        self.assertIn('ph.d. in civil engineering', text)

    def test_homepage_avoids_private_or_generic_positioning(self):
        html = (self.public / 'index.html').read_text(encoding='utf-8').lower()
        for phrase in ('personal page', 'cutting-edge', '2,048 gpus', '15b–120b', 'financial impact'):
            self.assertNotIn(phrase, html)
        visible_text = ' '.join(_accessible_text(node) for node in self.pages['index.html'].nodes)
        self.assertNotRegex(visible_text, r'\b\d{5}(?:-\d{4})?\b')
        self.assertNotIn('tel:', html)

    def test_research_leadership_about_and_notes_routes_have_unique_metadata(self):
        metadata = []
        for route in ('research.html', 'research/reasoning-and-distillation.html',
                      'research/efficient-model-systems.html', 'research/trustworthy-ml.html',
                      'leadership.html', 'about.html', 'writing.html'):
            path = self.public / route
            self.assertTrue(path.exists(), f'missing generated route: /{route}')
            document = _Document()
            document.feed(path.read_text(encoding='utf-8'))
            headings = [node for node in self.visible(document) if node['tag'] == 'h1']
            self.assertEqual(len(headings), 1, route)
            title = next(node for node in document.nodes if node['tag'] == 'title')
            description = next(node for node in document.nodes if node['tag'] == 'meta' and
                               node['attrs'].get('name') == 'description')
            metadata.append((_accessible_text(title), description['attrs'].get('content', '')))
            self.assertTrue(metadata[-1][0].strip(), route)
            self.assertTrue(metadata[-1][1].strip(), route)
        self.assertEqual(len({title for title, _ in metadata}), len(metadata))
        self.assertEqual(len({description for _, description in metadata}), len(metadata))

    def test_navigation_has_research_leadership_about_and_notes(self):
        document = self.pages['index.html']
        primary = next(node for node in document.nodes if node['tag'] == 'nav' and
                       node['attrs'].get('aria-label', '').casefold() == 'primary')
        def descendants(node):
            for child in node['children']:
                if isinstance(child, dict):
                    yield child
                    yield from descendants(child)
        names = {_accessible_name(node, {}).casefold() for node in descendants(primary)
                 if node['tag'] == 'a'}
        expected = {'research', 'publications', 'leadership', 'about', 'research notes'}
        self.assertLessEqual(expected, names)

    def test_each_research_theme_links_a_supporting_publication(self):
        required = {
            'reasoning-and-distillation.html': ('2026-critique-guided-distillation.html',),
            'efficient-model-systems.html': ('2026-load-balancing-expert-pruning.html', '2025-spear-mm.html'),
            'trustworthy-ml.html': ('2026-critique-guided-distillation.html', '2025-spear-mm.html'),
        }
        for route, papers in required.items():
            with self.subTest(route=route):
                path = self.public / 'research' / route
                self.assertTrue(path.exists(), f'missing generated research theme: /research/{route}')
                document = _Document()
                document.feed(path.read_text(encoding='utf-8'))
                hrefs = {node['attrs'].get('href', '') for node in document.nodes if node['tag'] == 'a'}
                self.assertTrue(any(paper in href for paper in papers for href in hrefs), route)

    def test_about_maps_the_two_masters_degrees_to_the_correct_fields(self):
        path = self.public / 'about.html'
        self.assertTrue(path.exists(), 'missing generated route: /about.html')
        document = _Document()
        document.feed(path.read_text(encoding='utf-8'))
        text = ' '.join(_accessible_text(node) for node in self.visible(document))
        text = text.casefold()
        self.assertRegex(text, r'(?:delft.{0,120}applied mathematics|applied mathematics.{0,120}delft)')
        self.assertRegex(text, r'(?:erlangen-nuremberg.{0,120}computational engineering|computational engineering.{0,120}erlangen-nuremberg)')

    def test_research_notes_is_an_honest_empty_state(self):
        path = self.public / 'writing.html'
        self.assertTrue(path.exists(), 'missing generated route: /writing.html')
        document = _Document()
        document.feed(path.read_text(encoding='utf-8'))
        text = ' '.join(_accessible_text(node) for node in self.visible(document))
        self.assertIn('no research notes have been published yet', text.casefold())
        hrefs = {node['attrs'].get('href', '') for node in document.nodes if node['tag'] == 'a'}
        self.assertTrue(any('/research/reasoning-and-distillation.html' in href for href in hrefs))
        self.assertTrue(any('/research/efficient-model-systems.html' in href for href in hrefs))
        self.assertTrue(any('/research/trustworthy-ml.html' in href for href in hrefs))

    def test_writing_template_lists_pages_with_accessible_metadata(self):
        template = (Path(__file__).parents[1] / 'layouts/writing/list.html').read_text(
            encoding='utf-8')
        self.assertRegex(template, r'if\s+\.Pages')
        self.assertRegex(template, r'range\s+\.Pages')
        for expression in ('.RelPermalink', '.Title', '.Date', '.Summary'):
            with self.subTest(expression=expression):
                self.assertIn(expression, template)
        self.assertIn('notes-empty-state', template)

    def test_writing_page_lists_a_real_note_bundle(self):
        repo = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            writing = root / 'content' / 'writing'
            note = writing / 'a-test-note'
            note.mkdir(parents=True)
            (writing / '_index.md').write_text(
                '---\ntitle: Research Notes\ndescription: Notes about research and engineering.\n---\n'
                'No research notes have been published yet.\n', encoding='utf-8')
            (note / 'index.md').write_text(
                '---\ntitle: A Test Note\ndate: 2026-09-30\n'
                'description: A practical research note.\n---\n'
                'A short test note summary that should appear in the generated listing.\n',
                encoding='utf-8')
            destination = root / 'public'
            result = subprocess.run(
                ['hugo', '--contentDir', str(root / 'content'), '--destination', str(destination),
                 '--minify', '--panicOnWarning'], cwd=repo, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            document = _Document()
            document.feed((destination / 'writing.html').read_text(encoding='utf-8'))
            text = ' '.join(_accessible_text(node) for node in self.visible(document))
            self.assertIn('A Test Note', text)
            self.assertIn('September 30, 2026', text)
            self.assertIn('A short test note summary', text)
            self.assertNotIn('No research notes have been published yet', text)
            self.assertTrue(any(node['tag'] == 'a' and
                                node['attrs'].get('href') == './writing/a-test-note.html' and
                                _accessible_name(node, {}).strip() == 'A Test Note'
                                for node in document.nodes),
                            [(node['attrs'].get('href'), _accessible_name(node, {}))
                             for node in document.nodes if node['tag'] == 'a'])

    def test_new_narrative_pages_avoid_confidential_claims(self):
        for route in ('research.html', 'research/reasoning-and-distillation.html',
                      'research/efficient-model-systems.html', 'research/trustworthy-ml.html',
                      'leadership.html', 'about.html', 'writing.html'):
            with self.subTest(route=route):
                document = _Document()
                document.feed((self.public / route).read_text(encoding='utf-8'))
                text = ' '.join(_accessible_text(node) for node in self.visible(document)).casefold()
                for phrase in ('2,048 gpus', '15b–120b', 'financial impact', 'capital one, ai foundations', 'cutting-edge'):
                    self.assertNotIn(phrase, text)
                self.assertNotRegex(text, r'\b\d{5}(?:-\d{4})?\b')

    def test_about_uses_exact_official_title(self):
        document = _Document()
        document.feed((self.public / 'about.html').read_text(encoding='utf-8'))
        text = ' '.join(_accessible_text(node) for node in self.visible(document))
        self.assertIn('Staff Applied Researcher - AI Foundations', text)

    def test_research_notes_explains_publishable_and_reusable_content(self):
        document = _Document()
        document.feed((self.public / 'writing.html').read_text(encoding='utf-8'))
        text = ' '.join(_accessible_text(node) for node in self.visible(document)).casefold()
        self.assertIn('publishable notes', text)
        self.assertIn('linkedin', text)


if __name__ == '__main__':
    unittest.main()
