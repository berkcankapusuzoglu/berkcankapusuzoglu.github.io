import subprocess
import sys
import tempfile
import unittest
import re
import json
import html
import shutil
import struct
import zlib
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

from scripts.site_check import (
    collect_html_routes,
    validate_expected_routes,
    validate_html_document,
    _Document,
    _accessible_name,
    _accessible_text,
    _descendants,
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

    def test_research_figure_contract(self):
        valid = '<figure data-research-visual><img src="result.png" alt="Accuracy comparison" width="640" height="480"><figcaption>Accuracy improves.</figcaption></figure>'
        self.assertEqual(self.document('<main><h1>A</h1>' + valid + '</main>'), [])
        cases = (
            (valid.replace('result.png', 'https://example.org/result.png'), 'Research figure uses nonlocal image'),
            (valid.replace('result.png', '//example.org/result.png'), 'Research figure uses nonlocal image'),
            (valid.replace('result.png', 'data:image/png;base64,AA'), 'Research figure uses nonlocal image'),
            (valid.replace('<figcaption>Accuracy improves.</figcaption>', ''), 'Research figure missing useful figcaption'),
            (valid.replace('Accuracy improves.', ' '), 'Research figure missing useful figcaption'),
            (valid.replace(' width="640"', ''), 'Research image missing intrinsic dimensions'),
            (valid.replace('height="480"', 'height="0"'), 'Research image missing intrinsic dimensions'),
            (valid.replace('alt="Accuracy comparison"', 'alt="" aria-hidden="true"'), 'Research image missing useful alt text'),
        )
        for body, expected in cases:
            with self.subTest(body=body):
                self.assertTrue(any(expected in error for error in self.document('<main><h1>A</h1>' + body + '</main>')))

    def test_sequence_requires_accessible_control_button(self):
        for control in ('', '<a href="#">Play</a>', '<button></button>', '<button hidden>Play</button>'):
            with self.subTest(control=control):
                self.assertIn('Research sequence missing accessible control button', self.document(
                    '<main><h1>A</h1><div data-research-sequence>' + control + '</div></main>'))
        self.assertEqual(self.document('<main><h1>A</h1><div data-research-sequence><button>Play</button></div></main>'), [])

    def test_research_picture_sources_must_use_local_candidates(self):
        for srcset in ('https://example.org/result.webp 1x', '//example.org/result.webp 1x',
                       'local.webp 1x, https://example.org/result-2x.webp 2x',
                       'data:image/webp;base64,AA'):
            with self.subTest(srcset=srcset):
                errors = self.document('<main><h1>A</h1><figure data-research-visual><picture>'
                    f'<source type="image/webp" srcset="{srcset}">'
                    '<img src="result.png" alt="Accuracy comparison" width="640" height="480">'
                    '</picture><figcaption>Accuracy improves.</figcaption></figure></main>')
                self.assertTrue(any('Research figure uses nonlocal image' in error for error in errors))
        self.assertEqual(self.document('<main><h1>A</h1><figure data-research-visual><picture>'
            '<source type="image/webp" srcset="result.webp 1x, result-2x.webp 2x">'
            '<img src="result.png" alt="Accuracy comparison" width="640" height="480">'
            '</picture><figcaption>Accuracy improves.</figcaption></figure></main>'), [])

    def test_homepage_rejects_multiple_selected_research_visuals(self):
        path = self.root / 'index.html'
        path.write_text('<main><h1>A</h1><figure data-research-visual data-research-homepage="true"><figcaption>First</figcaption></figure><figure data-research-visual data-research-homepage="true"><figcaption>Second</figcaption></figure></main>', encoding='utf-8')
        self.assertIn('Homepage has more than one selected research visual', validate_html_document(path, '/'))

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


class VisualMetadataTests(unittest.TestCase):
    """Build real temporary publication bundles through the production validator."""

    def test_generated_homepage_rejects_selection_across_featured_publications(self):
        repo = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layouts = root / 'layouts'
            shutil.copytree(repo / 'layouts', layouts)
            # Task 2 validates metadata; rendering ships later. Expose the featured
            # selection with the agreed HTML markers in this fixture homepage.
            (layouts / 'index.html').write_text(
                '<main><h1>Fixture homepage</h1>{{ range partial "featured-publications.html" . }}'
                '{{ range .Params.visuals }}{{ if .homepage }}'
                '<figure data-research-visual data-research-homepage="true">'
                '<img src="result.svg" alt="Comparison" width="10" height="10">'
                '<figcaption>{{ .caption }}</figcaption></figure>{{ end }}{{ end }}{{ end }}</main>',
                encoding='utf-8')
            for index in (1, 2):
                bundle = root / 'content/publications' / f'featured-{index}'
                bundle.mkdir(parents=True)
                metadata = dict(title=f'Featured {index}', date='2026-01-01', authors=['Author'],
                                venue=dict(name='Test venue', type='preprint'), status='preprint',
                                summary='A publication.', contribution='An insight.', topics=[], links=[],
                                featured=True, featured_weight=index,
                                visuals=[dict(self.visual(), homepage=True)])
                (bundle / 'index.md').write_text(json.dumps(metadata), encoding='utf-8')
                (bundle / 'result.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>', encoding='utf-8')
            public = root / 'public'
            result = subprocess.run(['hugo', '--contentDir', str(root / 'content'), '--layoutDir',
                                     str(layouts), '--destination', str(public), '--panicOnWarning'],
                                    cwd=repo, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Homepage has more than one selected research visual',
                          validate_html_document(public / 'index.html', '/'))

    def build_visuals(self, visuals):
        repo = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / 'content/publications/contract-fixture'
            bundle.mkdir(parents=True)
            metadata = dict(title='Contract fixture', date='2026-01-01', authors=['Author'],
                            venue=dict(name='Test venue', type='preprint'), status='preprint',
                            summary='A test publication.', contribution='A test contribution.', topics=[], links=[])
            if visuals is not None:
                metadata['visuals'] = visuals
            (bundle / 'index.md').write_text(json.dumps(metadata) + '\nFixture body.', encoding='utf-8')
            (bundle / 'result.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>', encoding='utf-8')
            return subprocess.run(['hugo', '--contentDir', str(root / 'content'),
                                   '--destination', str(root / 'public'), '--panicOnWarning'],
                                  cwd=repo, capture_output=True, text=True)

    def visual(self):
        return dict(id='accuracy', file='result.svg', role='result', alt='Accuracy comparison',
                    caption='Accuracy improves.', takeaway='The model improves accuracy.',
                    source_label='Paper figure 1', source_url='https://example.org/paper',
                    license='CC BY 4.0')

    def test_legacy_and_complete_visuals_build(self):
        for visuals in (None, [], [self.visual()], [dict(self.visual(), sequence=[
                dict(label='Before', file='result.svg'), dict(label='After', file='result.svg')])]):
            with self.subTest(visuals=visuals):
                result = self.build_visuals(visuals)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_visual_required_fields_are_rejected(self):
        for field in ('id', 'file', 'role', 'alt', 'caption', 'takeaway', 'source_label', 'source_url', 'license'):
            for value in (None, ' '):
                with self.subTest(field=field, value=value):
                    visual = self.visual()
                    if value is None:
                        del visual[field]
                    else:
                        visual[field] = value
                    result = self.build_visuals([visual])
                    self.assertNotEqual(result.returncode, 0, 'Incomplete visual unexpectedly built')
                    self.assertIn('contract-fixture/index.md', (result.stdout + result.stderr).replace('\\', '/'))
                    self.assertIn(field, result.stdout + result.stderr)

    def test_visual_rejects_invalid_resources_roles_ids_and_sequences(self):
        cases = (
            [dict(self.visual(), file='https://example.org/result.svg')],
            [dict(self.visual(), file='//example.org/result.svg')],
            [dict(self.visual(), file='missing.svg')],
            [self.visual(), self.visual()],
            [dict(self.visual(), role='decorative')],
            [dict(self.visual(), sequence=[])],
            [dict(self.visual(), sequence=[dict(label='First', file='result.svg')])],
            [dict(self.visual(), sequence=[dict(file='result.svg'), dict(label='Last', file='result.svg')])],
            [dict(self.visual(), sequence=[dict(label='First'), dict(label='Last', file='result.svg')])],
            [dict(self.visual(), sequence=[dict(label='First', file='https://example.org/frame.svg'), dict(label='Last', file='result.svg')])],
            [dict(self.visual(), sequence=[dict(label='First', file='missing.svg'), dict(label='Last', file='result.svg')])],
            [dict(self.visual(), sequence=[dict(label='First', file='result.svg', duration=0), dict(label='Last', file='result.svg')])],
            [dict(self.visual(), sequence=[dict(label='First', file='result.svg', duration='fast'), dict(label='Last', file='result.svg')])],
            [dict(self.visual(), sequence=[dict(label='First', file='result.svg', focus=dict(x=95, y=0, width=10, height=10)), dict(label='Last', file='result.svg')])],
            [dict(self.visual(), sequence=[dict(label='First', file='result.svg', focus=dict(x=0, y=0, width=10)), dict(label='Last', file='result.svg')])],
        )
        for visuals in cases:
            with self.subTest(visuals=visuals):
                result = self.build_visuals(visuals)
                self.assertNotEqual(result.returncode, 0, 'Invalid visual unexpectedly built')
                self.assertIn('contract-fixture/index.md', (result.stdout + result.stderr).replace('\\', '/'))
                self.assertIn('accuracy', result.stdout + result.stderr)


class ResearchComponentTests(unittest.TestCase):
    """Exercise production partials with local image resources, not source snapshots."""

    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).parents[1]
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.public = cls.root / 'public'
        layouts = cls.root / 'layouts'
        shutil.copytree(cls.repo / 'layouts', layouts)
        (layouts / 'publications/single.html').write_text(
            '{{ define "main" }}<h1>{{ .Title }}</h1>'
            '{{ partial "research-visual-validate.html" . }}'
            '{{ range .Params.visuals }}{{ partial "research-figure.html" '
            '(dict "Page" $ "Visual" . "Context" "publication") }}{{ end }}{{ end }}',
            encoding='utf-8')
        (layouts / 'index.html').write_text(
            '{{ define "main" }}<h1>Research fixture</h1>'
            '{{ range partial "featured-publications.html" . }}{{ $page := . }}'
            '{{ range .Params.visuals }}{{ if .homepage }}'
            '{{ partial "research-figure.html" (dict "Page" $page "Visual" . "Context" "homepage") }}'
            '{{ end }}{{ end }}{{ end }}{{ end }}', encoding='utf-8')
        # A wide raster catches accidental upscaling and missing responsive derivatives.
        def chunk(kind, data):
            return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))
        png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', 1600, 900, 8, 2, 0, 0, 0))
               + chunk(b'IDAT', zlib.compress((b'\x00' + b'\xff\xff\xff' * 1600) * 900)) + chunk(b'IEND', b''))
        for name in ('static', 'sequence', 'vector'):
            bundle = cls.root / 'content/publications' / name
            bundle.mkdir(parents=True)
            visual = dict(VisualMetadataTests().visual(), file='result.png', homepage=name == 'static')
            if name == 'sequence':
                visual['sequence'] = [dict(label='Initial evidence', file='result.png'),
                                      dict(label='Combined evidence', file='result.png'),
                                      dict(label='Final interpretation', file='result.png')]
            if name == 'vector':
                visual['file'] = 'result.svg'
            metadata = dict(title=f'{name.title()} fixture', date='2026-01-01', authors=['Author'],
                            venue=dict(name='Test venue', type='preprint'), status='preprint',
                            summary='A test publication.', contribution='A test contribution.',
                            topics=[], links=[], featured=name == 'static', featured_weight=1, visuals=[visual])
            (bundle / 'index.md').write_text(json.dumps(metadata), encoding='utf-8')
            (bundle / 'result.png').write_bytes(png)
            (bundle / 'result.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450"></svg>', encoding='utf-8')
        cls.build = subprocess.run(['hugo', '--contentDir', str(cls.root / 'content'), '--layoutDir',
                                   str(layouts), '--destination', str(cls.public), '--panicOnWarning'],
                                  cwd=cls.repo, capture_output=True, text=True)

    def page(self, name):
        self.assertEqual(self.build.returncode, 0, self.build.stdout + self.build.stderr)
        path = self.public / name
        document = _Document()
        document.feed(path.read_text(encoding='utf-8'))
        return document

    def test_static_output_preserves_interpretation_attribution_and_responsive_images(self):
        document = self.page('publications/static.html')
        figures = [n for n in document.nodes if n['tag'] == 'figure' and 'data-research-visual' in n['attrs']]
        self.assertEqual(len(figures), 1)
        visible_text = _accessible_text(figures[0])
        for text in ('The model improves accuracy.', 'Accuracy improves.', 'Paper figure 1', 'CC BY 4.0'):
            self.assertIn(text, visible_text)
        self.assertTrue(any(n['tag'] == 'a' and n['attrs'].get('href') == 'https://example.org/paper'
                            for n in document.nodes))
        image = next(n for n in document.nodes if n['tag'] == 'img')
        self.assertEqual(image['attrs']['width'], '1600')
        self.assertEqual(image['attrs']['height'], '900')
        self.assertEqual(image['attrs']['loading'], 'lazy')
        source = next(n for n in document.nodes if n['tag'] == 'source')
        self.assertEqual(source['attrs']['type'], 'image/webp')
        self.assertTrue(all(f'{width}w' in source['attrs']['srcset'] for width in (640, 960, 1440)))
        self.assertEqual(validate_html_document(self.public / 'publications/static.html'), [])

    def test_only_homepage_selected_image_has_eager_priority(self):
        document = self.page('index.html')
        image = next(n for n in document.nodes if n['tag'] == 'img')
        self.assertEqual(image['attrs']['loading'], 'eager')
        self.assertEqual(image['attrs']['fetchpriority'], 'high')
        self.assertTrue(any(n['attrs'].get('data-research-homepage') == 'true' for n in document.nodes))

    def test_vector_resource_retains_viewbox_dimensions(self):
        document = self.page('publications/vector.html')
        image = next(n for n in document.nodes if n['tag'] == 'img')
        self.assertEqual((image['attrs']['width'], image['attrs']['height']), ('800', '450'))
        self.assertTrue(image['attrs']['src'].endswith('result.svg'))

    def test_sequence_has_static_final_frame_labels_and_accessible_control(self):
        document = self.page('publications/sequence.html')
        frames = [n for n in document.nodes if 'data-sequence-frame' in n['attrs']]
        self.assertEqual(len(frames), 3)
        self.assertTrue(frames[0]['hidden'])
        self.assertTrue(frames[1]['hidden'])
        self.assertFalse(frames[-1]['hidden'])
        self.assertTrue(any(n['tag'] == 'button' and _accessible_name(n, {}).strip() for n in document.nodes))
        self.assertTrue(any(n['attrs'].get('aria-live') == 'polite' for n in document.nodes))
        step_text = ' '.join(_accessible_text(n) for n in document.nodes if 'data-sequence-step' in n['attrs'])
        for label in ('Initial evidence', 'Combined evidence', 'Final interpretation'):
            self.assertIn(label, step_text)
        self.assertEqual(validate_html_document(self.public / 'publications/sequence.html'), [])

    def test_sequence_script_is_conditional_and_fingerprinted(self):
        for name, expected in (('index.html', False), ('publications/static.html', False),
                               ('publications/vector.html', False), ('publications/sequence.html', True)):
            with self.subTest(name=name):
                scripts = [n['attrs'].get('src', '') for n in self.page(name).nodes if n['tag'] == 'script']
                sequence_scripts = [src for src in scripts if 'research-visuals' in src]
                self.assertEqual(bool(sequence_scripts), expected)
                if expected:
                    self.assertRegex(sequence_scripts[0], r'research-visuals\.min\.[a-f0-9]+\.js$')

    def test_controller_syntax_and_browser_motion_keyboard_print_contract(self):
        self.page('publications/sequence.html')
        syntax = subprocess.run(['node', '--check', 'assets/js/research-visuals.js'],
                                cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(syntax.returncode, 0, syntax.stdout + syntax.stderr)
        environment = dict(os.environ)
        if os.name == 'nt' and Path('C:/Program Files/Google/Chrome/Application/chrome.exe').is_file():
            environment.pop('PUPPETEER_EXECUTABLE_PATH', None)
        browser = subprocess.run(['node', 'scripts/check_a11y.mjs', '--sequence-fixture', str(self.public)],
                                 cwd=self.repo, env=environment, capture_output=True, text=True, timeout=120)
        self.assertEqual(browser.returncode, 0, browser.stdout + browser.stderr)
        self.assertIn('Sequence browser checks passed', browser.stdout)


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
                'part_type': 'CreativeWorkSeries',
                'part_name': 'NeurIPS 2026 Workshop on On-Device Intelligence',
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
                self.assertIn('accepted' if route.startswith('2026-load') else 'published',
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

    def test_publication_listing_pages_use_only_unique_normalized_records(self):
        listing_paths = [self.public / 'publications.html']
        listing_paths.extend(sorted((self.public / 'publications' / 'page').glob('*.html')))
        title_links = []

        def descendants(node):
            for child in node['children']:
                if isinstance(child, dict):
                    yield child
                    yield from descendants(child)

        for path in listing_paths:
            document = _Document()
            document.feed(path.read_text(encoding='utf-8'))
            for card in (node for node in document.nodes if 'data-publication-card' in node['attrs']):
                headings = [node for node in descendants(card) if node['tag'] == 'h2']
                self.assertEqual(len(headings), 1, path)
                title_link = next(node for node in descendants(headings[0]) if node['tag'] == 'a')
                title_links.append((urljoin(f'https://berkcankapusuzoglu.github.io/{path.relative_to(self.public).as_posix()}',
                                            title_link['attrs'].get('href', '')),
                                    _accessible_name(title_link, {}).strip()))

        self.assertTrue(title_links)
        self.assertGreater(len(title_links), 10)
        self.assertEqual(len(title_links), len(set(title_links)))
        self.assertNotIn('/publications/2021_witherell_paul_witherell_berkcan_kapusuzoglu_matthew_sato_sankaran_mahadevan.html',
                         [href for href, _ in title_links])
        canonical_bond_record = 'https://berkcankapusuzoglu.github.io/publications/2020_kapusuzoglu_journal_of_manufacturing_science_and_engineering.html'
        self.assertEqual(sum(href == canonical_bond_record for href, _ in title_links), 1)

    def test_paginator_metadata_is_scoped_and_self_canonical(self):
        repo = Path(__file__).parents[1]
        for relative in ('layouts/_default/baseof.html', 'layouts/partials/head.html',
                         'layouts/partials/seo.html'):
            self.assertNotIn('.Paginator', (repo / relative).read_text(encoding='utf-8'))
        for route in ('publications/page/2.html', 'publication-type/2/page/2.html'):
            with self.subTest(route=route):
                document = self.all_pages[route]
                canonical = next(node['attrs'].get('href', '') for node in document.nodes
                                 if node['tag'] == 'link' and
                                 node['attrs'].get('rel') == 'canonical')
                title = next(node for node in document.nodes if node['tag'] == 'title')
                description = next(node['attrs'].get('content', '') for node in document.nodes
                                   if node['tag'] == 'meta' and
                                   node['attrs'].get('name') == 'description')
                expected = f'https://berkcankapusuzoglu.github.io/{route}'
                self.assertEqual(canonical, expected)
                self.assertIn('Page 2', _accessible_text(title))
                self.assertTrue(description.strip())

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

    def test_homepage_selects_only_cgd_overview_and_keeps_other_cards_text_only(self):
        document = self.pages['index.html']
        figures = [n for n in self.visible(document) if 'data-research-visual' in n['attrs']]
        self.assertEqual(len(figures), 1)
        self.assertEqual(figures[0]['attrs'].get('data-research-homepage'), 'true')
        images = [n for n in self.visible(document) if n['tag'] == 'img' and '/media/' in n['attrs'].get('src', '')]
        self.assertEqual(len(images), 1)
        self.assertIn('/2026-critique-guided-distillation/media/cgd-overview', images[0]['attrs']['src'])
        for card in [n for n in self.visible(document) if 'data-publication-card' in n['attrs']][1:]:
            self.assertFalse(any(n['tag'] == 'img' for n in _descendants(card)))

    def test_homepage_research_fallback_and_candidates_meet_byte_budget(self):
        doc = self.pages['index.html']
        figures = [node for node in doc.nodes if 'data-research-visual' in node['attrs']]
        self.assertEqual(len(figures), 1)
        paths = []
        for node in _descendants(figures[0]):
            if node['tag'] == 'img':
                paths.append(node['attrs']['src'])
            if node['tag'] == 'source':
                paths.extend(candidate.strip().split()[0]
                             for candidate in node['attrs']['srcset'].split(','))
        self.assertTrue(paths)
        self.assertTrue(any(node['tag'] == 'a' and
                            node['attrs'].get('href', '').endswith('/media/cgd-overview.png')
                            and _accessible_text(node).strip() == 'Open full-size figure'
                            for node in doc.nodes))
        for path in paths:
            with self.subTest(path=path):
                self.assertLessEqual((self.public / path.lstrip('/')).stat().st_size,
                                     250000)

    def test_featured_paper_figures_render_in_story_order_with_visible_interpretation(self):
        expected = {
            '2026-critique-guided-distillation': ['cgd-overview.png', 'cgd-accuracy.png'],
            '2026-load-balancing-expert-pruning': ['ppl-accuracy.png'],
            '2025-spear-mm': ['spear-pipeline.png', 'retention-adaptation.png'],
        }
        for slug, files in expected.items():
            with self.subTest(slug=slug):
                document = self.all_pages[f'publications/{slug}.html']
                visible = self.visible(document)
                figures = [n for n in visible if 'data-research-visual' in n['attrs']]
                self.assertEqual(len(figures), len(files))
                images = [n for n in visible if n['tag'] == 'img']
                self.assertEqual([Path(n['attrs']['src']).name for n in images], files)
                for figure in figures:
                    caption = next(n for n in figure['children'] if isinstance(n, dict) and n['tag'] == 'figcaption')
                    paragraphs = [n for n in caption['children'] if isinstance(n, dict) and n['tag'] == 'p']
                    self.assertTrue(_accessible_text(paragraphs[0]).strip())
                    self.assertIn('research-visual-takeaway', paragraphs[0]['attrs'].get('class', ''))
                    self.assertIn('CC BY 4.0', _accessible_text(paragraphs[-1]))
                    self.assertIn('Figure ', _accessible_text(paragraphs[-1]))
                    self.assertGreater(visible.index(caption), visible.index(images[figures.index(figure)]))
                contribution = next(n for n in visible if n['tag'] == 'h2' and _accessible_text(n).strip() == 'Research contribution')
                self.assertLess(visible.index(contribution), visible.index(figures[0]))

    def test_paper_figures_offer_original_resolution_for_dense_labels(self):
        for slug, count in [('2026-critique-guided-distillation', 2),
                            ('2026-load-balancing-expert-pruning', 1), ('2025-spear-mm', 2)]:
            document = self.all_pages[f'publications/{slug}.html']
            links = [n for n in self.visible(document) if n['tag'] == 'a' and
                     _accessible_text(n).strip() == 'Open full-size figure']
            self.assertEqual(len(links), count)
            self.assertTrue(all(n['attrs']['href'].endswith('.png') for n in links))

    def test_expert_pruning_identifies_accepted_odi_workshop(self):
        for route in ('index.html', 'publications/2026-load-balancing-expert-pruning.html'):
            document = self.all_pages[route]
            papers = [n for n in self.visible(document) if 'data-publication' in n['attrs'] and
                      'When Load-Balancing Goes Too Far' in _accessible_text(n)]
            self.assertEqual(len(papers), 1)
            self.assertEqual(papers[0]['attrs']['data-status'], 'accepted')
            self.assertIn('NeurIPS 2026 Workshop on On-Device Intelligence', _accessible_text(papers[0]))
            self.assertTrue(any(n['attrs'].get('data-venue-type') == 'workshop' for n in _descendants(papers[0])))
            self.assertTrue(any(n['attrs'].get('href') == 'https://arxiv.org/abs/2609.04453' for n in _descendants(papers[0])))

    def test_homepage_proof_strip_uses_verified_publication_facts(self):
        strip = next(node for node in self.visible(self.pages['index.html'])
                     if node['attrs'].get('aria-label') == 'Research profile')
        text = ' '.join(_accessible_text(node) for node in _descendants(strip)
                        if node['tag'] == 'p')
        self.assertIn('PMLR 306', text)
        self.assertIn('NeurIPS 2026 Workshop on On-Device Intelligence', text)
        self.assertIn('Accepted', text)
        self.assertNotIn('arXiv preprint', text)
        self.assertIn('IEEE Big Data 2025', text)
        self.assertNotIn('Paper-backed research connected to engineering practice', text)

    def test_about_page_states_doctoral_field(self):
        about = (self.public / 'about.html').read_text(encoding='utf-8')
        self.assertIn('Ph.D. in Civil Engineering', about)

    def test_leadership_renders_owner_supplied_policy_distillation_example(self):
        paragraphs = [_accessible_text(node) for node in self.visible(self.all_pages['leadership.html'])
                      if node['tag'] == 'p' and 'MOPD' in _accessible_text(node)]
        self.assertEqual(paragraphs, [
            'In my latest role, I worked on policy distillation (OPD) and multi-teacher OPD '
            '(MOPD), improving internal model performance on agentic tasks.'])

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

    def test_research_notes_lists_the_published_cgd_note(self):
        path = self.public / 'writing.html'
        self.assertTrue(path.exists(), 'missing generated route: /writing.html')
        document = _Document()
        document.feed(path.read_text(encoding='utf-8'))
        text = ' '.join(_accessible_text(node) for node in self.visible(document))
        self.assertNotIn('no research notes have been published yet', text.casefold())
        self.assertIn('Learning from mistakes with critique-guided distillation', text)
        hrefs = {node['attrs'].get('href', '') for node in document.nodes if node['tag'] == 'a'}
        self.assertTrue(any('/writing/critique-guided-distillation-refinement.html' in href for href in hrefs))

    def test_cgd_note_renders_exact_pixel_sequence_and_result_with_provenance(self):
        import hashlib
        repo = Path(__file__).parents[1]
        route = self.public / 'writing/critique-guided-distillation-refinement.html'
        self.assertTrue(route.is_file(), 'CGD Research Note is missing')
        document = _Document()
        document.feed(route.read_text(encoding='utf-8'))
        self.assertEqual(validate_html_document(route), [])
        frames = [node for node in document.nodes if 'data-sequence-frame' in node['attrs']]
        self.assertEqual(len(frames), 4)
        self.assertTrue(all('hidden' in node['attrs'] for node in frames[:-1]))
        self.assertIn('data-sequence-poster', frames[-1]['attrs'])
        images = [node for node in document.nodes if node['tag'] == 'img' and
                  node['attrs'].get('src', '').endswith('cgd-overview.png')]
        self.assertEqual(len(images), 4)
        self.assertEqual(len({node['attrs']['src'] for node in images}), 1)
        self.assertEqual(len([node for node in document.nodes if 'data-sequence-focus' in node['attrs']]), 3)
        self.assertIn('Prompt only. No teacher or critique at inference.',
                      ' '.join(_accessible_text(node) for node in self.visible(document)))
        self.assertEqual(len([node for node in document.nodes if 'data-research-visual' in node['attrs']]), 2)
        self.assertTrue(any(node['tag'] == 'script' and 'research-visuals.min.' in
                            node['attrs'].get('src', '') for node in document.nodes))
        for name in ('cgd-overview.png', 'cgd-accuracy.png'):
            source = repo / 'content/publications/2026-critique-guided-distillation/media' / name
            output = repo / 'content/writing/critique-guided-distillation-refinement/media' / name
            self.assertEqual(hashlib.sha256(output.read_bytes()).digest(),
                             hashlib.sha256(source.read_bytes()).digest())

    def test_writing_template_lists_pages_with_accessible_metadata(self):
        template = (Path(__file__).parents[1] / 'layouts/writing/list.html').read_text(
            encoding='utf-8')
        self.assertRegex(template, r'if\s+gt\s+\(len\s+\.RegularPages\)\s+0')
        self.assertRegex(template, r'range\s+\$paginator\.Pages')
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

    def test_writing_pagination_lists_eleven_notes_exactly_once(self):
        repo = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            writing = root / 'content' / 'writing'
            writing.mkdir(parents=True)
            (writing / '_index.md').write_text(
                '---\ntitle: Research Notes\ndescription: A collection of research notes.\n---\n'
                'No research notes have been published yet.\n', encoding='utf-8')
            expected = {f'note-{index:02d}' for index in range(1, 12)}
            for index in range(1, 12):
                note = writing / f'note-{index:02d}'
                note.mkdir()
                (note / 'index.md').write_text(
                    f'---\ntitle: Research Note {index:02d}\n'
                    f'date: 2026-08-{index:02d}\ndescription: Summary for note {index:02d}.\n'
                    f'---\nA useful summary for research note {index:02d}.\n',
                    encoding='utf-8')
            destination = root / 'public'
            result = subprocess.run(
                ['hugo', '--contentDir', str(root / 'content'), '--destination', str(destination),
                 '--minify', '--panicOnWarning'], cwd=repo, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page_paths = (destination / 'writing.html', destination / 'writing' / 'page' / '2.html')
            self.assertTrue(all(path.is_file() for path in page_paths))
            page_notes = []
            for path in page_paths:
                document = _Document()
                document.feed(path.read_text(encoding='utf-8'))
                self.assertNotIn('No research notes have been published yet',
                                 ' '.join(_accessible_text(node) for node in document.nodes))
                note_ids = [Path(urlparse(node['attrs'].get('href', '')).path).stem
                            for node in document.nodes if node['tag'] == 'a' and
                            '/writing/note-' in node['attrs'].get('href', '')]
                page_notes.append(note_ids)
            self.assertTrue(set(page_notes[0]).isdisjoint(page_notes[1]))
            self.assertEqual(set(page_notes[0] + page_notes[1]), expected)
            self.assertEqual(len(page_notes[0] + page_notes[1]), len(expected))

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
