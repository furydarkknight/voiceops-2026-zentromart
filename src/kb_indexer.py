"""Knowledge base indexing and chunk extraction for ZentroMart."""
import os
import re
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
from src.config import KB_DIR, DATA_DIR, DOC_TYPE_PRECEDENCE

@dataclass
class KBChunk:
    section_id: str
    doc_id: str
    doc_type: str
    title: str
    content: str
    status: str
    effective_from: str
    precedence: int
    file_name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "title": self.title,
            "content": self.content,
            "status": self.status,
            "effective_from": self.effective_from,
            "precedence": self.precedence,
            "file_name": self.file_name,
        }

class KBIndexer:
    def __init__(self, kb_dir: Optional[Path] = None, data_dir: Optional[Path] = None):
        self.kb_dir = Path(kb_dir or KB_DIR)
        self.data_dir = Path(data_dir or DATA_DIR)
        self.chunks: List[KBChunk] = []
        self.chunks_by_id: Dict[str, KBChunk] = {}
        self.products: Dict[str, Dict[str, str]] = {}
        self._load_products()
        self._load_kb()

    def _load_products(self):
        products_file = self.data_dir / "products.csv"
        if products_file.exists():
            with open(products_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.products[row["sku"]] = row

    def _parse_frontmatter(self, text: str) -> Dict[str, str]:
        meta = {}
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if fm_match:
            for line in fm_match.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
        return meta

    def _load_kb(self):
        for file_path in sorted(self.kb_dir.glob("*.md")):
            text = file_path.read_text(encoding="utf-8")
            meta = self._parse_frontmatter(text)
            doc_id = meta.get("doc_id", file_path.stem)
            doc_type = meta.get("doc_type", "general")
            status = meta.get("status", "current")
            effective_from = meta.get("effective_from", "")

            base_prec = DOC_TYPE_PRECEDENCE.get(doc_type, 10)
            if status != "current":
                base_prec -= 30  # Superseded policies have significantly lower precedence

            # Split by section headers: ## [SECTION_ID] Section Title
            pattern = re.compile(r"^##\s*\[([^\]]+)\]\s*(.*)$", re.MULTILINE)
            matches = list(pattern.finditer(text))
            
            for i, match in enumerate(matches):
                sec_id = match.group(1).strip()
                sec_title = match.group(2).strip()
                start_pos = match.end()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                sec_content = text[start_pos:end_pos].strip()

                chunk = KBChunk(
                    section_id=sec_id,
                    doc_id=doc_id,
                    doc_type=doc_type,
                    title=sec_title,
                    content=sec_content,
                    status=status,
                    effective_from=effective_from,
                    precedence=base_prec,
                    file_name=file_path.name,
                )
                self.chunks.append(chunk)
                self.chunks_by_id[sec_id] = chunk

    def get_chunk(self, section_id: str) -> Optional[KBChunk]:
        return self.chunks_by_id.get(section_id)

    def get_product(self, sku: str) -> Optional[Dict[str, str]]:
        return self.products.get(sku)
