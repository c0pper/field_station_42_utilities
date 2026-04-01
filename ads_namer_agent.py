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


system_prompt = SystemPromptGenerator(
    background=[
        "You are a specialized advertising naming assistant.",
        "Your task is to generate a short, unique, filesystem-safe name for an advertisement based on its transcription.",
    ],
    steps=[
        "Read and analyze the ad transcription.",
        "Identify the main subject: brand, product, service, or performer.",
        "Identify context: event, promotion, or activity.",
        "Detect seasonality if present: spring, summer, fall, winter, christmas, new year, festival.",
        "Construct a concise name combining key elements.",
        "Use lowercase and underscores only.",
        "Avoid generic names like 'ad_1', 'video', etc.",
        "Prefer specificity: brand + context + season if available.",
        "Limit to 3-6 words maximum.",
        "If text only says 'Music' or 'Grazie a tutti', name it 'bumper'"
    ],
    output_instructions=[
        "Return ONLY the generated name.",
        "Use snake_case.",
        "No spaces, no special characters.",
        "Examples:",
        "coca_cola_christmas",
        "piero_pelu_concert_summer",
        "nike_running_campaign",
        "amazon_black_friday",
        "spotify_music_festival_summer"
    ]
)


class AdsNamingInputSchema(BaseIOSchema):
    """ Input schema for the ads naming agent. """
    transcription: str = Field(
        ...,
        description="The transcription text of the advertisement"
    )


class AdsNamingOutputSchema(BaseIOSchema):
    """ Output schema for the ads naming agent. """
    name: str = Field(
        ...,
        description="Generated unique, filesystem-safe ad name",
        examples=[
            "coca_cola_christmas",
            "piero_pelu_concert_summer"
        ]
    )


class AdsNamingAgent(AtomicAgent[AdsNamingInputSchema, AdsNamingOutputSchema]):
    def __init__(self):
        super().__init__(AgentConfig(
            client=client,
            model="qwen/qwen3.5-9b",
            history=ChatHistory(),
            system_prompt_generator=system_prompt
        ))


agent = AdsNamingAgent()

if __name__ == "__main__":
    from pathlib import Path

    txt_files = Path("/home/simo/Downloads").glob("**/*.txt")

    for txt_file in txt_files:
        print(f"Processing {txt_file}")

        input_data = AdsNamingInputSchema(
            transcription=txt_file.read_text()
        )

        output_data = agent.run(input_data)

        print(f"Generated name: {output_data.name}")
        print("-" * 80)
