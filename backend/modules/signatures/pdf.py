"""
Signed copy of a document, as one PDF:

  1. The original pages (PDF uploads), each with a small footer naming the
     signing record, so a printed page can be traced back to it.
     TXT uploads are typeset onto pages; DOCX can't be rendered here, so the
     certificate notes that the original is attached instead.
  2. Signature certificate pages: who signed, their typed signature, when,
     from which IP and browser, the consent they gave, and the audit trail.
  3. The original file embedded as an attachment, byte for byte, so anyone
     can check it against the SHA-256 printed on the certificate.
"""
import io
import os
from datetime import datetime, timezone
from typing import Optional
from xml.sax.saxutils import escape

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    KeepTogether, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle,
)

FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "MrsSaintDelafield-Regular.ttf")
SIGNATURE_FONT = "Helvetica-Oblique"
try:
    pdfmetrics.registerFont(TTFont("Signature", os.path.abspath(FONT_PATH)))
    SIGNATURE_FONT = "Signature"
except Exception:  # pragma: no cover - font missing: fall back to italic
    pass

INK = colors.HexColor("#1b1f2a")
MUTED = colors.HexColor("#5b6272")
RULE = colors.HexColor("#d9dce3")
OK = colors.HexColor("#1f7a4d")
BAD = colors.HexColor("#b42318")

EVENT_LABEL = {
    "created": "Sent for signing",
    "link_reissued": "New signing link issued",
    "emailed": "Email sent",
    "viewed": "Opened the document",
    "signed": "Signed",
    "declined": "Declined to sign",
    "completed": "Completed - everyone signed",
    "cancelled": "Cancelled",
}

_s = {
    "eyebrow": ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=MUTED, spaceAfter=4),
    "title": ParagraphStyle("title", fontName="Times-Bold", fontSize=20, leading=24, textColor=INK, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Times-Bold", fontSize=14, leading=18, textColor=INK, spaceBefore=14, spaceAfter=6),
    "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=MUTED),
    "value": ParagraphStyle("value", fontName="Helvetica", fontSize=9, leading=12, textColor=INK),
    "mono": ParagraphStyle("mono", fontName="Courier", fontSize=8, leading=10, textColor=INK),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9, leading=12, textColor=INK, alignment=TA_LEFT),
    "sig": ParagraphStyle("sig", fontName=SIGNATURE_FONT, fontSize=30, leading=36, textColor=INK),
}


def _p(text, style="value") -> Paragraph:
    return Paragraph(escape(str(text)) if text not in (None, "") else "-", _s[style])


def _utc(v) -> str:
    if not v:
        return "-"
    if isinstance(v, str):
        v = datetime.fromisoformat(v.replace("Z", "+00:00"))
    if v.tzinfo is None:
        v = v.replace(tzinfo=timezone.utc)
    return v.astimezone(timezone.utc).strftime("%d %b %Y, %H:%M:%S UTC")


def _browser(ua: Optional[str]) -> str:
    if not ua:
        return "-"
    name = next((n for k, n in (("Edg/", "Edge"), ("OPR/", "Opera"), ("Chrome/", "Chrome"), ("Firefox/", "Firefox"), ("Safari/", "Safari")) if k in ua), None)
    os_ = next((n for k, n in (("Windows", "Windows"), ("Android", "Android"), ("iPhone", "iOS"), ("iPad", "iOS"), ("Mac OS X", "macOS"), ("Linux", "Linux")) if k in ua), None)
    return f"{name} on {os_}" if name and os_ else ua[:60]


def _fields(rows, widths) -> Table:
    """A grid of label-over-value cells."""
    data = [[[_p(label, "label"), Spacer(1, 1), value if isinstance(value, Paragraph) else _p(value)] for label, value in row] for row in rows]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def certificate_pdf(env: dict, original_note: Optional[str]) -> bytes:
    """The certificate pages on their own."""
    buf = io.BytesIO()
    width = A4[0] - 40 * mm
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Signature certificate - {env['document_filename']}", author="ContractIQ",
    )
    completed = env["status"] == "completed"
    story = [
        _p("SIGNATURE CERTIFICATE" if completed else "SIGNING AUDIT TRAIL", "eyebrow"),
        _p(env["document_filename"], "title"),
        _fields(
            [
                [("Sent by", env.get("requested_by_name")), ("Sent", _utc(env.get("created_at")))],
                [("Status", "Completed - everyone signed" if completed else env["status"].capitalize()),
                 ("Completed" if completed else "Closed", _utc(env.get("closed_at")))],
            ],
            [width / 2, width / 2],
        ),
        _p("Record ID", "label"),
        Spacer(1, 2),
        _p(env["id"], "mono"),
        Spacer(1, 6),
        _p("Document fingerprint (SHA-256)", "label"),
        Spacer(1, 2),
        _p(env["document_sha256"], "mono"),
    ]
    if env.get("message"):
        story += [Spacer(1, 8), _p(f"Message to signers: {env['message']}", "body")]
    if original_note:
        story += [Spacer(1, 8), _p(original_note, "small")]

    story.append(_p("Signers", "h2"))
    for s in env["signers"]:
        state = {"signed": ("Signed", OK), "declined": ("Declined", BAD)}.get(s["status"], ("Not signed", MUTED))
        head = Table(
            [[Paragraph(f"<b>{escape(s['name'])}</b> <font color='#5b6272'>&middot; {escape(s['email'])}</font>", _s["value"]),
              Paragraph(f"<font color='#{state[1].hexval()[2:]}'><b>{state[0]}</b></font>", _s["value"])]],
            colWidths=[width - 30 * mm - 16, 30 * mm],
        )
        head.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
        block = [head]
        if s["status"] == "signed":
            sig = Table([[Paragraph(escape(s.get("typed_signature") or s["name"]), _s["sig"])]], colWidths=[width - 16])
            sig.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.8, INK), ("LEFTPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
            block += [Spacer(1, 4), sig]
        if s.get("decline_reason"):
            block += [Spacer(1, 4), _p(f"Reason: {s['decline_reason']}", "body")]
        block += [
            Spacer(1, 6),
            _fields(
                [
                    [("Opened", _utc(s.get("viewed_at"))), ("Declined" if s["status"] == "declined" else "Signed", _utc(s.get("acted_at")))],
                    [("IP address", s.get("ip_address")), ("Browser", _browser(s.get("user_agent")))],
                ],
                [(width - 16) / 2, (width - 16) / 2],
            ),
        ]
        if s.get("consent_text"):
            block.append(_p(f"Agreed to: “{s['consent_text']}”", "small"))
        card = Table([[block]], colWidths=[width])
        card.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, RULE), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                  ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        story += [KeepTogether(card), Spacer(1, 8)]

    story.append(_p("Audit trail", "h2"))
    rows = []
    for e in env.get("events") or []:
        what = f"<b>{escape(EVENT_LABEL.get(e['type'], e['type']))}</b>"
        if e.get("actor"):
            what += f" &middot; {escape(e['actor'])}"
        if e.get("detail"):
            what += f"<br/><font color='#5b6272'>{escape(e['detail'])}</font>"
        if e.get("ip_address"):
            what += f"<br/><font size='7' color='#5b6272'>{escape(e['ip_address'])} &middot; {escape(_browser(e.get('user_agent')))}</font>"
        rows.append([_p(_utc(e["created_at"]), "small"), Paragraph(what, _s["value"])])
    if rows:
        trail = Table(rows, colWidths=[42 * mm, width - 42 * mm], repeatRows=0)
        trail.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(trail)

    story += [
        Spacer(1, 12),
        _p(
            "Each signer opened a private link, typed their name and agreed to sign electronically. The fingerprint above "
            "is the SHA-256 of the exact file that was sent for signing; that file is attached to this PDF (open the "
            "attachments panel in your PDF reader) so anyone can check it, for example with sha256sum. This is a simple "
            "electronic signature with an audit trail, not an Aadhaar eSign or certificate-based digital signature. "
            "Whether it is enough for a particular document depends on the law that applies to it.",
            "small",
        ),
    ]

    def footer(c: canvas.Canvas, d):
        c.saveState()
        c.setFont("Helvetica", 7)
        c.setFillColor(MUTED)
        c.drawString(20 * mm, 10 * mm, f"ContractIQ signature certificate · Record {env['id']}")
        c.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Certificate page {d.page}")
        c.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


def _text_pages(text: str, filename: str) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title=filename)
    style = ParagraphStyle("pre", fontName="Courier", fontSize=8.5, leading=11, textColor=INK)
    # Preformatted keeps line breaks; wrap long lines so nothing runs off the page.
    lines = []
    for line in text.replace("\r\n", "\n").split("\n"):
        while len(line) > 95:
            lines.append(line[:95])
            line = line[95:]
        lines.append(line)
    doc.build([Preformatted("\n".join(lines), style)])
    return buf.getvalue()


def _stamp(page_width: float, page_height: float, text: str) -> PdfReader:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))
    c.setFont("Helvetica", 6.5)
    c.setFillColor(MUTED)
    c.drawCentredString(page_width / 2, 5 * mm, text)
    c.save()
    buf.seek(0)
    return PdfReader(buf)


def build_signed_pdf(env: dict, original: bytes) -> bytes:
    """Original pages (stamped) + certificate + original attached."""
    filename = env["document_filename"]
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    writer = PdfWriter()
    note = None
    stamp_text = f"Signed electronically with ContractIQ · Record {env['id']} · see the certificate at the end"

    source: Optional[PdfReader] = None
    if ext == "pdf":
        try:
            source = PdfReader(io.BytesIO(original))
            if source.is_encrypted and not source.decrypt(""):
                source = None
        except Exception:
            source = None
        if source is None:
            note = "The original PDF is protected or couldn't be read, so its pages aren't reproduced here. It is attached unchanged."
    elif ext == "txt":
        try:
            source = PdfReader(io.BytesIO(_text_pages(original.decode("utf-8", errors="replace"), filename)))
            note = "The original text file is typeset on the preceding pages and attached unchanged."
        except Exception:
            source = None
    else:
        note = f"The original {ext.upper() or 'file'} can't be shown as PDF pages here. It is attached to this PDF unchanged."

    if source is not None:
        for original_page in source.pages:
            # pypdf 7 only allows editing pages that belong to a writer.
            page = writer.add_page(original_page)
            try:
                page.transfer_rotation_to_content()
                box = page.mediabox
                stamp = _stamp(float(box.width), float(box.height), stamp_text).pages[0]
                page.merge_translated_page(stamp, float(box.left), float(box.bottom))
            except Exception:
                pass  # an odd page still goes in, just without the footer

    for page in PdfReader(io.BytesIO(certificate_pdf(env, note))).pages:
        writer.add_page(page)

    writer.add_attachment(filename, original)
    writer.add_metadata({
        "/Title": f"{filename} (signed)",
        "/Author": "ContractIQ",
        "/Subject": f"Signature record {env['id']} · original SHA-256 {env['document_sha256']}",
    })
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def signed_filename(document_filename: str) -> str:
    base = document_filename.rsplit(".", 1)[0] if "." in document_filename else document_filename
    return f"{base} (signed).pdf"
