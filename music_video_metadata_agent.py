from pydantic import Field
import instructor
from openai import OpenAI
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory, SystemPromptGenerator
from ddgs import DDGS
from config import OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL, MODEL_API_PARAMETERS


client = instructor.from_openai(
    OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
)


system_prompt = SystemPromptGenerator(
    background=[
        "You are a specialized music video metadata assistant.",
        "Your task is to identify a song from its filename and any web search results, then output the canonical title, artist, album, and release year.",
    ],
    steps=[
        "Read the video filename provided by the user.",
        "Read the web search results provided by the user.",
        "Identify the most likely song match based on the filename and search results.",
        "Determine the official title (correct capitalization and formatting).",
        "Determine the primary artist or band.",
        "Determine the album the song appears on (if unknown, leave empty).",
        "Determine the release year (4-digit year, if unknown, leave empty).",
        "Use the web search results as your primary source of truth.",
    ],
    output_instructions=[
        "Return ONLY the structured metadata.",
        "Use correct capitalization for title and artist.",
        "Year must be a 4-digit string or empty string.",
        "Album can be empty string if not found.",
    ],
)


class MusicVideoMetadataInputSchema(BaseIOSchema):
    """Input schema for the music video metadata agent."""

    filename: str = Field(
        ...,
        description="The video filename (without extension), e.g. 'Eminem - Lose Yourself' or 'andrea_bocelli_con_te_partiro'",
    )
    search_results: str = Field(
        ...,
        description="Web search result snippets related to the filename, used to identify the song",
    )


class MusicVideoMetadataOutputSchema(BaseIOSchema):
    """Output schema for the music video metadata agent."""

    title: str = Field(
        ...,
        description="The official song title",
        examples=["Lose Yourself", "Con Te Partirò"],
    )
    artist: str = Field(
        ...,
        description="The primary artist or band name",
        examples=["Eminem", "Andrea Bocelli"],
    )
    album: str = Field(
        ...,
        description="The album name (empty string if unknown)",
        examples=["8 Mile Soundtrack", ""],
    )
    year: str = Field(
        ...,
        description="The release year as a 4-digit string (empty string if unknown)",
        examples=["2002", ""],
    )


class MusicVideoMetadataAgent(
    AtomicAgent[MusicVideoMetadataInputSchema, MusicVideoMetadataOutputSchema]
):
    def __init__(self):
        super().__init__(
            AgentConfig(
                client=client,
                model=OPENAI_MODEL,
                history=ChatHistory(),
                system_prompt_generator=system_prompt,
                model_api_parameters=MODEL_API_PARAMETERS,
            )
        )


agent = MusicVideoMetadataAgent()


def search_music_video(query: str, max_results: int = 5) -> str:
    """Search DuckDuckGo for music video metadata and return joined snippet text."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception:
        return ""

    if not results:
        return ""

    parts = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        if title and body:
            parts.append(f"{title}: {body}")
        elif body:
            parts.append(body)
    return "\n\n".join(parts)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "- Good Charlotte - The Click. (Official Video) [y13YF3re7MQ]"

    print(f"[SEARCH] Searching for: {query}")
    results = search_music_video(query)
    if not results:
        print("[SKIP] No search results found")
        sys.exit(1)

    print(f"[SEARCH] Got {len(results.split(chr(10)))} lines of results")

    input_data = MusicVideoMetadataInputSchema(
        filename=query,
        search_results=results,
    )

    print(f"[AGENT] Querying LLM for metadata...")
    output = agent.run(input_data)

    print(f"Title:  {output.title}")
    print(f"Artist: {output.artist}")
    print(f"Album:  {output.album}")
    print(f"Year:   {output.year}")
