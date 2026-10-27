"""Minimal Markdown -> .docx writer (stdlib only).

Application forms (Greenhouse included) accept .pdf/.doc/.docx/.txt — not
.md. The tailored resume lives as Markdown; this converts it to a valid
.docx for upload, keeping headings and bullets as plain paragraphs and
stripping Markdown markers. No external dependencies.
"""
from __future__ import annotations
import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


def _clean(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^#{1,6}\s*", "", line)          # headings
    line = re.sub(r"^[-*]\s+", "• ", line)           # bullets
    line = line.replace("**", "").replace("__", "")  # bold markers
    return line


def _paragraph(text: str, bold: bool = False) -> str:
    rpr = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return (f'<w:p><w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t>'
            f"</w:r></w:p>")


def markdown_to_docx(md_text: str, out_path: str | Path) -> Path:
    paras = []
    for raw in md_text.splitlines():
        line = _clean(raw)
        if not line:
            continue
        is_heading = raw.lstrip().startswith("#") or (
            line.isupper() and len(line) < 80)
        paras.append(_paragraph(line, bold=is_heading))
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(paras)}</w:body></w:document>")
    out = Path(out_path)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/document.xml", document)
    return out
