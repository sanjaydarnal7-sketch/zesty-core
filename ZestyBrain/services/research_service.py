import re
import requests


class ResearchService:
    """
    Handles external web research for Zesty OS.
    """

    SEARCH_URL = "https://lite.duckduckgo.com/lite/"
    MAX_RESULTS = 4

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        )
    }


    def is_available(self) -> bool:
        return True

    def search(self, query: str) -> str:
        print(f"\n[🚀 DEEP SEARCH]: {query}")

        try:
            response = requests.post(
                self.SEARCH_URL,
                data={"q": query},
                headers=self.HEADERS,
                timeout=5.0,
            )

            if response.status_code != 200:
                return ""

            snippets = re.findall(
                r'<td class="result-snippet">(.*?)</td>',
                response.text,
                re.DOTALL,
            )

            cleaned = []

            for snippet in snippets[: self.MAX_RESULTS]:
                value = re.sub(r"<[^>]+>", "", snippet).strip()

                if value:
                    cleaned.append(value)

            if not cleaned:
                return ""

            return "\n".join(f"• {item}" for item in cleaned)

        except Exception as exc:
            print(f"[SEARCH ERROR] {exc}")
            return ""
