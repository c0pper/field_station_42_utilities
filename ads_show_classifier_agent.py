from enum import Enum
from pydantic import Field
import instructor
from openai import OpenAI
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory, SystemPromptGenerator


client = instructor.from_openai(
    OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="ollama"),
    mode=instructor.Mode.JSON_SCHEMA
)


# -------------------------
# SYSTEM PROMPT
# -------------------------

system_prompt = SystemPromptGenerator(
    background=[
        "You are a specialized advertising classifier assistant.",
        "Your task is to determine whether an advertisement is promoting a TV show, channel content, or programming.",
    ],
    steps=[
        "Read and analyze the ad transcription provided by the user.",
        "Determine if the content is promoting a TV show, episode, program, or channel content.",
        "Look for indicators such as:",
        "- Show titles or program names",
        "- Mentions of schedules (e.g., 'tonight at 21:00', 'every Friday')",
        "- Phrases like 'only on', 'next on', 'coming up',",
        "- Channel branding (e.g., MTV, Rai, Mediaset, etc.)",
        "- Episode previews or narration about a show",
        "",
        "If the ad is about a product, service, or brand, classify it as NOT a show ad.",
        "If the ad promotes TV programming or channel content, classify it as a show ad.",
    ],
    output_instructions=[
        "Return ONLY a boolean value:",
        "- true → if it is a TV show/channel promotion",
        "- false → if it is a regular commercial ad",
        "Be strict: only return true when clearly a show promo."
    ]
)


# -------------------------
# SCHEMAS
# -------------------------

class AdsShowClassifierInputSchema(BaseIOSchema):
    """Input schema for show ad classification."""
    transcription: str = Field(
        ...,
        description="The transcription text of the advertisement"
    )


class AdsShowClassifierOutputSchema(BaseIOSchema):
    """Output schema for show ad classification."""
    is_show_ad: bool = Field(
        ...,
        description="True if the ad promotes a TV show or channel programming, False otherwise",
        examples=[True, False]
    )


# -------------------------
# AGENT
# -------------------------

class AdsShowClassifierAgent(
    AtomicAgent[AdsShowClassifierInputSchema, AdsShowClassifierOutputSchema]
):
    def __init__(self):
        super().__init__(AgentConfig(
            client=client,
            model="qwen/qwen3.5-9b",
            history=ChatHistory(),
            system_prompt_generator=system_prompt
        ))


agent = AdsShowClassifierAgent()


# -------------------------
# TEST
# -------------------------

if __name__ == "__main__":
    from pathlib import Path

    txt_files = Path("/home/simo/Downloads").glob("**/*.txt")

    for txt_file in txt_files:
        print(f"Processing {txt_file}")

        input_data = AdsShowClassifierInputSchema(
            transcription=txt_file.read_text()
        )

        output_data = agent.run(input_data)

        print(f"Result: {output_data.is_show_ad}")
        print("-" * 80)
