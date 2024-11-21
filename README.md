# AI Research Assistant

An intelligent research and writing tool built with Reflex, Imagine SDK and CrewAI that allows users to research a topic and generate a concise, well-structured blog post using advanced AI-powered research and writing agents.

## Features
- Perform in-depth research on any topic
- Utilize multiple AI agents for comprehensive information gathering
- Generate structured, markdown-formatted research outputs
- User-friendly web interface
- Real-time processing with async functionality

## Installation

1. Clone the repository:
```bash
git clone hhttps://github.com/Sumanth077/agentic-blogger.git
cd agentic-blogger
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate # On Windows, use `venv\Scripts\activate`
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Environment Variables:
   - Visit [https://cloudai.cirrascale.com/api-keys](https://cloudai.cirrascale.com/api-keys) to sign up and obtain your API key
   - Create a `.env` file in the project root directory
   - Add the following environment variables:
     ```
     IMAGINE_API_KEY="your_cloudai_api_key_here"
     IMAGINE_API_ENDPOINT="https://cloudai.cirrascale.com/apis/v2"
     ```
   - Replace `"your_cloudai_api_key_here"` with the actual API key you received

## Running the Application
```bash
reflex run
```

## How It Works
The AI Research Assistant uses two specialized agents:

1. **Research Agent**:
- Searches for the most relevant and recent information
- Retrieves data from reputable sources
- Provides structured search results

2. **Writing Agent**:
- Analyzes raw research results
- Identifies key themes and important information
- Synthesizes a cohesive narrative
- Generates a markdown-formatted blog post

## Customization
You can customize the agents' roles, goals, and backstories in the `process_research` method to suit different research needs.