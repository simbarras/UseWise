import base64
import io
import logging
import re

import httpx
import pypdf

logger = logging.getLogger(__name__)


def is_url(text: str) -> bool:
    return bool(re.match(r"^https?://\S+$", text.strip()))


def is_base64_pdf(text: str) -> bool:
    return text.startswith("data:application/pdf;base64,")


def extract_pdf_text(data: bytes) -> str:
    logger.debug("Extracting text from PDF content of size %d bytes", len(data))
    reader = pypdf.PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def decode_base64_pdf(text: str) -> str:
    b64data = text.split(",", 1)[1]
    logger.debug("Decoding base64 PDF content of size %d bytes", len(b64data))
    return extract_pdf_text(base64.b64decode(b64data))


def strip_html(html: str) -> str:
    html = re.sub(
        r"<(script|style)[^>]*>.*?</(script|style)>",
        "",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s{2,}", "\n", html).strip()


def fetch_url_content(url: str) -> str:
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        response = client.get(url)
        response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    final_url = str(response.url).lower()
    is_pdf = (
        "pdf" in content_type
        or url.lower().endswith(".pdf")
        or final_url.endswith(".pdf")
        or response.content[:4] == b"%PDF"
    )
    content = extract_pdf_text(response.content) if is_pdf else strip_html(response.text)
    logger.debug("Fetched %d chars from %s (pdf=%s)", len(content), url, is_pdf)
    logger.debug("Content preview: %s", content[:200].replace("\n", " "))
    return content


def resolve_content(raw: str) -> str:
    if is_url(raw):
        return fetch_url_content(raw)
    if is_base64_pdf(raw):
        return decode_base64_pdf(raw)
    return raw
