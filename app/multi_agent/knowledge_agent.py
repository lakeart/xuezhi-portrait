# -*- coding: utf-8 -*-
"""
知识库管理智能体
提供文档解析、分块索引、语义检索和带引用的 RAG 问答能力。
"""

import hashlib
import json
import os
import re
import uuid
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple

from app import db
from app.models.agent_models import KnowledgeChunkModel, KnowledgeDocumentModel
from app.multi_agent import HallucinationDetector


class KnowledgeBaseAgent:
    """轻量级知识库 Agent。

    现阶段使用 TF-IDF 向量空间完成可演示的语义检索闭环，后续可平滑替换为
    ChromaDB/Milvus 等向量库。
    """

    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.csv', '.json', '.docx', '.pdf'}

    def index_file(self, user_id: int, file_path: str, original_filename: str, title: str = "") -> Dict:
        text = self.extract_text(file_path, original_filename)
        if len(text.strip()) < 20:
            raise ValueError("文档内容过少，无法建立知识库索引")

        content_hash = self._hash_text(text)
        existing = KnowledgeDocumentModel.query.filter_by(
            user_id=user_id,
            content_hash=content_hash
        ).first()
        if existing:
            return {
                'document': existing.to_dict(),
                'chunks': existing.chunk_count,
                'deduplicated': True
            }

        document_id = str(uuid.uuid4())
        ext = os.path.splitext(original_filename)[1].lower().lstrip('.')
        chunks = self._chunk_text(text)

        document = KnowledgeDocumentModel(
            document_id=document_id,
            user_id=user_id,
            title=title or os.path.splitext(original_filename)[0],
            original_filename=original_filename,
            stored_filename=os.path.basename(file_path),
            file_type=ext,
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            content_hash=content_hash,
            status='indexed',
            chunk_count=len(chunks),
            summary=self._summarize(text)
        )
        db.session.add(document)

        for index, chunk in enumerate(chunks):
            keywords = self._extract_keywords(chunk)
            db.session.add(KnowledgeChunkModel(
                document_id=document_id,
                user_id=user_id,
                chunk_index=index,
                content=chunk,
                keywords=json.dumps(keywords, ensure_ascii=False),
                vector_meta=json.dumps({
                    'method': 'tfidf',
                    'chunk_hash': self._hash_text(chunk),
                    'token_count_estimate': max(1, len(chunk) // 2)
                }, ensure_ascii=False),
                char_count=len(chunk)
            ))

        db.session.commit()
        return {
            'document': document.to_dict(),
            'chunks': len(chunks),
            'deduplicated': False
        }

    def extract_text(self, file_path: str, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("暂不支持该文件类型，请上传 TXT/Markdown/CSV/JSON/DOCX/PDF")

        if ext == '.docx':
            return self._extract_docx_text(file_path)
        if ext == '.pdf':
            return self._extract_pdf_text(file_path)

        with open(file_path, 'rb') as f:
            raw = f.read()
        for encoding in ('utf-8-sig', 'utf-8', 'gbk', 'gb18030'):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw.decode('utf-8', errors='ignore')

    def search(self, user_id: int, query: str, top_k: int = 5) -> Dict:
        query = (query or '').strip()
        if not query:
            return {'results': [], 'count': 0}
        try:
            top_k = max(1, min(10, int(top_k)))
        except Exception:
            top_k = 5

        chunks = KnowledgeChunkModel.query.filter_by(user_id=user_id).all()
        if not chunks:
            return {'results': [], 'count': 0}

        scores = self._rank_chunks(query, chunks)
        document_ids = {chunk.document_id for chunk, _ in scores}
        docs = KnowledgeDocumentModel.query.filter(
            KnowledgeDocumentModel.document_id.in_(document_ids)
        ).all() if document_ids else []
        doc_map = {doc.document_id: doc for doc in docs}

        results = []
        for chunk, score in scores[:top_k]:
            doc = doc_map.get(chunk.document_id)
            results.append({
                'chunk_id': chunk.id,
                'document_id': chunk.document_id,
                'document_title': doc.title if doc else '未知文档',
                'filename': doc.original_filename if doc else '',
                'chunk_index': chunk.chunk_index,
                'score': round(float(score), 4),
                'content': chunk.content,
                'preview': self._highlight_preview(chunk.content, query)
            })

        return {'results': results, 'count': len(results)}

    def answer(self, user_id: int, question: str, top_k: int = 4) -> Dict:
        search_result = self.search(user_id, question, top_k=top_k)
        contexts = search_result.get('results', [])
        if not contexts:
            return {
                'answer': '知识库中暂未检索到足够相关的材料。建议先上传课程讲义、课件或题库文档，再进行基于资料的问答。',
                'citations': [],
                'confidence': 0.0,
                'warnings': ['未命中知识库材料，回答已被拦截以降低幻觉风险。'],
                'retrieval': search_result
            }

        answer_lines = [
            f"基于已上传知识库，我检索到 {len(contexts)} 条相关材料：",
            ""
        ]
        for i, ctx in enumerate(contexts, 1):
            sentence = self._best_sentence(ctx['content'], question)
            answer_lines.append(f"{i}. {sentence} [来源{i}]")

        answer_lines.extend([
            "",
            "建议学习路径：先阅读最高相关来源，提炼概念定义，再用练习题验证掌握度；若多个来源表述不一致，以课程讲义或教师上传材料优先。"
        ])

        combined = "\n".join(answer_lines)
        _, warnings = HallucinationDetector.check_factuality(combined, question)
        max_score = max((ctx['score'] for ctx in contexts), default=0)

        return {
            'answer': combined,
            'citations': [
                {
                    'ref': f"来源{i}",
                    'document_title': ctx['document_title'],
                    'filename': ctx['filename'],
                    'chunk_index': ctx['chunk_index'],
                    'score': ctx['score'],
                    'content': ctx['content'][:360]
                }
                for i, ctx in enumerate(contexts, 1)
            ],
            'confidence': round(min(0.96, max_score + 0.18), 2),
            'warnings': warnings,
            'retrieval': search_result
        }

    def status(self, user_id: int) -> Dict:
        documents = KnowledgeDocumentModel.query.filter_by(user_id=user_id).order_by(
            KnowledgeDocumentModel.created_at.desc()
        ).all()
        chunk_count = KnowledgeChunkModel.query.filter_by(user_id=user_id).count()
        return {
            'documents': [doc.to_dict() for doc in documents],
            'document_count': len(documents),
            'chunk_count': chunk_count,
            'retrieval_engine': 'TF-IDF semantic retrieval',
            'supported_extensions': sorted(self.SUPPORTED_EXTENSIONS)
        }

    def _rank_chunks(self, query: str, chunks: List[KnowledgeChunkModel]) -> List[Tuple[KnowledgeChunkModel, float]]:
        corpus = [chunk.content for chunk in chunks]
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4), max_features=6000)
            matrix = vectorizer.fit_transform(corpus + [query])
            similarities = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
            scored = list(zip(chunks, similarities))
        except Exception:
            query_terms = set(self._tokenize(query))
            scored = []
            for chunk in chunks:
                terms = set(self._tokenize(chunk.content))
                overlap = len(query_terms & terms)
                scored.append((chunk, overlap / max(1, len(query_terms))))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [(chunk, score) for chunk, score in scored if score > 0]

    def _extract_docx_text(self, file_path: str) -> str:
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        with zipfile.ZipFile(file_path) as z:
            xml = z.read('word/document.xml')
        root = ET.fromstring(xml)
        paragraphs = []
        for p in root.findall('.//w:p', ns):
            text = ''.join((t.text or '') for t in p.findall('.//w:t', ns)).strip()
            if text:
                paragraphs.append(text)
        return '\n'.join(paragraphs)

    def _extract_pdf_text(self, file_path: str) -> str:
        try:
            try:
                from pypdf import PdfReader
            except Exception:
                from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            return '\n'.join(page.extract_text() or '' for page in reader.pages)
        except Exception as exc:
            raise ValueError(f"PDF 解析依赖不可用或文件无法解析：{exc}")

    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
        cleaned = re.sub(r'\n{3,}', '\n\n', text).strip()
        if len(cleaned) <= chunk_size:
            return [cleaned]

        chunks = []
        start = 0
        while start < len(cleaned):
            end = min(len(cleaned), start + chunk_size)
            window = cleaned[start:end]
            cut = max(window.rfind('\n'), window.rfind('。'), window.rfind('；'), window.rfind('.'))
            if cut > chunk_size * 0.45:
                end = start + cut + 1
            chunk = cleaned[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(cleaned):
                break
            start = max(0, end - overlap)
        return chunks

    def _summarize(self, text: str) -> str:
        normalized = re.sub(r'\s+', ' ', text).strip()
        return normalized[:220] + ('...' if len(normalized) > 220 else '')

    def _extract_keywords(self, text: str, limit: int = 12) -> List[str]:
        tokens = self._tokenize(text)
        freq = {}
        for token in tokens:
            if len(token) < 2:
                continue
            freq[token] = freq.get(token, 0) + 1
        return [item[0] for item in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit]]

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'[\u4e00-\u9fa5]{2,}|[A-Za-z][A-Za-z0-9_+-]{1,}', text.lower())

    def _highlight_preview(self, text: str, query: str) -> str:
        sentence = self._best_sentence(text, query)
        return sentence[:240] + ('...' if len(sentence) > 240 else '')

    def _best_sentence(self, text: str, query: str) -> str:
        sentences = [s.strip() for s in re.split(r'(?<=[。！？!?；;.\n])', text) if s.strip()]
        if not sentences:
            return text[:260]
        terms = set(self._tokenize(query))
        best = max(sentences, key=lambda s: len(terms & set(self._tokenize(s))))
        return best[:320] + ('...' if len(best) > 320 else '')

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()
