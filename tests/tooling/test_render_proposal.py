"""Tests for Markdown->DOCX conversion, not application crypto."""
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET
import io
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from render_proposal import parse_markdown, render_bytes, PackageBuilder, DEFAULT_SOURCE, DEFAULT_OUTPUT
from validate_proposal_sync import NS, docx_records, markdown_records


class RenderProposalTests(unittest.TestCase):
    def test_current_proposal_roundtrip_content(self):
        with zipfile.ZipFile(io.BytesIO(render_bytes(DEFAULT_SOURCE))) as z:
            doc=ET.fromstring(z.read('word/document.xml'))
            actual=docx_records(doc.find('w:body',NS))
        expected=markdown_records(DEFAULT_SOURCE.read_text(encoding='utf-8'))[0]
        self.assertEqual(actual,expected)

    def test_deterministic_output(self):
        first=render_bytes(DEFAULT_SOURCE)
        self.assertEqual(first,render_bytes(DEFAULT_SOURCE))
        self.assertEqual(first,DEFAULT_OUTPUT.read_bytes())

    def test_markdown_change_propagates_without_reading_old_docx(self):
        with TemporaryDirectory(prefix='medshare-render-test-') as temp:
            root=Path(temp); source=root/'proposal.md'
            source.write_text('# Title\n\n| Field | Value |\n|---|---|\n| A | old |\n',encoding='utf-8')
            old=render_bytes(source,root)
            source.write_text(source.read_text().replace('old','new'),encoding='utf-8')
            new=render_bytes(source,root)
            self.assertNotEqual(old,new)
            with zipfile.ZipFile(io.BytesIO(new)) as z:
                body=ET.fromstring(z.read('word/document.xml')).find('w:body',NS)
                self.assertIn(('row',('A','new')),docx_records(body))

    def test_cell_count_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_markdown('| A | B |\n|---|---|\n| C |')

    def test_unsupported_block_rejected(self):
        with self.assertRaises(ValueError): parse_markdown('~~~python\npass\n~~~')
        with self.assertRaises(ValueError): parse_markdown('<script>no</script>')

    def test_escaped_pipe(self):
        rows=parse_markdown('| A | B |\n|---|---|\n| A'+chr(92)+'|B | C |')[0][1]
        self.assertEqual(rows[1],['A|B','C'])

    def test_wrapped_paragraph(self):
        self.assertEqual(parse_markdown('First line\nnext line\n'),[('p','First line next line')])

    def test_local_asset_cannot_escape_root(self):
        with TemporaryDirectory(prefix='medshare-asset-test-') as temp:
            root=Path(temp); builder=PackageBuilder(root/'proposal.md',root)
            with self.assertRaises(ValueError): builder.local_path('../outside.png')
            with self.assertRaises(ValueError): builder.local_path('missing.png')

    def test_unsafe_hyperlink_rejected(self):
        with TemporaryDirectory(prefix='medshare-link-test-') as temp:
            root=Path(temp); source=root/'proposal.md'
            source.write_text('[no](file:///outside.txt)',encoding='utf-8')
            with self.assertRaises(ValueError): render_bytes(source,root)

    def test_images_local_and_no_external_relationship(self):
        with zipfile.ZipFile(io.BytesIO(render_bytes(DEFAULT_SOURCE))) as z:
            rels=ET.fromstring(z.read('word/_rels/document.xml.rels'))
            images=[r for r in rels if r.attrib['Type'].endswith('/image')]
            self.assertEqual(len(images),2)
            self.assertTrue(all(r.attrib.get('TargetMode')!='External' for r in images))


if __name__=='__main__': unittest.main()
