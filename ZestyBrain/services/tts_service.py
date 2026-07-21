import asyncio
import os
import subprocess

from edge_tts import Communicate


class TTSService:
    """
    Edge-TTS speech engine for Zesty OS.
    """

    OUTPUT_AUDIO = "zesty_reply.mp3"

    VOICES = {
        "english": "en-IN-NeerjaNeural",
        "hinglish": "hi-IN-SwaraNeural",
    }

    def cleanup(self) -> None:
        try:
            subprocess.run(
                ["pkill", "afplay"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if os.path.exists(self.OUTPUT_AUDIO):
                os.remove(self.OUTPUT_AUDIO)

        except Exception:
            pass

    async def _generate(
        self,
        text: str,
        voice: str,
    ) -> None:
        communicate = Communicate(
            text,
            voice,
            rate="+8%",
            pitch="+10Hz",
        )
        await communicate.save(self.OUTPUT_AUDIO)

    def speak(
        self,
        text: str,
        language: str = "hinglish",
    ) -> None:

        self.cleanup()

        voice = self.VOICES.get(
            language,
            self.VOICES["hinglish"],
        )

        loop = asyncio.new_event_loop()

        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self._generate(text, voice)
            )
        finally:
            loop.close()

        subprocess.Popen(
            ["afplay", self.OUTPUT_AUDIO],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
