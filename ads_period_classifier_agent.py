from enum import Enum
import os
from typing import List
from pydantic import Field
import instructor
from openai import OpenAI
from atomic_agents import AtomicAgent, AgentConfig, BasicChatInputSchema, BaseIOSchema
from atomic_agents.context import ChatHistory, SystemPromptGenerator

client = instructor.from_openai(
    OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="ollama"),
    mode=instructor.Mode.JSON_SCHEMA,
)

system_prompt = SystemPromptGenerator(
    background=[
        "You are a specialized advertising period classifier assistant.",
        "Your task is to analyze transcriptions of audio/video ads and determine which fiscal quarter they should run based on seasonal keywords.",
    ],
    steps=[
        "Read and analyze the ad name provided as context.",
        "Extract any seasonal hints from the ad name (e.g., 'christmas', 'summer', 'winter').",
        "Read and analyze the ad transcription provided by the user.",
        "Identify any seasonal keywords: 'spring', 'summer', 'fall', 'winter' (case-insensitive).",
        "Map identified keywords to fiscal quarters: spring→Q1, summer→Q2, fall→Q3, winter→Q4.",
        "If multiple seasons are mentioned, prioritize the most prominent or first-mentioned season.",
        "Guideline for months:",
        "January, February → Q4",
        "March, April → Q1",
        "May, June, July → Q2",
        "August, September → Q3",
        "October, November, December → Q4",
        "If no seasonal keyword is found, default to ALL_YEAR.",
        "Formulate the classification result as a quarter enum value (Q1, Q2, Q3, Q4, ALL_YEAR).",
    ],
    output_instructions=[
        "Return ONLY the period enum value (Q1/Q2/Q3/Q4/ALL_YEAR) in the structured output schema.",
        "Handle edge cases: 'back to school' → Q3, 'holiday season' → Q4, 'new year' → Q1.",
    ],
)


class AdsPeriod(str, Enum):
    """Fiscal quarter periods for ad scheduling."""

    Q1 = "Q1"  # January-March (Spring)
    Q2 = "Q2"  # April-June (Summer)
    Q3 = "Q3"  # July-September (Fall/Autumn)
    Q4 = "Q4"  # October-December (Winter/Holiday)
    ALL_YEAR = "ALL_YEAR"  # All year


class AdsPeriodClassifierInputSchema(BaseIOSchema):
    """Input schema for the ads period classifier agent."""

    ad_name: str = Field(
        ...,
        description="The original filename of the advertisement (without extension), e.g. ad_001 or coca_cola_christmas",
    )
    transcription: str = Field(
        ..., description="The transcription text of the advertisement to classify"
    )


class AdsPeriodClassifierOutputSchema(BaseIOSchema):
    """Output schema for the ads period classifier agent."""

    period: AdsPeriod = Field(
        ...,
        description="The fiscal quarter period when the ad should run, determined by seasonal keywords in the transcription",
        examples=["Q1", "Q2", "Q3", "Q4"],
    )


class AdsPeriodClassifierAgent(
    AtomicAgent[AdsPeriodClassifierInputSchema, AdsPeriodClassifierOutputSchema]
):
    """Atomic agent for classifying ads by fiscal quarter period."""

    def __init__(self):
        super().__init__(
            AgentConfig(
                client=client,
                model="qwen/qwen3.5-9b",
                history=ChatHistory(),
                system_prompt_generator=system_prompt,
            )
        )


agent = AdsPeriodClassifierAgent()

if __name__ == "__main__":
    from pathlib import Path

    txt_files = Path("/home/simo/Downloads").glob("**/*.txt")
    for txt_file in txt_files:
        print(f"Processing {txt_file}")
        input_data = AdsPeriodClassifierInputSchema(
            ad_name=txt_file.stem, transcription=txt_file.read_text()
        )
        output_data = agent.run(input_data)

        print(f"Input: {input_data.transcription}")
        print(f"Output: {output_data.period}")
        print("-" * 80)
