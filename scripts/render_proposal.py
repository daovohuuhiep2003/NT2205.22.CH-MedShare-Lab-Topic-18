"""Build the canonical proposal DOCX from Markdown; standard library only.

Supported: headings, paragraphs, bold/emphasis, links, lists, tables, PNG images.
No network, Office, template DOCX or external dependency is required.
Unknown fenced code/HTML fails before overwriting the output.
"""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET
import argparse
import hashlib
import io
import json
import re
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'docs/proposal/project-proposal.md'
DEFAULT_OUTPUT = DEFAULT_SOURCE.with_suffix('.docx')
NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
WIDTH = 9354  # 16.5 cm in twentieths of a point, within A4 margins.


def element(tag, text=None, **attrs):
    def qualified(name):
        prefix, local = name.split(':')
        return '{' + NS[prefix] + '}' + local
    node = ET.Element(qualified(tag), {qualified(k): str(v) for k, v in attrs.items()})
    if text is not None:
        node.text = text
    return node


def xml(node):
    return ET.tostring(node, encoding='utf-8', xml_declaration=True)


def parse_markdown(text):
    lines = text.splitlines()
    blocks, pending = [], []

    def flush():
        if pending:
            blocks.append(('p', ' '.join(pending)))
            pending.clear()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            flush(); i += 1; continue
        if line.startswith(('~~~', chr(96) * 3, '<')):
            raise ValueError('Unsupported block syntax at line ' + str(i + 1))
        if line.startswith('|'):
            flush(); rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [x.strip().replace(chr(92)+'|', '|')
                         for x in re.split(r'(?<!\\)\|', lines[i].strip())[1:-1]]
                if not all(re.fullmatch(r':?-+:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            if not rows or any(len(row) != len(rows[0]) for row in rows):
                raise ValueError('Malformed table')
            blocks.append(('table', rows)); continue
        image = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        heading = re.match(r'^(#{1,6}) (.+)$', line)
        listing = re.match(r'^(-|\d+\.) (.+)$', line)
        if image:
            flush(); blocks.append(('image', image.groups()))
        elif heading:
            flush(); blocks.append(('heading', (len(heading[1]), heading[2])))
        elif listing:
            flush(); blocks.append(('list', listing.groups()))
        elif line.startswith('*') and line.endswith('*') and not line.startswith('**'):
            flush(); blocks.append(('caption', line[1:-1]))
        else:
            pending.append(line)
        i += 1
    flush()
    return blocks


def run(parent, text, bold=False, italic=False, color=None):
    r = element('w:r')
    props = element('w:rPr')
    if bold: props.append(element('w:b'))
    if italic: props.append(element('w:i'))
    if color: props.append(element('w:color', **{'w:val': color}))
    if len(props): r.append(props)
    t = element('w:t', text)
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    r.append(t); parent.append(r)


class PackageBuilder:
    def __init__(self, source, root):
        self.source, self.root = source.resolve(), root.resolve()
        self.files = {}
        self.rels = ET.Element('Relationships', xmlns=REL)
        self.image_count = 0

    def relationship(self, kind, target, external=False):
        rid = 'rId' + str(len(self.rels) + 1)
        attrs = {'Id': rid, 'Type': NS['r'] + '/' + kind, 'Target': target}
        if external: attrs['TargetMode'] = 'External'
        ET.SubElement(self.rels, 'Relationship', attrs)
        return rid

    def local_path(self, target):
        path = (self.source.parent / unquote(target.split('#')[0])).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise ValueError('Missing/out-of-repository local asset: ' + target)
        return path

    def inline(self, parent, text, bold=False, italic=False, color=None):
        pattern = r'(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)|<br\s*/?>)'
        for part in re.split(pattern, text):
            match = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', part)
            if match:
                label, target = match.groups()
                if not urlsplit(target).scheme and not target.startswith('#'):
                    self.local_path(target)
                if urlsplit(target).scheme not in ('', 'http', 'https', 'mailto'):
                    raise ValueError('Unsupported hyperlink scheme')
                link = element('w:hyperlink', **{'r:id': self.relationship('hyperlink', target, True)})
                run(link, label, bold, italic, color or '245C86'); parent.append(link)
            elif part.startswith('**') and part.endswith('**'):
                run(parent, part[2:-2], True, italic, color)
            elif part.startswith('<br'):
                r = element('w:r'); r.append(element('w:br')); parent.append(r)
            elif part:
                run(parent, part.replace(chr(96), ''), bold, italic, color)

    def paragraph(self, text='', style=None, **options):
        p = element('w:p'); props = element('w:pPr')
        if style: props.append(element('w:pStyle', **{'w:val': style}))
        for name in ('keepNext', 'pageBreakBefore', 'keepLines'):
            if options.get(name): props.append(element('w:' + name))
        if len(props): p.append(props)
        self.inline(p, text)
        return p

    def image(self, alt, target):
        path = self.local_path(target)
        data = path.read_bytes()
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Only PNG proposal images are supported')
        w, h = struct.unpack('>II', data[16:24])
        if not w or not h: raise ValueError('Invalid PNG size')
        self.image_count += 1
        name = 'image' + str(self.image_count) + '.png'
        self.files['word/media/' + name] = data
        rid = self.relationship('image', 'media/' + name)
        cx = WIDTH * 635; cy = round(cx * h / w)
        if cy > 7000000:
            cx = round(cx * 7000000 / cy); cy = 7000000
        p = self.paragraph(keepNext=True, pageBreakBefore=self.image_count > 1)
        r = element('w:r'); p.append(r)
        drawing = element('w:drawing'); r.append(drawing)
        inline = element('wp:inline'); drawing.append(inline)
        inline.append(ET.Element('{' + NS['wp'] + '}extent', cx=str(cx), cy=str(cy)))
        inline.append(ET.Element('{' + NS['wp'] + '}docPr', id=str(self.image_count), name=path.name, descr=alt))
        graphic = element('a:graphic'); inline.append(graphic)
        gd = ET.SubElement(graphic, '{' + NS['a'] + '}graphicData', uri=NS['pic'])
        pic = element('pic:pic'); gd.append(pic)
        nv = element('pic:nvPicPr'); pic.append(nv)
        ET.SubElement(nv, '{'+NS['pic']+'}cNvPr', id='0', name=path.name)
        nv.append(element('pic:cNvPicPr'))
        fill = element('pic:blipFill'); pic.append(fill)
        fill.append(element('a:blip', **{'r:embed': rid}))
        stretch = element('a:stretch'); stretch.append(element('a:fillRect')); fill.append(stretch)
        sp = element('pic:spPr'); pic.append(sp)
        xf = element('a:xfrm'); sp.append(xf)
        ET.SubElement(xf, '{'+NS['a']+'}off', x='0', y='0')
        ET.SubElement(xf, '{'+NS['a']+'}ext', cx=str(cx), cy=str(cy))
        geom = ET.SubElement(sp, '{'+NS['a']+'}prstGeom', prst='rect'); geom.append(element('a:avLst'))
        return p

    def table(self, rows):
        header = rows[0]
        ratios = [1] * len(header)
        if header[0] in ('ID', 'Mã', 'Tuần'): ratios = [.15, .425, .425]
        elif len(header) == 2: ratios = [.27, .73]
        elif header[0] == 'Trường / nhóm dữ liệu': ratios = [.23, .26, .51]
        widths = [round(WIDTH*x/sum(ratios)) for x in ratios]
        widths[-1] = WIDTH - sum(widths[:-1])
        table = element('w:tbl'); props = element('w:tblPr'); table.append(props)
        props.append(element('w:tblW', **{'w:w':WIDTH, 'w:type':'dxa'}))
        props.append(element('w:tblLayout', **{'w:type':'fixed'}))
        borders = element('w:tblBorders'); props.append(borders)
        for edge in ('top','left','bottom','right','insideH','insideV'):
            borders.append(element('w:'+edge, **{'w:val':'single','w:sz':4,'w:color':'B8C7D8'}))
        grid = element('w:tblGrid'); table.append(grid)
        for width in widths: grid.append(element('w:gridCol', **{'w:w':width}))
        for i,row in enumerate(rows):
            tr = element('w:tr'); table.append(tr)
            rp = element('w:trPr'); rp.append(element('w:cantSplit')); tr.append(rp)
            if i==0: rp.append(element('w:tblHeader'))
            for text,width in zip(row,widths):
                c = element('w:tc'); tr.append(c)
                cp = element('w:tcPr'); c.append(cp)
                cp.append(element('w:tcW', **{'w:w':width,'w:type':'dxa'}))
                if i==0 or i%2==0:
                    cp.append(element('w:shd', **{'w:fill':'314E6E' if i==0 else 'F1F5FA'}))
                p=self.paragraph(style='TableText')
                self.inline(p,text,bold=i==0,color='FFFFFF' if i==0 else None)
                c.append(p)
        return table


def styles_xml():
    styles = element('w:styles')
    defaults = element('w:docDefaults'); styles.append(defaults)
    rd = element('w:rPrDefault'); defaults.append(rd)
    rp = element('w:rPr'); rd.append(rp)
    rp.append(element('w:rFonts', **{'w:ascii':'Calibri','w:hAnsi':'Calibri'}))
    rp.append(element('w:sz', **{'w:val':22}))
    rp.append(element('w:lang', **{'w:val':'vi-VN'}))
    for name,size,bold in [('Normal',22,False),('Title',46,True),('Subtitle',30,True),
                           ('Heading1',28,True),('Heading2',24,True),('Heading3',23,True),
                           ('Caption',19,False),('TableText',21,False)]:
        st=element('w:style', **{'w:type':'paragraph','w:styleId':name}); styles.append(st)
        st.append(element('w:name', **{'w:val':name}))
        if name!='Normal': st.append(element('w:basedOn', **{'w:val':'Normal'}))
        pp=element('w:pPr'); st.append(pp)
        pp.append(element('w:spacing', **{'w:after':60 if name=='TableText' else 120,
                                        'w:before':180 if name.startswith('Heading') else 0,
                                        'w:line':252,'w:lineRule':'auto'}))
        pp.append(element('w:widowControl'))
        if bold: pp.append(element('w:keepNext')); pp.append(element('w:keepLines'))
        if name.startswith('Heading'):
            pp.append(element('w:outlineLvl', **{'w:val':int(name[-1])-1}))
        rp=element('w:rPr'); st.append(rp); rp.append(element('w:sz', **{'w:val':size}))
        if bold:
            rp.append(element('w:b')); rp.append(element('w:color', **{'w:val':'243C5A'}))
        if name=='Caption': rp.append(element('w:i'))
    return xml(styles)


def numbering_xml():
    numbering=element('w:numbering')
    for index,fmt,label in [(1,'bullet','•'),(2,'decimal','%1.')]:
        abstract=element('w:abstractNum', **{'w:abstractNumId':index}); numbering.append(abstract)
        lvl=element('w:lvl', **{'w:ilvl':0}); abstract.append(lvl)
        lvl.append(element('w:start', **{'w:val':1}))
        lvl.append(element('w:numFmt', **{'w:val':fmt}))
        lvl.append(element('w:lvlText', **{'w:val':label}))
        pp=element('w:pPr'); lvl.append(pp)
        pp.append(element('w:ind', **{'w:left':360,'w:hanging':240}))
        num=element('w:num', **{'w:numId':index}); numbering.append(num)
        num.append(element('w:abstractNumId', **{'w:val':index}))
    return xml(numbering)


def render_bytes(source, root=ROOT):
    source=Path(source).resolve(); root=Path(root).resolve()
    content=source.read_text(encoding='utf-8-sig')
    blocks=parse_markdown(content)
    b=PackageBuilder(source,root)
    doc=element('w:document'); body=element('w:body'); doc.append(body)
    for kind,value in blocks:
        if kind=='heading':
            level,text=value
            style='Title' if level==1 else ('Subtitle' if len(body)==1 else 'Heading'+str(min(level-1,3)))
            body.append(b.paragraph(text,style))
        elif kind=='table': body.append(b.table(value))
        elif kind=='image': body.append(b.image(*value))
        elif kind=='list':
            p=b.paragraph(value[1]); pp=element('w:pPr'); p.insert(0,pp)
            np=element('w:numPr'); pp.append(np)
            np.append(element('w:ilvl', **{'w:val':0}))
            np.append(element('w:numId', **{'w:val':1 if value[0]=='-' else 2}))
            body.append(p)
        else: body.append(b.paragraph(value,'Caption' if kind=='caption' else None))
    b.relationship('styles','styles.xml')
    b.relationship('numbering','numbering.xml')
    footer_id=b.relationship('footer','footer1.xml')
    footer=element('w:ftr'); fp=b.paragraph('Topic 18 | NT2205.11.CH     Trang '); footer.append(fp)
    for instr in ('PAGE','NUMPAGES'):
        field=element('w:fldSimple', **{'w:instr':instr}); fp.append(field); run(field,'1')
        if instr=='PAGE': run(fp,' / ')
    sect=element('w:sectPr'); body.append(sect)
    sect.append(element('w:footerReference', **{'w:type':'default','r:id':footer_id}))
    sect.append(element('w:pgSz', **{'w:w':11906,'w:h':16838}))
    sect.append(element('w:pgMar', **{'w:top':1077,'w:right':1276,'w:bottom':1021,'w:left':1276,
                                     'w:header':454,'w:footer':454,'w:gutter':0}))
    ct=ET.Element('Types',xmlns=CT)
    for ext,mime in [('rels','application/vnd.openxmlformats-package.relationships+xml'),
                     ('xml','application/xml'),('png','image/png')]:
        ET.SubElement(ct,'Default',Extension=ext,ContentType=mime)
    for part,kind in [('document','document.main'),('styles','styles'),('numbering','numbering'),('footer1','footer')]:
        ET.SubElement(ct,'Override',PartName='/word/'+part+'.xml',
                      ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.'+kind+'+xml')
    rels=ET.Element('Relationships',xmlns=REL)
    ET.SubElement(rels,'Relationship',Id='rId1',Type=NS['r']+'/officeDocument',Target='word/document.xml')
    b.files.update({'[Content_Types].xml':xml(ct),'_rels/.rels':xml(rels),
                    'word/document.xml':xml(doc),'word/styles.xml':styles_xml(),
                    'word/numbering.xml':numbering_xml(),
                    'word/footer1.xml':xml(footer),'word/_rels/document.xml.rels':xml(b.rels)})
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(b.files.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=0  # Stable metadata across Windows and Linux.
            info.external_attr=0o600 << 16
            z.writestr(info,data)
    return out.getvalue()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Read-only deterministic artifact check')
    args=parser.parse_args()
    data=render_bytes(DEFAULT_SOURCE)
    if args.check:
        same=DEFAULT_OUTPUT.is_file() and DEFAULT_OUTPUT.read_bytes()==data
        print(json.dumps({'canonical_docx_matches_markdown':same,'read_only':True}))
        return 0 if same else 1
    # Build/parse everything before replacing the explicitly selected generated file.
    temporary=DEFAULT_OUTPUT.with_name(DEFAULT_OUTPUT.name+'.tmp')
    temporary.write_bytes(data)
    temporary.replace(DEFAULT_OUTPUT)
    print(json.dumps({'generated':DEFAULT_OUTPUT.relative_to(ROOT).as_posix(),
                      'source_sha256':hashlib.sha256(DEFAULT_SOURCE.read_bytes()).hexdigest(),
                      'bytes':len(data)}))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
