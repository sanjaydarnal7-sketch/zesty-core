"""
Deep Probe Engine — structured person/social profile research for Zesty OS Social Panel.
Builds on ResearchService DuckDuckGo extraction; does not replace Host Research text flow.
"""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import urlparse

import requests


_SOCIAL_PLATFORMS = {
    "instagram.com": "instagram",
    "www.instagram.com": "instagram",
    "linkedin.com": "linkedin",
    "www.linkedin.com": "linkedin",
    "in.linkedin.com": "linkedin",
    "twitter.com": "x",
    "www.twitter.com": "x",
    "x.com": "x",
    "www.x.com": "x",
    "facebook.com": "facebook",
    "www.facebook.com": "facebook",
}

# Base platform priority for profile *image* selection (higher = preferred).
_PLATFORM_IMAGE_BASE_SCORE: dict[str, int] = {
    "linkedin": 100,
    "x": 85,
    "website": 70,
    "wikipedia": 65,
    "wikidata": 60,
    "web": 55,
    "facebook": 40,
    "instagram": 25,
}

_REPUTABLE_DOMAINS = (
    "linkedin.com",
    "licdn.com",
    "twitter.com",
    "x.com",
    "twimg.com",
    "wikipedia.org",
    "wikimedia.org",
    "wikidata.org",
)

_LOW_QUALITY_IMAGE_RE = re.compile(
    r"(logo|banner|cover-photo|cover_photo|coverphoto|site-logo|favicon|"
    r"sprite|placeholder|default-avatar|generic|og-default|share-image|"
    r"opengraph|/icons/|/assets/logo)",
    re.IGNORECASE,
)

_HIGH_QUALITY_IMAGE_RE = re.compile(
    r"(profile|avatar|headshot|portrait|/photo/|/photos/|face|"
    r"media\.licdn\.com|pbs\.twimg\.com/profile_images|"
    r"upload\.wikimedia\.org/wikipedia/commons)",
    re.IGNORECASE,
)

_PROBE_TRIGGERS = (
    "deep probe",
    "social probe",
    "instagram",
    "linkedin",
    "twitter",
    " profile",
    "who is",
    "search for",
    "search the internet",
    "find on instagram",
    "find on linkedin",
    "social media",
    "social radar",
)


def _name_tokens(subject_name: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", (subject_name or "").lower())
    return [t for t in tokens if len(t) >= 2]


def _classify_image_platform(page_url: str, image_url: str) -> str:
    for url in (image_url, page_url):
        host = urlparse(url).netloc.lower()
        if "wikipedia.org" in host or "wikimedia.org" in host:
            return "wikipedia"
        if "wikidata.org" in host:
            return "wikidata"
        if "licdn.com" in host or "linkedin.com" in host:
            return "linkedin"
        if "twimg.com" in host or "twitter.com" in host or host.endswith("x.com"):
            return "x"
        if "instagram.com" in host or "cdninstagram.com" in host:
            return "instagram"
        if "facebook.com" in host or "fbcdn.net" in host:
            return "facebook"

    page_platform = DeepProbeEngine._detect_platform(page_url)
    if page_platform == "web":
        host = urlparse(page_url).netloc.lower()
        if host and not any(
            social in host
            for social in ("instagram", "linkedin", "twitter", "facebook", "x.com")
        ):
            return "website"
    return page_platform


def _score_image_candidate(candidate: dict[str, Any], name_tokens: list[str]) -> float:
    platform = candidate.get("platform") or "web"
    score = float(_PLATFORM_IMAGE_BASE_SCORE.get(platform, 40))

    image_url = (candidate.get("url") or "").lower()
    source_url = (candidate.get("source_url") or "").lower()
    context = f"{candidate.get('context_text', '')} {candidate.get('alt_text', '')}".lower()
    combined = f"{image_url} {context} {source_url}"

    for domain in _REPUTABLE_DOMAINS:
        if domain in image_url:
            score += 8
            break

    if _HIGH_QUALITY_IMAGE_RE.search(image_url):
        score += 15
    if _LOW_QUALITY_IMAGE_RE.search(image_url):
        score -= 35

    # Website banners / hero images are not profile photos.
    if platform in ("website", "web") and re.search(
        r"(/fill/w_|/fill/h_|hero|header|banner|cover|wixstatic\.com/media/.+~mv2\.(png|jpg)/v1/fill)",
        image_url,
        re.IGNORECASE,
    ):
        score -= 45

    # Facebook CDN profile-picture path pattern (common when LinkedIn is blocked).
    if "fbcdn.net" in image_url and re.search(r"/t39\.\d+-1/", image_url):
        score += 30
        if any(token in source_url for token in name_tokens):
            score += 20

    if platform == "instagram":
        score -= 20
        if not name_tokens or not any(token in combined for token in name_tokens):
            score -= 25
        if not re.search(r"cdninstagram\.com/v/t\d+\.\d+-19/", image_url):
            score -= 15

    matched = sum(1 for token in name_tokens if token in combined)
    if name_tokens:
        score += matched * 12
        if matched >= min(2, len(name_tokens)):
            score += 10

    source_matches = sum(1 for token in name_tokens if token in source_url)
    score += source_matches * 10

    width_hint = candidate.get("width_hint")
    if isinstance(width_hint, int):
        if width_hint >= 200:
            score += 5
        if width_hint < 80:
            score -= 15

    return score


def _confidence_from_score(score: float, platform: str) -> str:
    if platform == "instagram" and score < 90:
        return "low"
    if score >= 130:
        return "high"
    if score >= 85:
        return "medium"
    return "low"


def select_best_profile_image(
    candidates: list[dict[str, Any]],
    subject_name: str = "",
) -> dict[str, Any]:
    """
    Pick the best profile image from multiple source candidates.

    Each candidate should include:
      - url: image URL
      - platform: linkedin | x | website | wikipedia | instagram | ...
      - source_url: page the image was discovered on
      - context_text / alt_text: optional surrounding text for name matching
    """
    if not candidates:
        return {
            "url": None,
            "source": None,
            "source_url": None,
            "confidence": "low",
            "score": 0,
        }

    name_tokens = _name_tokens(subject_name)
    seen_urls: set[str] = set()
    ranked: list[tuple[float, dict[str, Any]]] = []

    for candidate in candidates:
        url = (candidate.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        if _LOW_QUALITY_IMAGE_RE.search(url) and not _HIGH_QUALITY_IMAGE_RE.search(url):
            continue
        score = _score_image_candidate(candidate, name_tokens)
        ranked.append((score, candidate))

    if not ranked:
        return {
            "url": None,
            "source": None,
            "source_url": None,
            "confidence": "low",
            "score": 0,
        }

    ranked.sort(key=lambda item: item[0], reverse=True)
    best_score, best = ranked[0]
    platform = best.get("platform") or "web"

    return {
        "url": best.get("url"),
        "source": platform,
        "source_url": best.get("source_url"),
        "confidence": _confidence_from_score(best_score, platform),
        "score": round(best_score, 2),
    }


class DeepProbeEngine:
    """Structured social/person research for Social Panel integration."""

    def __init__(self, research_service):
        self.research_service = research_service

    @staticmethod
    def should_probe(text: str) -> bool:
        lowered = (text or "").lower()
        if not lowered.strip():
            return False
        if any(t in lowered for t in _PROBE_TRIGGERS):
            return True
        if any(t in lowered for t in ("search", "find", "research", "lookup")) and any(
            p in lowered for p in ("instagram", "linkedin", "twitter", "profile", "social")
        ):
            return True
        return DeepProbeEngine.should_probe_person(text)

    @staticmethod
    def should_probe_person(text: str) -> bool:
        """Broader person-search detection for continuity (e.g. 'search John Smith')."""
        lowered = (text or "").lower()
        if not lowered.strip():
            return False
        if any(
            w in lowered
            for w in (
                "weather", "forecast", "temperature", "news", "recipe",
                "stock", "price", "gold", "bitcoin", "match score", "cricket score",
            )
        ):
            return False
        if not re.search(r"\b(search|find|research|who is|lookup)\b", lowered):
            return False
        noise = {
            "search", "find", "research", "lookup", "about", "the", "for", "and",
            "with", "who", "is", "tell", "me", "give", "info", "detail", "please",
        }
        tokens = [t for t in re.findall(r"[a-z]{2,}", lowered) if t not in noise]
        return len(tokens) >= 2

    @staticmethod
    def looks_like_person_query(text: str) -> bool:
        """Heuristic for person/profile searches that should run a social probe."""
        lowered = (text or "").lower()
        if not lowered.strip():
            return False
        if any(w in lowered for w in ("weather", "news", "recipe", "price", "stock", "temperature", "forecast")):
            return False
        if any(w in lowered for w in ("who is", "profile", "linkedin", "instagram", "deep probe", "social probe")):
            return True
        if re.search(r"\b(search|find|research)\s+\w+", lowered):
            words = re.findall(r"[a-z]{2,}", lowered)
            skip = {
                "search", "find", "research", "about", "the", "for", "and", "with",
                "from", "into", "what", "when", "where", "how",
            }
            return len([w for w in words if w not in skip]) >= 2
        return False

    @staticmethod
    def _clean_query(text: str) -> str:
        q = re.sub(
            r"(?i)\b(search the internet for|search for|deep probe|social probe|"
            r"find on instagram|find on linkedin|tell me everything you can find about|"
            r"instagram|linkedin|twitter|profile of|about me|about)\b",
            " ",
            text or "",
        )
        q = re.sub(r"\s+", " ", q).strip(" .,!?")
        return q or text.strip()

    @staticmethod
    def _detect_platform(url: str) -> str:
        host = urlparse(url).netloc.lower()
        for domain, platform in _SOCIAL_PLATFORMS.items():
            if host == domain or host.endswith("." + domain):
                return platform
        if "wikipedia.org" in host:
            return "wikipedia"
        if "wikidata.org" in host:
            return "wikidata"
        return "web"

    @staticmethod
    def _extract_username(url: str, platform: str) -> str:
        path = urlparse(url).path.strip("/")
        if not path:
            return ""
        parts = [p for p in path.split("/") if p]
        if platform == "instagram" and parts:
            return parts[0].lstrip("@")
        if platform == "linkedin":
            if parts and parts[0] in ("in", "pub", "company"):
                return parts[1] if len(parts) > 1 else parts[0]
            return parts[-1] if parts else ""
        if platform == "x":
            return parts[0].lstrip("@") if parts else ""
        return parts[-1] if parts else ""

    @staticmethod
    def _parse_counts(text: str) -> dict[str, str]:
        counts: dict[str, str] = {}
        for label, pattern in (
            ("followers", r"([\d,.]+[KMB]?)\s*followers"),
            ("following", r"([\d,.]+[KMB]?)\s*following"),
            ("connections", r"([\d,.]+[KMB]?\+?)\s*connections"),
        ):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                counts[label] = match.group(1)
        return counts

    @staticmethod
    def _parse_image_dimensions(image_url: str) -> int | None:
        match = re.search(r"[=_-](\d{2,4})x(\d{2,4})", image_url)
        if match:
            return min(int(match.group(1)), int(match.group(2)))
        match = re.search(r"width=(\d+)", image_url, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _fetch_page_image_candidates(
        self,
        page_url: str,
        result_item: dict[str, str],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        context_text = f"{result_item.get('title', '')} {result_item.get('snippet', '')}".strip()

        try:
            res = requests.get(
                page_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ZestyDeepProbe/1.0)"},
                timeout=8,
            )
            if res.status_code != 200:
                return candidates

            page_html = res.text
            image_urls: list[str] = []
            for pattern in (
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+property=["\']og:image:secure_url["\'][^>]+content=["\']([^"\']+)',
            ):
                for match in re.finditer(pattern, page_html, re.IGNORECASE):
                    image_urls.append(html.unescape(match.group(1).strip()))

            for match in re.finditer(
                r'<img[^>]+alt=["\']([^"\']*)["\'][^>]+src=["\']([^"\']+)',
                page_html,
                re.IGNORECASE,
            ):
                alt_text, src = match.group(1), html.unescape(match.group(2).strip())
                if src.startswith("http"):
                    platform = _classify_image_platform(page_url, src)
                    candidates.append(
                        {
                            "url": src,
                            "source_url": page_url,
                            "platform": platform,
                            "context_text": context_text,
                            "alt_text": alt_text,
                            "width_hint": self._parse_image_dimensions(src),
                        }
                    )

            for image_url in image_urls:
                platform = _classify_image_platform(page_url, image_url)
                candidates.append(
                    {
                        "url": image_url,
                        "source_url": page_url,
                        "platform": platform,
                        "context_text": context_text,
                        "alt_text": "",
                        "width_hint": self._parse_image_dimensions(image_url),
                    }
                )
        except Exception:
            return candidates

        return candidates

    def _gather_image_candidates(
        self,
        merged: list[dict[str, str]],
        subject_name: str,
    ) -> list[dict[str, Any]]:
        """Collect image candidates from all platforms before scoring."""
        by_platform: dict[str, list[dict[str, str]]] = {}
        for item in merged:
            url = item.get("url", "")
            platform = self._detect_platform(url)
            by_platform.setdefault(platform, []).append(item)

        if subject_name:
            for item in self._fetch_structured(f"{subject_name} wikipedia")[:2]:
                url = item.get("url", "")
                if "wikipedia.org" in url and url not in {
                    i.get("url") for i in merged
                }:
                    merged.append(item)
                    by_platform.setdefault("wikipedia", []).append(item)

        fetch_priority = ("linkedin", "x", "web", "wikipedia", "facebook", "instagram")
        candidates: list[dict[str, Any]] = []
        seen_pages: set[str] = set()
        seen_image_urls: set[str] = set()

        for platform in fetch_priority:
            for item in by_platform.get(platform, []):
                page_url = item.get("url", "")
                if not page_url or page_url in seen_pages:
                    continue
                seen_pages.add(page_url)
                for candidate in self._fetch_page_image_candidates(page_url, item):
                    img_url = candidate.get("url", "")
                    if img_url and img_url not in seen_image_urls:
                        seen_image_urls.add(img_url)
                        candidates.append(candidate)

        return candidates

    def _fetch_structured(self, query: str) -> list[dict[str, str]]:
        try:
            url = "https://duckduckgo.com/html/"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, params={"q": query}, headers=headers, timeout=10)
            if res.status_code != 200:
                return []
            return self.research_service._extract_duckduckgo_results(res.text)
        except Exception:
            return []

    def _rank_profile_url(self, results: list[dict[str, str]]) -> dict[str, str] | None:
        priority = ("linkedin", "x", "web", "wikipedia", "facebook", "instagram")
        scored: list[tuple[int, dict[str, str]]] = []
        for item in results:
            platform = self._detect_platform(item.get("url", ""))
            try:
                score = priority.index(platform)
            except ValueError:
                score = len(priority)
            scored.append((score, item))
        scored.sort(key=lambda x: x[0])
        return scored[0][1] if scored else None

    def _build_timeline(self, results: list[dict[str, str]]) -> list[dict[str, str]]:
        timeline: list[dict[str, str]] = []
        for item in results[:4]:
            timeline.append(
                {
                    "title": item.get("title", ""),
                    "detail": item.get("snippet", ""),
                    "url": item.get("url", ""),
                }
            )
        return timeline

    def _format_panel_text(self, profile: dict[str, Any]) -> str:
        lines = [
            f"NAME: {profile.get('name') or 'Unknown'}",
        ]
        if profile.get("username"):
            lines.append(f"USERNAME: @{profile['username']}")
        if profile.get("platform"):
            lines.append(f"PLATFORM: {profile['platform'].upper()}")
        if profile.get("profile_image_source"):
            conf = profile.get("profile_image_confidence", "low")
            lines.append(
                f"PHOTO SOURCE: {profile['profile_image_source'].upper()} ({conf} confidence)"
            )
        if profile.get("bio"):
            lines.append(f"\nBIO / OVERVIEW:\n{profile['bio']}")
        metrics = []
        if profile.get("followers"):
            metrics.append(f"Followers: {profile['followers']}")
        if profile.get("following"):
            metrics.append(f"Following: {profile['following']}")
        if profile.get("connections"):
            metrics.append(f"Connections: {profile['connections']}")
        if metrics:
            lines.append("\nMETRICS: " + " | ".join(metrics))
        if profile.get("recent_activity"):
            lines.append("\nRECENT ACTIVITY:")
            for act in profile["recent_activity"][:4]:
                lines.append(f"• {act}")
        if profile.get("social_links"):
            lines.append("\nSOCIAL LINKS:")
            for link in profile["social_links"][:5]:
                lines.append(f"• {link.get('platform', 'web').upper()}: {link.get('url', '')}")
        if profile.get("key_findings"):
            lines.append("\nKEY FINDINGS:")
            for finding in profile["key_findings"][:6]:
                lines.append(f"• {finding}")
        if profile.get("sources"):
            lines.append("\nSOURCES:")
            for src in profile["sources"][:5]:
                lines.append(f"• {src.get('title', '')} ({src.get('url', '')})")
        if profile.get("timeline"):
            lines.append("\nTIMELINE:")
            for entry in profile["timeline"][:3]:
                lines.append(f"• {entry.get('title', '')}: {entry.get('detail', '')}")
        return "\n".join(lines)

    def probe(self, user_text: str) -> dict[str, Any] | None:
        if not self.should_probe(user_text):
            return None

        subject = self._clean_query(user_text)
        queries = [subject, f"{subject} linkedin", f"{subject} instagram"]
        merged: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        for query in queries:
            for item in self._fetch_structured(query):
                url = item.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    merged.append(item)

        if not merged:
            return None

        primary = self._rank_profile_url(merged) or merged[0]
        primary_url = primary.get("url", "")
        platform = self._detect_platform(primary_url)
        username = self._extract_username(primary_url, platform)

        name = subject.title() if subject else primary.get("title", "Unknown")
        if " - " in primary.get("title", ""):
            name = primary["title"].split(" - ")[0].strip()
        elif " | " in primary.get("title", ""):
            name = primary["title"].split(" | ")[0].strip()

        combined_text = " ".join(
            f"{r.get('title', '')} {r.get('snippet', '')}" for r in merged[:6]
        )
        counts = self._parse_counts(combined_text)

        social_links: list[dict[str, str]] = []
        for item in merged:
            url = item.get("url", "")
            plat = self._detect_platform(url)
            if plat != "web" and url:
                social_links.append(
                    {
                        "platform": plat,
                        "url": url,
                        "username": self._extract_username(url, plat),
                    }
                )

        image_candidates = self._gather_image_candidates(merged, name)
        image_pick = select_best_profile_image(image_candidates, subject_name=name)

        key_findings = []
        for item in merged[:5]:
            snippet = html.unescape(item.get("snippet", "").strip())
            if snippet and len(snippet) > 20:
                key_findings.append(snippet[:220])

        recent_activity = [
            f"{item.get('title', '')}: {item.get('snippet', '')[:120]}"
            for item in merged[:3]
            if item.get("snippet")
        ]

        facts_lines = []
        for item in merged[:5]:
            line = f"- {item.get('title', '')}"
            if item.get("snippet"):
                line += f": {item['snippet']}"
            if item.get("url"):
                line += f" ({item['url']})"
            facts_lines.append(line)

        profile: dict[str, Any] = {
            "name": html.unescape(name),
            "username": username,
            "platform": platform,
            "bio": html.unescape(primary.get("snippet", "")),
            "profile_image_url": image_pick.get("url"),
            "profile_image_source": image_pick.get("source"),
            "profile_image_confidence": image_pick.get("confidence"),
            "profile_image_score": image_pick.get("score"),
            "followers": counts.get("followers"),
            "following": counts.get("following"),
            "connections": counts.get("connections"),
            "engagement_rate": None,
            "follower_delta": None,
            "recent_activity": recent_activity,
            "social_links": social_links[:6],
            "key_findings": key_findings,
            "sources": [
                {"title": i.get("title", ""), "url": i.get("url", "")} for i in merged[:6]
            ],
            "timeline": self._build_timeline(merged),
            "facts_text": "\n".join(facts_lines),
            "panel_text": "",
            "primary_url": primary_url,
        }

        if counts.get("followers"):
            profile["follower_delta"] = f"+{counts['followers']}"
        profile["panel_text"] = self._format_panel_text(profile)
        return profile
