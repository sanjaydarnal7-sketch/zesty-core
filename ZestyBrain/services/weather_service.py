import requests


class WeatherService:
    """
    Fetches live weather information for Zesty OS.
    """

    DEFAULT_WEATHER = "Clear Sky +29°C"
    DEFAULT_TIMEOUT = 2.0


    def is_available(self) -> bool:
        return True

    def __init__(self, location: str = "Goa"):
        self.location = location


    def set_location(self, location: str) -> None:
        if location and location.strip():
            self.location = location.strip()

    def get_weather(self) -> str:
        try:
            response = requests.get(
                f"https://wttr.in/{self.location}?format=%C+%t",
                timeout=self.DEFAULT_TIMEOUT,
            )

            if response.status_code == 200:
                text = response.text.strip()
                if text:
                    return text

        except Exception as exc:
            print(f"[WEATHER ERROR] {exc}")

        return self.DEFAULT_WEATHER
