"""Read-only DOCX/Markdown checks; Python standard library only.

Run: python scripts/validate_proposal_sync.py [--self-test]
Does not verify Word pagination, external URLs or cryptographic behavior.
"""
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET
import hashlib
import json
import posixpath
import re
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_DIR = Path('docs/proposal')
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
W = '{' + NS['w'] + '}'


def normalized(text):
    return ' '.join(text.split())


def plain_markdown(text):
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = text.replace('**', '').replace(chr(96), '')
    if text.startswith('*') and text.endswith('*'):
        text = text[1:-1]
    return normalized(text.replace(chr(92) + '|', '|').replace('<br>', ' '))


def markdown_records(text):
    result, images = [], []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        image = re.fullmatch(r'!\[[^\]]*\]\(([^)]+)\)', line)
        if image:
            images.append(unquote(image.group(1)))
            continue
        if line.startswith('|'):
            cells = re.split(r'(?<!\\)\|', line)[1:-1]
            if all(re.fullmatch(r'\s*:?-+:?\s*', c) for c in cells):
                continue
            result.append(('row', tuple(plain_markdown(c.strip()) for c in cells)))
            continue
        heading = re.match(r'^(#{1,6}) (.+)$', line)
        line = heading.group(2) if heading else re.sub(r'^(?:- |\d+\. )', '', line)
        result.append(('p', plain_markdown(line)))
    return result, images


def xml_text(node):
    return normalized(''.join(n.text or '' for n in node.iter(W + 't')))


def docx_records(body):
    result = []
    for node in body:
        if node.tag == W + 'p':
            text = xml_text(node)
            if text:
                result.append(('p', text))
        elif node.tag == W + 'tbl':
            for row in node.findall('w:tr', NS):
                cells = tuple(normalized(' '.join(xml_text(p) for p in c.findall('w:p', NS)))
                              for c in row.findall('w:tc', NS))
                result.append(('row', cells))
    return result


def is_external(target):
    return bool(re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', target))


def validate(root):
    errors = []
    base = root / PROPOSAL_DIR
    text = (base / 'project-proposal.md').read_text(encoding='utf-8')
    md_records, image_paths = markdown_records(text)
    with zipfile.ZipFile(base / 'project-proposal.docx') as package:
        bad = package.testzip()
        if bad:
            errors.append('DOCX CRC failure: ' + bad)
        xml_parts = [p for p in package.namelist() if p.endswith(('.xml', '.rels'))]
        for name in xml_parts:
            ET.fromstring(package.read(name))
        document = ET.fromstring(package.read('word/document.xml'))
        body = document.find('w:body', NS)
        records = docx_records(body)
        if records != md_records:
            errors.append('DOCX/Markdown ordered content mismatch')
            for i, (left, right) in enumerate(zip(records, md_records)):
                if left != right:
                    errors.append('First mismatched content record: ' + str(i + 1))
                    break
        rels = ET.fromstring(package.read('word/_rels/document.xml.rels'))
        relationships = {r.attrib['Id']: r.attrib for r in rels}
        images = document.findall('.//a:blip', NS)
        if len(images) != len(image_paths) or len(images) != 2:
            errors.append('Expected exactly two images in both formats')
        for node, filename in zip(images, image_paths):
            rid = node.attrib['{' + NS['r'] + '}embed']
            target = relationships[rid]['Target']
            embedded = package.read(posixpath.normpath(posixpath.join('word', target)))
            local = base / filename
            if not local.is_file() or hashlib.sha256(embedded).digest() != hashlib.sha256(local.read_bytes()).digest():
                errors.append('Embedded/local image mismatch: ' + filename)
        for rel in relationships.values():
            if rel.get('Type', '').endswith('/hyperlink'):
                target = rel['Target']
                if not is_external(target) and not (base / unquote(target.split('#')[0])).exists():
                    errors.append('Broken DOCX local link: ' + target)
        for tag in ('ins', 'del', 'commentReference'):
            if document.find('.//w:' + tag, NS) is not None:
                errors.append('Unexpected tracked edits/comments: ' + tag)
        for table in body.findall('w:tbl', NS):
            if table.find('w:tr/w:trPr/w:tblHeader', NS) is None:
                errors.append('Missing repeating table header')
            for row in table.findall('w:tr', NS):
                if row.find('w:trPr/w:cantSplit', NS) is None:
                    errors.append('Table row can split across pages')
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if not is_external(target) and not target.startswith('#'):
            if not (base / unquote(target.split('#')[0])).exists():
                errors.append('Broken Markdown local link: ' + target)
    from validate_docs import phase_errors
    errors.extend(phase_errors(text))
    for required in ('7.2 Nghiên cứu liên quan', '7.3 Chốt phạm vi E5',
                     '2.1 Ma trận dữ liệu', '8.3 Nguồn lực', 'Phụ lục A.',
                     'Mật mã học và ứng dụng', 'Thạc sĩ An toàn thông tin',
                     '26848038', '26848065', '432–528', 'root/hypervisor'):
        if required.lower() not in text.lower():
            errors.append('Missing required proposal content: ' + required)
    for forbidden in ('một học viên dành', 'An toàn bảo mật hệ thống thông tin',
                      'Thành viên A', 'Thành viên B', 'Một số trường hợp có thể sẽ'):
        if forbidden in text:
            errors.append('Stale scope or individual assignment: ' + forbidden)
    reference_ids = re.findall(r'^\[(G|T|\d+)\] \[', text, re.M)
    if set(reference_ids) != {'G', 'T', *(str(i) for i in range(1, 16))}:
        errors.append('Incomplete reference IDs')
    if chr(65533) in text:
        errors.append('Unicode replacement character')
    return {'content_records': len(records), 'markdown_records': len(md_records),
            'tables': len(body.findall('w:tbl', NS)), 'images': len(images),
            'references': len(reference_ids), 'docx_xml_parts': len(xml_parts),
            'ordered_content_matches': records == md_records,
            'errors': errors, 'word_pagination': 'NOT_VERIFIED',
            'external_urls': 'NOT_VERIFIED', 'application_security': 'NOT_RUN'}


class SyncTests(unittest.TestCase):
    def test_inline_links_and_bold(self):
        self.assertEqual(plain_markdown('**Tên:** [Nguồn](https://example.org).'), 'Tên: Nguồn.')

    def test_heading_keeps_section_number(self):
        self.assertEqual(markdown_records('## 1. System Analysis')[0], [('p', '1. System Analysis')])

    def test_list_number_is_presentation(self):
        self.assertEqual(markdown_records('1. Nội dung\n- Khác')[0], [('p', 'Nội dung'), ('p', 'Khác')])

    def test_table_header_separator_and_escaped_pipe(self):
        text = '| H | K |\n|---|---|\n| A' + chr(92) + '|B | C |'
        self.assertEqual(markdown_records(text)[0], [('row', ('H', 'K')), ('row', ('A|B', 'C'))])

    def test_images_and_caption(self):
        records, images = markdown_records('![Hình](docs/a%20b.png)\n*Hình 1.*')
        self.assertEqual(images, ['docs/a b.png'])
        self.assertEqual(records, [('p', 'Hình 1.')])

    def test_xml_hyperlink_text_order(self):
        xml = '<w:body xmlns:w="' + NS['w'] + '"><w:p><w:r><w:t>A </w:t></w:r>'
        xml += '<w:hyperlink><w:r><w:t>B</w:t></w:r></w:hyperlink></w:p></w:body>'
        self.assertEqual(docx_records(ET.fromstring(xml)), [('p', 'A B')])

    def test_changed_table_cell_is_detected(self):
        self.assertNotEqual(markdown_records('| A | B |')[0], markdown_records('| A | C |')[0])

    def test_external_url_detection(self):
        self.assertTrue(is_external('https://example.org'))
        self.assertFalse(is_external('docs/a.md'))


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        result = validate(ROOT)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        sys.exit(1 if result['errors'] else 0)
