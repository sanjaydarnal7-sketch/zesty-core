"""
Zesty OS
Prompt Builder
Version: 1.0

Mission 24

Builds a unified prompt for every AI provider.
"""


class PromptBuilder:

    def __init__(self):
        pass

    def build(
        self,
        system_prompt: str,
        conversation_history: list,
        user_prompt: str,
        local_context: str = "",
        web_context: str = "",
    ):

        final_system = system_prompt

        if local_context:
            final_system += f"\n\n[LOCAL CONTEXT]\n{local_context}"

        if web_context:
            final_system += f"\n\n[WEB CONTEXT]\n{web_context}"

        messages = [
            {
                "role": "system",
                "content": final_system
            }
        ]

        messages.extend(conversation_history)

        messages.append(
            {
                "role": "user",
                "content": user_prompt
            }
        )

        return messages


if __name__ == "__main__":

    builder = PromptBuilder()

    prompt = builder.build(

        system_prompt="You are Zesty.",

        conversation_history=[
            {
                "role": "assistant",
                "content": "Hello"
            }
        ],

        user_prompt="How are you?"

    )

    print(prompt)