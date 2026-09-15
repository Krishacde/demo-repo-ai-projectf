# ✈️ TripMate AI — A Multi-Agent Travel Planner with LangGraph

An intelligent, multi-agent AI travel planning platform that turns natural-language trip requests into comprehensive, customized travel plans—complete with real-time flight suggestions, hotel recommendations, activity schedules, and structured day-by-day itineraries.

Built with **LangGraph**, **FastAPI**, **LangChain**, and **Google Gemini**.

---

## 🌟 Key Features

- 🤖 **Multi-Agent Orchestration**: Specialized agents handle flight research, hotel discovery, itinerary planning, and response synthesis.
- ✈️ **Flight Discovery**: Real-time airline and schedule lookups powered by AviationStack.
- 🏨 **Hotel & Destination Research**: Live web search and location research powered by Tavily.
- 📋 **Structured Itinerary Planning**: Pydantic-validated, day-by-day activity schedules and budget allocation.
- 💾 **State Persistence**: Multi-turn conversation and session state checkpointing with PostgreSQL.
- 🌐 **Modern Web Interface**: Responsive frontend with intuitive travel forms, discovery dashboard, and itinerary export.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Agent Orchestration**: LangGraph, LangChain
- **LLM**: Google Gemini (`google-genai`), Groq
- **Tools & APIs**: Tavily API, AviationStack API
- **Database / State**: PostgreSQL (`psycopg[binary]`, `langgraph-checkpoint-postgres`)
- **Frontend**: HTML5, CSS3, JavaScript, Jinja2 Templates

---

## 📁 Project Structure

```text
├── app.py                     # FastAPI application entry point & routes
├── backend.py                 # LangGraph multi-agent workflow & state graph
├── requirements.txt           # Python dependencies
├── static/                    # Frontend static assets (CSS, JS, media)
│   ├── style.css              # Application styling
│   ├── script.js             # Client-side planner interactions
│   └── discover.js           # Discovery page scripts
├── templates/                 # Jinja2 HTML templates
│   ├── index.html             # Main travel planner interface
│   └── discover.html          # Destination discovery page
├── tools/                     # Agent tools & integrations
│   ├── flight_tool.py         # AviationStack flight search tool
│   └── tavily_tool.py         # Tavily web & hotel search tool
├── .env.example               # Template environment configuration
└── README.md                  # Project documentation
```

---

## 🚀 Quick Start Guide for Friends & Teammates

### 1. Prerequisites

Ensure you have installed:
- [Python 3.10+](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/) (running locally or cloud database)
- [Git](https://git-scm.com/)

---

### 2. Clone the Repository

```bash
git clone https://github.com/Krishacde/demo-repo-ai-project.git
cd demo-repo-ai-project
```

---

### 3. Set Up Virtual Environment

**On Windows (PowerShell / Command Prompt):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Configure Environment Variables

Copy the example configuration file:

```bash
cp .env.example .env
```

Open `.env` in your editor and provide your keys:

```env
# Database configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tripmate

# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Tool API Keys
TAVILY_API_KEY=your_tavily_api_key_here
AVIATIONSTACK_API_KEY=your_aviationstack_api_key_here

# Default Departure Airport
DEFAULT_ORIGIN_IATA=JFK
```

---

### 6. Run the Application

Start the server using:

```bash
python app.py
```

Then open your browser and visit:

👉 **`http://127.0.0.1:8000/`**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Main travel planner web interface |
| `GET` | `/discover` | Destination inspiration & discovery view |
| `GET` | `/health` | Server health check endpoint |
| `POST` | `/api/travel` | Natural-language trip planning endpoint |
| `POST` | `/api/trips` | Structured guided planner submission |

---

## 🧠 Multi-Agent Workflow

1. **User Request**: User provides travel destination, dates, preferences, and budget.
2. **Flight Agent**: Gathers available flight options and schedules.
3. **Hotel Agent**: Researches matching accommodations and neighborhood spots.
4. **Itinerary Agent**: Coordinates flights, hotels, and points of interest into daily schedules.
5. **Final Response Agent**: Formats the synthesized plan for real-time frontend rendering.

---

## 👤 Author

Developed by **[Krishacde](https://github.com/Krishacde)**.
