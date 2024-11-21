import reflex as rx
from crewai_tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from crewai import Agent, Crew, Process, Task
from crewai.telemetry import Telemetry
from imagine.langchain import ImagineLLM
import time
import asyncio

# Disable CrewAI telemetry
def noop(*args, **kwargs):
    pass

for attr in dir(Telemetry):
    if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
        setattr(Telemetry, attr, noop)

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
            search = DuckDuckGoSearchRun()
            return search.invoke(query)
        return search_tool
    async def process_research(self, form_data: dict[str, str]):
        """Process the research request using CrewAI."""
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
            llm = ImagineLLM(max_tokens=500, temperature=0.2)
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
                llm=llm,
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
                    "3. Combine information from multiple sources into a cohesive narrative.\n"
                    "4. Write a comprehensive yet concise synthesis.\n"
                    "5. Maintain a factual and professional tone, adhering to journalistic objectivity.\n"
                    "6. Write in markdown format."
                ),
                verbose=True,
                allow_delegation=False,
                tools=[],
                llm=llm,
                cache=True,
            )

            # Define Tasks
            task_1 = Task(
                description=f"Research about {query_text}, including famous papers and related architecture. Summarize findings.",
                agent=research_agent,
                expected_output=f"Provide a list of main famous articles about {query_text}, key findings, and its architecture."
            )
            
            task_2 = Task(
                description=f"Write a detailed blog about {query_text} based on the research findings.",
                agent=writer,
                expected_output=f"Write a markdown-formatted blog post summarizing the key points of {query_text}, focusing on architecture and important papers."
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

            # Execute Research and Writing
            result = research_crew.kickoff()

            self.research_result = str(result)
            self.processing = False
            self.result_ready = True
            yield

        except Exception as ex:
            self.processing = False
            yield rx.window_alert(f"Error during research process: {ex}")


def index():
    return rx.center(
        rx.vstack(
            rx.heading("AI Blog Agent", font_size="1.5em"),
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
app.add_page(index, title="Agentic Blogger")
