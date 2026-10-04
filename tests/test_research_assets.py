import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts import research_assets
from scripts.research_assets import inventory_archive, select_entry


class ResearchAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / 'outer.zip'
        self.make_archive({
            'Z project.zip': {'figures/z.PDF': b'pdf', 'movie.webm': b'motion'},
            'A project.zip': {'figures/b.png': b'image', 'figures/a.pdf': b'abc',
                              'main.tex': b'not a figure'},
        })

    def make_archive(self, projects):
        with zipfile.ZipFile(self.archive, 'w') as outer:
            for project, files in projects.items():
                data = io.BytesIO()
                with zipfile.ZipFile(data, 'w') as inner:
                    for name, payload in files.items():
                        inner.writestr(name, payload)
                outer.writestr(project, data.getvalue())

    def test_inventory_sorted_metadata_and_counts_without_extraction(self):
        before = sorted(self.root.rglob('*'))
        projects = inventory_archive(self.archive)
        self.assertEqual([p.name for p in projects], ['A project.zip', 'Z project.zip'])
        self.assertEqual([(f.path, f.extension, f.size) for f in projects[0].figures],
                         [('figures/a.pdf', '.pdf', 3), ('figures/b.png', '.png', 5)])
        self.assertEqual([p.figure_count for p in projects], [2, 1])
        self.assertEqual([p.motion_count for p in projects], [0, 1])
        self.assertEqual(projects[0].figures[0].sha256,
                         'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        self.assertEqual(sorted(self.root.rglob('*')), before)

    def test_extract_only_selected_entry(self):
        destination = self.root / 'output' / 'figure.pdf'
        self.assertEqual(select_entry(self.archive, 'A project.zip',
                                      'figures/a.pdf', destination), destination)
        self.assertEqual(destination.read_bytes(), b'abc')
        self.assertEqual(list(destination.parent.iterdir()), [destination])

    def test_missing_project_does_not_create_destination_parent(self):
        destination = self.root / 'output' / 'figure.pdf'
        with self.assertRaises(KeyError):
            select_entry(self.archive, 'unknown.zip', 'figures/a.pdf', destination)
        self.assertFalse(destination.parent.exists())

    def test_missing_entry_does_not_create_destination_parent(self):
        destination = self.root / 'output' / 'figure.pdf'
        with self.assertRaises(KeyError):
            select_entry(self.archive, 'A project.zip', 'unknown.pdf', destination)
        self.assertFalse(destination.parent.exists())

    def test_reject_unsafe_requested_paths(self):
        for name in ('../outside.pdf', '/outside.pdf', 'C:/outside.pdf',
                     '..\\outside.pdf'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                select_entry(self.archive, 'A project.zip', name,
                             self.root / 'output' / 'figure.pdf')
        with self.assertRaises(ValueError):
            select_entry(self.archive, '../project.zip', 'figures/a.pdf',
                         self.root / 'output' / 'figure.pdf')
        self.assertFalse((self.root / 'output').exists())

    def test_inventory_rejects_unsafe_archive_paths(self):
        for project, entry in (('safe.zip', '../outside.pdf'),
                               ('../unsafe.zip', 'figures/a.pdf')):
            with self.subTest(project=project, entry=entry):
                self.make_archive({project: {entry: b'abc'}})
                with self.assertRaises(ValueError):
                    inventory_archive(self.archive)

    def test_non_zip_outer_rejected(self):
        self.archive.write_bytes(b'not a zip')
        with self.assertRaises(zipfile.BadZipFile):
            inventory_archive(self.archive)
        with self.assertRaises(zipfile.BadZipFile):
            select_entry(self.archive, 'A project.zip', 'figures/a.pdf',
                         self.root / 'output' / 'figure.pdf')
        self.assertFalse((self.root / 'output').exists())

    def test_cli_inventory_is_deterministic_yaml_compatible_json(self):
        command = [sys.executable, 'scripts/research_assets.py', 'inventory',
                   '--archive', str(self.archive)]
        first = subprocess.run(command, capture_output=True, text=True, check=True)
        second = subprocess.run(command, capture_output=True, text=True, check=True)
        self.assertEqual(first.stdout, second.stdout)
        result = json.loads(first.stdout)
        self.assertEqual(result['archive_sha256'], hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.assertEqual((result['project_count'], result['figure_count'], result['motion_count']),
                         (2, 3, 1))

    def test_cli_extract_reports_selected_entry_checksum(self):
        destination = self.root / 'output' / 'figure.pdf'
        result = subprocess.run([sys.executable, 'scripts/research_assets.py', 'extract',
                                 '--archive', str(self.archive), '--project', 'A project.zip',
                                 '--entry', 'figures/a.pdf', '--output', str(destination)],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['sha256'],
                         'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        self.assertEqual(destination.read_bytes(), b'abc')

    def prepare(self, **options):
        self.assertTrue(callable(getattr(research_assets, 'prepare_figure', None)),
                        'PDF preparation is not implemented')
        with patch.object(research_assets, 'REPOSITORY_ROOT', self.root):
            return research_assets.prepare_figure(
                self.archive, 'A project.zip', 'figures/a.pdf',
                options.pop('output', self.root / 'content/publications/paper/media/figure.png'),
                **options)

    def render_png(self, command, **options):
        # Poppler is external; keep real extraction, validation and PNG decoding.
        from PIL import Image
        self.assertIsInstance(command, list)
        self.assertEqual(command[0:5], ['pdftoppm', '-singlefile', '-png', '-r', '180'])
        self.assertEqual(options, {'check': True, 'capture_output': True, 'text': True})
        self.assertEqual(Path(command[-2]).read_bytes(), b'abc')
        self.render_temp = Path(command[-2]).parent
        Image.new('RGB', (32, 24), 'white').save(command[-1] + '.png')

    def test_prepare_safe_poppler_arguments_and_source_metadata(self):
        with patch('shutil.which', return_value='pdftoppm'), \
                patch('subprocess.run', side_effect=self.render_png):
            result = self.prepare()
        self.assertEqual((result['width'], result['height'], result['source_page']), (32, 24, 1))
        self.assertEqual(result['source_sha256'],
                         'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        self.assertTrue(Path(result['output']).is_file())
        self.assertFalse(self.render_temp.exists())

    def test_prepare_rejects_outputs_outside_publication_tree(self):
        for output in (self.root / 'figure.png',
                       self.root / 'content/publications/../figure.png',
                       self.root / 'content/publications/paper/figure.pdf'):
            with self.subTest(output=output), self.assertRaises(ValueError):
                self.prepare(output=output)
        self.assertFalse((self.root / 'content').exists())

    def test_prepare_rejects_invalid_dpi_and_page(self):
        for dpi in (0, 71, 601, -180):
            with self.subTest(dpi=dpi), self.assertRaises(ValueError):
                self.prepare(dpi=dpi)
        with self.assertRaises(ValueError):
            self.prepare(page=0)

    def test_prepare_missing_poppler_is_actionable_and_creates_no_output(self):
        with patch('shutil.which', return_value=None), self.assertRaisesRegex(
                FileNotFoundError, 'pdftoppm'):
            self.prepare()
        self.assertFalse((self.root / 'content').exists())

    def test_prepare_missing_render_is_rejected_and_temp_is_removed(self):
        def no_output(command, **options):
            self.render_temp = Path(command[-2]).parent
        with patch('shutil.which', return_value='pdftoppm'), \
                patch('subprocess.run', side_effect=no_output), self.assertRaises(FileNotFoundError):
            self.prepare()
        self.assertFalse(self.render_temp.exists())
        self.assertFalse((self.root / 'content').exists())

    def test_prepare_poppler_error_preserves_destination_and_cleans_temp(self):
        def fail(command, **options):
            self.render_temp = Path(command[-2]).parent
            raise subprocess.CalledProcessError(1, command, stderr='bad PDF')
        with patch('shutil.which', return_value='pdftoppm'), \
                patch('subprocess.run', side_effect=fail), self.assertRaises(subprocess.CalledProcessError):
            self.prepare()
        self.assertFalse(self.render_temp.exists())
        self.assertFalse((self.root / 'content').exists())

    def test_prepare_requires_replace_for_existing_output(self):
        output = self.root / 'content/publications/paper/media/figure.png'
        output.parent.mkdir(parents=True)
        output.write_bytes(b'keep me')
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(output.read_bytes(), b'keep me')
        with patch('shutil.which', return_value='pdftoppm'), \
                patch('subprocess.run', side_effect=self.render_png):
            self.prepare(replace=True)
        self.assertTrue(output.read_bytes().startswith(b'\x89PNG'))

    def test_prepare_explicit_page_is_passed_to_poppler(self):
        def render_page(command, **options):
            self.assertEqual(command[5:9], ['-f', '2', '-l', '2'])
            self.render_png(command, **options)
        with patch('shutil.which', return_value='pdftoppm'), \
                patch('subprocess.run', side_effect=render_page):
            self.assertEqual(self.prepare(page=2)['source_page'], 2)

    def test_prepare_invalid_png_is_rejected(self):
        def bad_png(command, **options):
            self.render_temp = Path(command[-2]).parent
            Path(command[-1] + '.png').write_bytes(b'not an image')
        with patch('shutil.which', return_value='pdftoppm'), \
                patch('subprocess.run', side_effect=bad_png), self.assertRaises(OSError):
            self.prepare()
        self.assertFalse(self.render_temp.exists())
        self.assertFalse((self.root / 'content').exists())

    def test_prepare_failed_publication_copy_preserves_existing_asset(self):
        output = self.root / 'content/publications/paper/media/figure.png'
        output.parent.mkdir(parents=True)
        output.write_bytes(b'keep me')
        with patch('shutil.which', return_value='pdftoppm'), \
                patch('subprocess.run', side_effect=self.render_png), \
                patch('shutil.copyfile', side_effect=OSError('copy failed')), \
                self.assertRaises(OSError):
            self.prepare(replace=True)
        self.assertEqual(output.read_bytes(), b'keep me')
        self.assertEqual(list(output.parent.iterdir()), [output])
        self.assertFalse(self.render_temp.exists())


if __name__ == '__main__':
    unittest.main()
