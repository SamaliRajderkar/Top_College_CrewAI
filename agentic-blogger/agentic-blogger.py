'''
.env file

GROQ_API_KEY="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"
GROQ_API_URL="https://api.groq.com/openai/v1/chat/completions"

'''


import reflex as rx
from crewai_tools import tool
from crewai import Agent, Crew, Process, Task
from crewai.telemetry import Telemetry
import requests
import asyncio
import os

# Disable CrewAI telemetry
def noop(*args, **kwargs):
    pass

for attr in dir(Telemetry):
    if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
        setattr(Telemetry, attr, noop)

# Load the Groq API key from environment variables
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = os.getenv('GROQ_API_URL')

class State(rx.State):
    """The app state."""
    research_result: str = ""
    processing: bool = False
    result_ready: bool = False

    def get_search_tool(self):
        """Initialize and return the search tool."""
        @tool
        def search_tool(query: str):
            """Search for a query on DuckDuckGo."""
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1"
            response = requests.get(url)
            print(response)
            if response.status_code == 200:
                data = response.json()
                related_topics = data.get("RelatedTopics", [])
                return "\n".join([topic.get("Text", "") for topic in related_topics if "Text" in topic])
            else:
                return "Error fetching data from DuckDuckGo."
        return search_tool

    async def process_research(self, form_data: dict[str, str]):
        """Process the research request using CrewAI and Groq."""
        query_text: str = form_data["query_text"]

        if not query_text:
            rx.toast("Please enter a topic to process.")
            return
        
        # Reset states
        self.result_ready = False
        self.processing = True
        
        # Yield to show processing state
        yield

        await asyncio.sleep(1)
        
        try:
            search_tool = self.get_search_tool()

            # Research Agent: Specialized for news or information research
            research_agent = Agent(
                role="researcher",
                goal="Search and summarize relevant information on a given query.",
                backstory=( 
                    "You are a news search specialist. Your task is to:\n"
                    "1. Search for the most relevant and recent information on the given topic.\n"
                    "2. Ensure the results are from reputable sources.\n"
                    "3. Return the raw search results in a structured format."
                ),
                verbose=True,
                allow_delegation=False,
                tools=[search_tool],
                cache=True,
            )

            # Writing Agent: Synthesizes the research into a blog-style output
            writer = Agent(
                role="writer",
                goal="Create a structured and concise blog post based on research.",
                backstory=(
                    "You are a news synthesis expert. Your task is to:\n"
                    "1. Analyze the raw research results provided.\n"
                    "2. Identify key themes and important information.\n"
                    "3. Combine information into a cohesive narrative.\n"
                ),
                verbose=True,
                allow_delegation=False,
                tools=[],
                cache=True,
            )

            # Define Tasks
            task_1 = Task(
                description=f"Research about {query_text}, summarize findings.",
                agent=research_agent,
                expected_output=f"Provide a list of main articles about {query_text} and summarize key findings."
            )
            
            task_2 = Task(
                description=f"Write a detailed summary about {query_text} based on the research findings.",
                agent=writer,
                expected_output=f"Write a markdown-formatted summary of the key points of {query_text}."
            )

            # Create Crew
            research_crew = Crew(
                name="Research and Writing Crew",
                agents=[research_agent, writer],
                tasks=[task_1, task_2],
                verbose=True,
                share_crew=False,
                process=Process.sequential,
            )

            # Groq integration: Query Groq's model after research task
            print(GROQ_API_KEY)
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                
                "max_tokens": 1000 ,
                "model": "llama3-8b-8192",
                "messages": [{
                        "role": "user",
                        "content": f"Summarize the following research findings: {self.research_result}"
                }]
            }

            groq_response = requests.post(GROQ_API_URL, json=payload, headers=headers)

            if groq_response.status_code == 200:
                self.research_result = groq_response.json().get("summary", "No summary returned.")
            else:
                self.research_result = "Error with Groq API."

            self.processing = False
            self.result_ready = True
            yield
            
        except Exception as ex:
            self.processing = False
            yield rx.window_alert(f"Error during research process: {ex}")

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
