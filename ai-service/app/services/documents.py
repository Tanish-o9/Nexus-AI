from __future__ import annotations

from io import BytesIO
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.memory.models import DocumentChunkModel, DocumentModel
from app.services.embeddings import embed_texts

ALLOWED_MIME_TYPES = {
    'text/plain': '.txt', 'text/markdown': '.md', 'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
}


def extract_text(filename: str, mime_type: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if mime_type not in ALLOWED_MIME_TYPES or ALLOWED_MIME_TYPES[mime_type] != suffix:
        raise ValueError('Only TXT, Markdown, PDF, and DOCX documents are supported.')
    if suffix in {'.txt', '.md'}:
        return content.decode('utf-8', errors='replace')
    if suffix == '.pdf':
        from pypdf import PdfReader
        return '\n'.join(page.extract_text() or '' for page in PdfReader(BytesIO(content)).pages)
    from docx import Document as DocxDocument
    return '\n'.join(paragraph.text for paragraph in DocxDocument(BytesIO(content)).paragraphs)


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    clean = ' '.join(text.split())
    if not clean:
        raise ValueError('The document does not contain extractable text.')
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + size)
        if end < len(clean):
            boundary = clean.rfind(' ', start, end)
            if boundary > start + size // 2:
                end = boundary
        chunks.append(clean[start:end].strip())
        if end == len(clean):
            break
        start = max(end - overlap, start + 1)
    return chunks


async def ingest_document(session: AsyncSession, *, filename: str, mime_type: str, content: bytes, org_id: str, project_id: str | None, user_id: str) -> tuple[DocumentModel, int]:
    settings = get_settings()
    if len(content) > settings.MAX_DOCUMENT_SIZE_BYTES:
        raise ValueError('Document exceeds the 10 MB upload limit.')
    chunks = chunk_text(extract_text(filename, mime_type, content), settings.DOCUMENT_CHUNK_SIZE, settings.DOCUMENT_CHUNK_OVERLAP)
    document = DocumentModel(filename=Path(filename).name, mime_type=mime_type, org_id=org_id, project_id=project_id, uploaded_by=user_id)
    session.add(document)
    await session.flush()
    # Create chunk models (without embeddings first)
    chunk_models: list[DocumentChunkModel] = []
    for index, chunk in enumerate(chunks):
        model = DocumentChunkModel(
            document_id=document.id,
            content=chunk,
            chunk_index=index,
            metadata_={'source': document.filename, 'org_id': org_id, 'project_id': project_id, 'uploaded_by': user_id},
        )
        session.add(model)
        chunk_models.append(model)
    await session.flush()
    # Generate embeddings in one batch — much faster than one-at-a-time
    embeddings = await embed_texts(chunks)
    for model, embedding in zip(chunk_models, embeddings):
        model.embedding = embedding
    return document, len(chunks)
