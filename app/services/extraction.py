from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    return cleaned or None


class _HtmlTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            cleaned = _clean_text(data)
            if cleaned:
                self.parts.append(cleaned)


class _JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_json_ld = False
        self._buffer: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "script":
            return
        attrs_dict = {name.lower(): value for name, value in attrs}
        if attrs_dict.get("type", "").lower() == "application/ld+json":
            self._in_json_ld = True
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_json_ld:
            self.scripts.append("".join(self._buffer))
            self._in_json_ld = False
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._buffer.append(data)


@dataclass
class ExtractedJob:
    title: str | None = None
    company: str | None = None
    location: str | None = None
    apply_url: str | None = None
    description: str | None = None
    source_platform: str | None = None
    raw_html: str | None = None
    selected_text: str | None = None
    raw_extraction_metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    confidence: str = "low"


def html_to_text(html: str | None) -> str | None:
    if not html:
        return None
    parser = _HtmlTextParser()
    parser.feed(html)
    return _clean_text(" ".join(parser.parts))


def _iter_jsonld_objects(value: Any) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    if isinstance(value, dict):
        objects.append(value)
        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                objects.extend(_iter_jsonld_objects(item))
    elif isinstance(value, list):
        for item in value:
            objects.extend(_iter_jsonld_objects(item))
    return objects


def _is_job_posting(item: dict[str, Any]) -> bool:
    item_type = item.get("@type")
    if isinstance(item_type, list):
        return "JobPosting" in item_type
    return item_type == "JobPosting"


def extract_jsonld_job_posting(raw_html: str | None, warnings: list[str]) -> dict[str, Any] | None:
    if not raw_html:
        return None
    parser = _JsonLdParser()
    parser.feed(raw_html)
    for script in parser.scripts:
        try:
            parsed = json.loads(script)
        except json.JSONDecodeError:
            warnings.append("Ignored invalid JSON-LD block.")
            continue
        for item in _iter_jsonld_objects(parsed):
            if _is_job_posting(item):
                return item
    return None


def _company_from_jsonld(job_posting: dict[str, Any] | None) -> str | None:
    if not job_posting:
        return None
    hiring_org = job_posting.get("hiringOrganization")
    if isinstance(hiring_org, dict):
        return _clean_text(hiring_org.get("name"))
    return _clean_text(hiring_org)


def _location_from_jsonld(job_posting: dict[str, Any] | None) -> str | None:
    if not job_posting:
        return None
    location = job_posting.get("jobLocation")
    if isinstance(location, list):
        location = location[0] if location else None
    if isinstance(location, dict):
        address = location.get("address")
        if isinstance(address, dict):
            parts = [
                address.get("streetAddress"),
                address.get("addressLocality"),
                address.get("addressRegion"),
                address.get("postalCode"),
                address.get("addressCountry"),
            ]
            return _clean_text(", ".join(str(part) for part in parts if part))
        return _clean_text(address)
    return _clean_text(location)


def _apply_url_from_jsonld(job_posting: dict[str, Any] | None, source_url: str | None) -> str | None:
    if not job_posting:
        return None
    for key in ("applicationContact", "url", "sameAs"):
        value = job_posting.get(key)
        if isinstance(value, dict):
            value = value.get("url")
        if isinstance(value, list):
            value = value[0] if value else None
        cleaned = _clean_text(value)
        if cleaned:
            return urljoin(source_url or "", cleaned)
    return None


def extract_job_capture(
    *,
    source_url: str | None = None,
    apply_url: str | None = None,
    title: str | None = None,
    company: str | None = None,
    location: str | None = None,
    description: str | None = None,
    selected_text: str | None = None,
    source_platform: str | None = None,
    raw_extraction_metadata: dict[str, Any] | None = None,
    raw_html: str | None = None,
) -> ExtractedJob:
    warnings: list[str] = []
    job_posting = extract_jsonld_job_posting(raw_html, warnings)
    html_text = html_to_text(raw_html)
    jsonld_description = (
        html_to_text(str(job_posting.get("description")))
        if job_posting and job_posting.get("description")
        else None
    )

    extracted = ExtractedJob(
        title=_clean_text(title) or _clean_text(job_posting.get("title") if job_posting else None),
        company=_clean_text(company) or _company_from_jsonld(job_posting),
        location=_clean_text(location) or _location_from_jsonld(job_posting),
        apply_url=_clean_text(apply_url) or _apply_url_from_jsonld(job_posting, source_url),
        description=_clean_text(description) or jsonld_description or _clean_text(selected_text) or html_text,
        source_platform=_clean_text(source_platform),
        raw_html=raw_html,
        selected_text=selected_text,
        raw_extraction_metadata=raw_extraction_metadata or {},
        warnings=warnings,
        confidence="medium" if job_posting else "low",
    )

    if not extracted.title:
        warnings.append("No title extracted.")
    if not extracted.description:
        warnings.append("No description extracted.")
    return extracted
