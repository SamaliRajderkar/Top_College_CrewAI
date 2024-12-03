
import typing
import asyncio
import os
import aiohttp
import reflex as rx  # Reflex should be imported as `rx`
from bs4 import BeautifulSoup
from crewai.telemetry import Telemetry
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable CrewAI telemetry
def noop(*args, **kwargs):
    pass

for attr in dir(Telemetry):
    if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
        setattr(Telemetry, attr, noop)

# Load the Groq API key and URL from environment variables
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = os.getenv('GROQ_API_URL')

# Define the Reflex State class
class State(rx.State):
    """The app state."""
    research_result: str = ""
    processing: bool = False
    result_ready: bool = False

    async def process_research(self, form_data: typing.Dict[str, typing.Any]):
        """Process the research request using CrewAI and Groq."""
        query_text: str = form_data["query_text"]

        if not query_text:
            rx.toast("Please enter a topic to process.")
            return

        # Reset states
        self.result_ready = False
        self.processing = True
        yield

        try:
            # Fetch search results using DuckDuckGo's HTML
            search_results = await self.get_search_results(query_text)
            print("Search Tool Results:", search_results)

            if not search_results:
                self.research_result = "No relevant research results found."
                self.processing = False
                self.result_ready = True
                yield
                return

            # Format the input for Groq API
            formatted_input = f"Please summarize the following research findings:\n{search_results}"

            # Query Groq's API
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "max_tokens": 1000,
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": formatted_input}]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(GROQ_API_URL, json=payload, headers=headers) as groq_response:
                    if groq_response.status == 200:
                        response_data = await groq_response.json()
                        print("Groq Response Data:", response_data)
                        
                        # Extract the summary
                        summary = response_data.get("choices", [{}])[0].get("message", {}).get("content")
                        if summary:
                            self.research_result = summary
                        else:
                            self.research_result = "Groq API did not return a summary. Please try again."
                    else:
                        self.research_result = f"Error with Groq API: {groq_response.status}"
        except Exception as ex:
            self.research_result = f"Error during research process: {ex}"

        self.processing = False
        self.result_ready = True
        yield

    async def get_search_results(self, query: str):
        """Search for a query using DuckDuckGo and parse HTML for results."""
        url = f"https://duckduckgo.com/html/?q={query}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, "html.parser")

                    # Extract results
                    results = []
                    for result in soup.select(".result__title"):
                        text = result.get_text(strip=True)
                        if text:
                            results.append(text)

                    if results:
                        return "\n".join(results[:10])  # Return top 10 results
                    else:
                        return "No relevant results found on DuckDuckGo."
                else:
                    return f"Error fetching data from DuckDuckGo. Status code: {response.status}"

# Reflex app UI
def index():
    return rx.center(
        rx.vstack(
            rx.heading("AI Blog Agent with Groq", font_size="1.5em"),
            rx.form(
                rx.vstack(
                    rx.input(
                        id="query_text",
                        placeholder="Enter your topic...",
                        size="3",
                    ),
                    rx.button(
                        "Process",
                        type="submit",
                        size="3",
                    ),
                    align="stretch",
                    spacing="2",
                ),
                width="100%",
                on_submit=State.process_research,
            ),
            rx.cond(
                State.processing,
                rx.spinner(),
                rx.cond(
                    State.result_ready,
                    rx.box(
                        rx.markdown(State.research_result),
                        padding="4",
                        border="1px solid #eaeaea",
                        border_radius="md",
                        width="100%",
                        max_height="400px",
                        overflow_y="auto",
                    ),
                ),
            ),
            width="50em",
            bg="white",
            padding="2em",
            align="center",
            border_radius="lg",
            box_shadow="lg",
        ),
        width="100%",
        height="100vh",
        background="radial-gradient(circle at 22% 11%,rgba(62, 180, 137,.20),hsla(0,0%,100%,0) 19%),radial-gradient(circle at 82% 25%,rgba(33,150,243,.18),hsla(0,0%,100%,0) 35%),radial-gradient(circle at 25% 61%,rgba(250, 128, 114, .28),hsla(0,0%,100%,0) 55%)",
    )

# Create the app with theme
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="blue",
    ),
)
app.add_page(index, title="Agentic Blogger with Groq")
