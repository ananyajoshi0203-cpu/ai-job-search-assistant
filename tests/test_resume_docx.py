import zipfile
from jobhunt.resume_docx import markdown_to_docx


def test_markdown_to_docx_is_valid(tmp_path):
    md = "# ALEX RIVERA\n## PROJECTS\n- Built a **RAG** chatbot with FAISS\nPlain line."
    out = markdown_to_docx(md, tmp_path / "r.docx")
    assert zipfile.is_zipfile(out)
    with zipfile.ZipFile(out) as z:
        xml = z.read("word/document.xml").decode()
    assert "ALEX RIVERA" in xml and "RAG" in xml
    assert "**" not in xml and "##" not in xml


def test_upload_resume_path_converts_md(tmp_path):
    from jobhunt.prefill import upload_resume_path
    md = tmp_path / "tailored.md"
    md.write_text("# ALEX RIVERA\nPython, RAG.")
    out = upload_resume_path(str(md))
    assert out.endswith(".docx") and zipfile.is_zipfile(out)
    assert upload_resume_path(None) is None
    pdf = tmp_path / "r.pdf"
    pdf.write_bytes(b"%PDF")
    assert upload_resume_path(str(pdf)) == str(pdf)
