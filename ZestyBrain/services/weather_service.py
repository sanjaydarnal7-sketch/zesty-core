import requests


class WeatherService:
    """
    Fetches live weather information for Zesty OS.
    """

    DEFAULT_WEATHER = "Clear Sky +29°C"

    def __init__(self, location: str = "Goa"):
        self.location = location

    def get_weather(self) -> str:
        try:
            response = requests.get(
                f"https://wttr.in/{self.location}?format=%C+%t",
                timeout=2.0,
            )

            if response.status_code == 200:
                text = response.text.strip()
                if text:
                    return text

        except Exception as exc:
            print(f"[WEATHER ERROR] {exc}")

        return self.DEFAULT_WEATHER
