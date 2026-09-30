"""Validate generated routes and basic HTML accessibility without dependencies."""

import argparse
import posixpath
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


PAGINATOR_REDIRECT_ROUTES = {
    '/categories/page/1.html',
    '/gallery/page/1.html',
    '/news/page/1.html',
    '/publication-type/2/page/1.html',
    '/publication_types/page/1.html',
    '/publications/page/1.html',
    '/tag/job/page/1.html',
    '/tag/personal/page/1.html',
    '/tags/page/1.html',
}


def _is_known_paginator_redirect(document, route: str) -> bool:
    if route not in PAGINATOR_REDIRECT_ROUTES:
        return False
    nodes = document.nodes
    tags = [node['tag'] for node in nodes]
    if tags != ['html', 'head', 'title', 'link', 'meta', 'meta', 'meta']:
        return False
    expected_path = route.removesuffix('page/1.html').rstrip('/') + '.html'
    expected_url = f'https://berkcankapusuzoglu.github.io{expected_path}'
    title, canonical, robots, charset, refresh = nodes[2:]
    return (
        _accessible_text(title).strip() == expected_url and
        canonical['attrs'] == {'rel': 'canonical', 'href': expected_url} and
        robots['attrs'].get('name') == 'robots' and robots['attrs'].get('content') == 'noindex' and
        charset['attrs'].get('charset', '').lower() == 'utf-8' and
        refresh['attrs'].get('http-equiv', '').lower() == 'refresh' and
        refresh['attrs'].get('content', '').strip().lower() == f'0; url={expected_url}'.lower()
    )


def _has_remote_css_resource(css: str) -> bool:
    uncommented = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    remote_url = re.compile(r'''url\s*\(\s*["']?\s*(?:https?:)?//''', re.IGNORECASE)
    remote_import = re.compile(r'''@import\s+(?:url\s*\(\s*)?["']\s*(?:https?:)?//''', re.IGNORECASE)
    return bool(remote_url.search(uncommented) or remote_import.search(uncommented))


def collect_html_routes(public_dir: Path) -> set[str]:
    return {'/' if path.relative_to(public_dir).as_posix() == 'index.html'
            else '/' + path.relative_to(public_dir).as_posix()
            for path in public_dir.rglob('*.html')}


def validate_expected_routes(actual: set[str], expected_file: Path) -> list[str]:
    expected = {line.strip() for line in expected_file.read_text(encoding='utf-8').splitlines()
                if line.strip() and not line.lstrip().startswith('#')}
    return [f'Missing route: {route}' for route in sorted(expected - actual)]


class _Document(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {'tag': '', 'attrs': {}, 'children': [], 'hidden': False,
                     'in_template': False}
        self.stack = [self.root]
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        parent = self.stack[-1]
        node = {'tag': tag, 'attrs': attributes, 'children': [],
                'hidden': parent['hidden'] or 'hidden' in attributes or
                          attributes.get('aria-hidden', '').lower() == 'true',
                'in_template': parent['in_template'] or tag == 'template'}
        self.stack[-1]['children'].append(node)
        self.nodes.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index]['tag'] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1]['children'].append(data)


def _accessible_text(node, include_hidden=False):
    attrs = node['attrs']
    if node['in_template'] or (node['hidden'] and not include_hidden):
        return ''
    if node['tag'] in {'script', 'style', 'template'}:
        return ''
    if attrs.get('aria-label', '').strip():
        return attrs['aria-label']
    if node['tag'] == 'img':
        return attrs.get('alt') or ''
    return ' '.join(child if isinstance(child, str) else _accessible_text(child, include_hidden)
                    for child in node['children'])


def _accessible_name(node, ids):
    references = [ids[label] for label in node['attrs'].get('aria-labelledby', '').split()
                  if label in ids]
    if references:
        return ' '.join(_accessible_text(label, include_hidden=label['hidden'])
                        for label in references)
    return _accessible_text(node)


def validate_html_document(path: Path, route: str | None = None) -> list[str]:
    document = _Document()
    document.feed(path.read_text(encoding='utf-8'))
    route = route or '/' + path.as_posix().lstrip('/')
    if _is_known_paginator_redirect(document, route):
        return []
    errors = []
    visible = [node for node in document.nodes if not node['hidden'] and not node['in_template']]
    headings = [node for node in visible if node['tag'] == 'h1']
    h1_count = len(headings)
    if h1_count != 1:
        errors.append(f'Expected exactly one H1; found {h1_count}')
    if not any(node['tag'] == 'main' for node in visible):
        errors.append('Missing main landmark')
    ids = {node['attrs']['id']: node for node in document.nodes
           if node['attrs'].get('id') and not node['in_template']}
    for heading in headings:
        if not _accessible_name(heading, ids).strip():
            errors.append('H1 missing accessible text')
    for node in document.nodes:
        attrs = node['attrs']
        if node['tag'] == 'img':
            alt = attrs.get('alt')
            decorative = alt == '' and attrs.get('aria-hidden', '').lower() == 'true'
            if not decorative and not (alt or '').strip():
                errors.append(f"Image missing useful alt text: {attrs.get('src', '(no src)')}")
        if node['tag'] == 'a' and 'href' in attrs:
            name = _accessible_name(node, ids)
            if not name.strip():
                errors.append(f"Link missing accessible text: {attrs['href']}")
    return errors


def validate_generated_shell(path: Path, public_dir: Path) -> list[str]:
    """Check the shared local shell and its runtime assets on each generated page."""
    document = _Document()
    document.feed(path.read_text(encoding='utf-8'))
    route = '/' + path.relative_to(public_dir).as_posix()
    if route == '/index.html':
        route = '/'
    if _is_known_paginator_redirect(document, route):
        return []
    visible = [node for node in document.nodes if not node['hidden'] and not node['in_template']]
    errors = []

    if not any(node['tag'] == 'a' and node['attrs'].get('href') == '#main-content'
               for node in visible):
        errors.append('Missing skip link to #main-content')
    if not any(node['tag'] == 'main' and node['attrs'].get('id') == 'main-content'
               for node in visible):
        errors.append('Missing visible main#main-content landmark')
    if not any(node['tag'] == 'nav' and node['attrs'].get('aria-label') == 'Primary'
               for node in visible):
        errors.append('Missing labelled Primary navigation')
    toggles = [node for node in visible if 'data-nav-toggle' in node['attrs']]
    menus = [node for node in visible if 'data-nav-menu' in node['attrs']]
    if len(toggles) != 1 or toggles[0]['tag'] != 'button':
        errors.append('Mobile navigation requires exactly one real toggle button')
    elif (len(menus) != 1 or not menus[0]['attrs'].get('id') or
          toggles[0]['attrs'].get('aria-controls') != menus[0]['attrs'].get('id')):
        errors.append('Mobile navigation toggle must control its menu')

    canonicals = [node for node in document.nodes if node['tag'] == 'link'
                  and node['attrs'].get('rel') == 'canonical']
    if len(canonicals) != 1 or not canonicals[0]['attrs'].get('href', '').strip():
        errors.append('Expected one nonempty canonical URL')
    descriptions = [node for node in document.nodes if node['tag'] == 'meta'
                    and node['attrs'].get('name', '').lower() == 'description'
                    and node['attrs'].get('content', '').strip()]
    if not descriptions:
        errors.append('Missing nonempty meta description')

    canonical_host = urlparse(canonicals[0]['attrs'].get('href', '')).netloc if len(canonicals) == 1 else ''
    local_stylesheets = []
    for node in document.nodes:
        attrs = node['attrs']
        if node['tag'] == 'script' or (node['tag'] == 'link' and attrs.get('rel') in
                                       {'stylesheet', 'preconnect', 'preload'}):
            asset = attrs.get('src', attrs.get('href', ''))
            parsed = urlparse(asset)
            if parsed.netloc and parsed.netloc != canonical_host:
                errors.append(f'Remote runtime asset: {asset}')
            if 'wowchemy' in asset.lower():
                errors.append(f'Active Wowchemy asset: {asset}')
        if node['tag'] == 'link' and attrs.get('rel') == 'stylesheet':
            href = attrs.get('href', '')
            if not urlparse(href).netloc or urlparse(href).netloc == canonical_host:
                local_stylesheets.append(href)
    if not local_stylesheets:
        errors.append('Missing local stylesheet')
    for href in local_stylesheets:
        target_url = urljoin('https://site.invalid' + route, href)
        target_path = posixpath.normpath(urlparse(target_url).path.lstrip('/'))
        css_path = public_dir / Path(target_path)
        try:
            css = css_path.read_text(encoding='utf-8')
        except OSError:
            errors.append(f'Missing local stylesheet file: {href}')
            continue
        if ':focus-visible' not in css:
            errors.append(f'Local stylesheet lacks :focus-visible: {href}')
        if _has_remote_css_resource(css):
            errors.append(f'Remote font or runtime resource in stylesheet: {href}')
    return [f'{route}: {error}' for error in errors]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public', type=Path, required=True)
    parser.add_argument('--expected', type=Path, required=True)
    args = parser.parse_args()
    try:
        errors = validate_expected_routes(collect_html_routes(args.public), args.expected)
        findings = []
        for path in sorted(args.public.rglob('*.html')):
            relative = path.relative_to(args.public).as_posix()
            route = '/' if relative == 'index.html' else '/' + relative
            findings.extend(f'{route}: {error}' for error in validate_html_document(path, route))
            errors.extend(validate_generated_shell(path, args.public))
        errors.extend(findings)
    except (OSError, ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print(error)
    if not errors:
        print('Site checks passed')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
