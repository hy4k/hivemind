# ⚡ AgentForge - Legendary Multi-Agent AI System

A production-ready multi-agent framework with 6 distinct AI agents, each with unique personalities and capabilities.

## 🎭 The Agents

| Agent | Role | Specialty | Personality |
|-------|------|-----------|-------------|
| 📋 **The Planner** | Architect | Breaks complex goals into plans | Calculated, methodical, sees the big picture |
| 🔍 **The Oracle** | Researcher | Searches, analyzes, finds insights | Wise, thorough, finds needles in haystacks |
| 💻 **The Architect** | Builder | Writes & tests code | Precise, elegant, writes poetry in code |
| 🎨 **The Artist** | Designer | UI/UX, visuals, creative | Creative, bold, makes mundane magical |
| 📊 **The Sage** | Analyst | Data, reports, insights | Deep thinker, finds patterns in chaos |
| 🚀 **The Phantom** | Executor | Runs tasks, automation | Silent operator, efficiency incarnate |

## 🏗️ Architecture

```
agent-forge/
├── core/
│   ├── base.py          # Base Agent class, memory, tools
│   └── orchestrator.py # Task queue, message bus, hive mind
├── agents/
│   ├── architect.py     # The Planner
│   ├── oracle.py        # The Oracle
│   ├── builder.py       # The Architect
│   ├── designer.py      # The Artist
│   ├── sage.py          # The Sage
│   └── phantom.py       # The Phantom
├── api/
│   └── main.py          # FastAPI endpoints
├── ui/
│   └── dashboard.html   # Web control panel
└── memory/
    └── (SQLite databases)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd agent-forge
pip install -r requirements.txt
```

### 2. Run the API Server

```bash
python api/main.py
```

Server starts at **http://localhost:8000**

### 3. Open the Dashboard

Navigate to **http://localhost:8000/ui/dashboard.html**

## 🔌 API Endpoints

### Agents
- `GET /agents` - List all agents
- `GET /agents/{id}` - Get agent details
- `POST /agents` - Create new agent

### Tasks
- `POST /tasks` - Submit a task
- `GET /tasks` - List all tasks
- `GET /tasks/{id}` - Get task status

### Hive Mind
- `POST /hive-mind/activate` - Activate collective consciousness
- `POST /hive-mind/deactivate` - Deactivate
- `GET /hive-mind` - Get hive mind status

### Stats
- `GET /stats` - System statistics

## 💡 Usage Examples

### Submit a Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Build a REST API in Python",
    "agent_type": "builder"
  }'
```

### Get Task Result

```bash
curl http://localhost:8000/tasks/{task_id}
```

### Activate Hive Mind

```bash
curl -X POST http://localhost:8000/hive-mind/activate
```

## 🎨 Dashboard Features

- 📊 Real-time stats and metrics
- 🤖 Agent cards with personalities
- 🚀 Task submission with smart auto-assignment
- 🧠 Hive Mind toggle
- 📋 Task history and status

## 🔧 Extending the System

### Adding Custom Tools

```python
from core.base import ToolRegistry

registry = ToolRegistry()

@registry.register("my_tool")
async def my_tool(param: str):
    # Tool logic
    return result
```

### Creating Custom Agents

```python
from core.base import BaseAgent, AgentConfig, AgentType

class MyCustomAgent(BaseAgent):
    async def _execute_task(self, task):
        # Custom logic
        return result
```

## 🐝 Hive Mind Mode

When activated, all agents share consciousness:
- Collective thinking on problems
- Shared memory across agents
- Collaborative problem-solving
- Emergent intelligence

## 📦 Production Features

- ✅ SQLite persistent memory
- ✅ Async task queue with priorities
- ✅ Inter-agent messaging
- ✅ Error handling with retries
- ✅ CORS enabled
- ✅ RESTful API
- ✅ Web dashboard

## 🚢 Deployment

### Docker (Coming Soon)

```bash
docker build -t agent-forge .
docker run -p 8000:8000 agent-forge
```

### VPS Deployment

```bash
# On your VPS
pip install -r requirements.txt
nohup python api/main.py &

# Access at http://your-vps-ip:8000
```

## 🤝 Contributing

This is the foundation. Scale it to 100+ agents:
- Add more agent types
- Integrate LLMs (OpenAI, Claude, Ollama)
- Add more tools
- Build custom workflows

---

**Built with ⚡ by AgentForge**
*Legendary multi-agent system for the ambitious.*
