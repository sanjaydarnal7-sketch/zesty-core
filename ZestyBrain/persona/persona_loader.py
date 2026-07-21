"""
Persona loader.
"""

from .identity import IDENTITY
from .user_profile import USER_PROFILE

class PersonaLoader:

    def system_prompt(self) -> str:

        prompt = f"""
You are {IDENTITY['name']}.

Identity Rules:

"""

        for rule in IDENTITY["identity_rules"]:
            prompt += f"- {rule}\n"

        prompt += "\nKnown User\n"

        for k, v in USER_PROFILE.items():
            prompt += f"{k}: {v}\n"

        return prompt
