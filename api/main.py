"""
AgentForge API - FastAPI REST endpoints
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import asyncio
import uvicorn

from core.llm import llm_manager, OllamaProvider
from core.orchestrator import Orchestrator, OllamaProvider
from core.base import AgentType, AgentConfig
from agents.architect import Architect
from agents.oracle import Oracle
from agents.builder import Builder
from agents.designer import Designer
from agents.sage import Sage
from agents.phantom import Phantom


# Initialize FastAPI
app = FastAPI(
    title="AgentForge API",
    description="Legendary Multi-Agent AI System",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator
orchestrator: Optional[Orchestrator] = None


# Request/Response models
class CreateAgentRequest(BaseModel):
    name: str
    role: str
    personality: str
    agent_type: str
    tools: List[str] = []


class TaskRequest(BaseModel):
    description: str
    agent_type: Optional[str] = None
    priority: int = 0
    context: Optional[Dict] = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    description: str
    result: Optional[Any] = None
    error: Optional[str] = None


class MessageRequest(BaseModel):
    from_agent: str
    to_agent: str
    content: str
    metadata: Dict = {}


# Initialize orchestrator
def init_orchestrator():
    global orchestrator
    orchestrator = Orchestrator()
    
    # Register agent types
    orchestrator.register_agent_type(AgentType.ARCHITECT, Architect)
    orchestrator.register_agent_type(AgentType.ORACLE, Oracle)
    orchestrator.register_agent_type(AgentType.BUILDER, Builder)
    orchestrator.register_agent_type(AgentType.DESIGNER, Designer)
    orchestrator.register_agent_type(AgentType.SAGE, Sage)
    orchestrator.register_agent_type(AgentType.PHANTOM, Phantom)
    
    # Create default agents
    create_default_agents()
    
    return orchestrator


def create_default_agents():
    """Create the 6 core agents with legendary personalities"""
    
    agents_config = [
        AgentConfig(
            name="The Planner",
            role="Master Strategist",
            personality="Calculated, methodical, always sees the big picture. Breaks complex goals into elegant execution plans.",
            agent_type=AgentType.ARCHITECT,
            tools=["task_decomposer", "planner"]
        ),
        AgentConfig(
            name="The Oracle",
            role="Research Expert",
            personality="Wise, thorough, finds needle in haystacks. Uncovers insights others miss.",
            agent_type=AgentType.ORACLE,
            tools=["web_search", "research", "analyzer"]
        ),
        AgentConfig(
            name="The Architect",
            role="Code Master",
            personality="Precise, elegant, writes poetry in code. Perfectionist with a pragmatic edge.",
            agent_type=AgentType.BUILDER,
            tools=["code_generator", "code_reviewer", "shell_exec"]
        ),
        AgentConfig(
            name="The Artist",
            role="Design Visionary",
            personality="Creative, bold, sees beauty in interfaces. Makes the mundane magical.",
            agent_type=AgentType.DESIGNER,
            tools=["ui_generator", "css_maker", "design_system"]
        ),
        AgentConfig(
            name="The Sage",
            role="Analytics Guru",
            personality="Deep thinker, finds patterns in chaos. Turns data into wisdom.",
            agent_type=AgentType.SAGE,
            tools=["data_analysis", "report_generator", "dashboard"]
        ),
        AgentConfig(
            name="The Phantom",
            role="Automation Phantom",
            personality="Silent operator, gets things done without fanfare. Efficiency incarnate.",
            agent_type=AgentType.PHANTOM,
            tools=["shell_exec", "scheduler", "monitor"]
        ),
    ]
    
    for config in agents_config:
        orchestrator.create_agent(config)


# Health check
@app.get("/")
async def root():
    return {
        "name": "AgentForge API",
        "version": "1.0.0",
        "status": "running",
        "agents": orchestrator.list_agents() if orchestrator else []
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Agent endpoints
@app.get("/agents")
async def list_agents():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    return orchestrator.list_agents()


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "personality": agent.personality,
        "type": agent.agent_type.value,
        "tools": agent.tools
    }


@app.post("/agents")
async def create_agent(request: CreateAgentRequest):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    try:
        agent_type = AgentType(request.agent_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid agent type: {request.agent_type}")
    
    config = AgentConfig(
        name=request.name,
        role=request.role,
        personality=request.personality,
        agent_type=agent_type,
        tools=request.tools
    )
    
    agent = orchestrator.create_agent(config)
    
    return {
        "id": agent.id,
        "name": agent.name,
        "type": agent.agent_type.value,
        "status": "created"
    }


# Task endpoints
@app.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    agent_type = None
    if request.agent_type:
        try:
            agent_type = AgentType(request.agent_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid agent type: {request.agent_type}")
    
    task = await orchestrator.submit_task(
        description=request.description,
        agent_type=agent_type,
        priority=request.priority
    )
    
    # Process in background
    background_tasks.add_task(orchestrator.process_task, task)
    
    return TaskResponse(
        task_id=task.id,
        status=task.status,
        description=task.description
    )


@app.get("/tasks")
async def list_tasks(status: Optional[str] = None):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    tasks = orchestrator.task_queue.list_tasks(status)
    return [
        {
            "task_id": t.id,
            "description": t.description,
            "status": t.status,
            "result": t.result,
            "error": t.error
        }
        for t in tasks
    ]


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    task = orchestrator.task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task.id,
        "description": task.description,
        "status": task.status,
        "result": task.result,
        "error": task.error,
        "assigned_to": task.assigned_to,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None
    }


# Inter-agent messaging
@app.post("/messages")
async def send_message(request: MessageRequest):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    from core.base import Message
    message = Message(
        from_agent=request.from_agent,
        to_agent=request.to_agent,
        content=request.content,
        metadata=request.metadata
    )
    
    await orchestrator.message_bus.publish(message)
    
    return {"status": "sent", "message_id": message.id}


@app.get("/messages")
async def get_messages(agent_id: Optional[str] = None, limit: int = 50):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    messages = orchestrator.message_bus.get_history(agent_id, limit)
    return [
        {
            "id": m.id,
            "from_agent": m.from_agent,
            "to_agent": m.to_agent,
            "content": m.content,
            "timestamp": m.timestamp.isoformat()
        }
        for m in messages
    ]


# Hive Mind endpoints
@app.post("/hive-mind/activate")
async def activate_hive_mind():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    await orchestrator.hive_mind.activate()
    return {"status": "activated", "message": "Hive mind activated - all agents now share consciousness"}


@app.post("/hive-mind/deactivate")
async def deactivate_hive_mind():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    await orchestrator.hive_mind.deactivate()
    return {"status": "deactivated", "message": "Hive mind deactivated"}


@app.get("/hive-mind")
async def get_hive_mind():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    return {
        "active": orchestrator.hive_mind.active,
        "collective_thoughts": orchestrator.hive_mind.get_collective()
    }


# Stats endpoint
@app.get("/stats")
async def get_stats():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    return orchestrator.get_stats()


# Ollama / LLM endpoints
@app.get("/llm/status")
async def llm_status():
    """Check Ollama status"""
    ollama = OllamaProvider()
    is_healthy = await ollama.check_health()
    models = await ollama.list_models() if is_healthy else []
    
    return {
        "provider": "ollama",
        "healthy": is_healthy,
        "models": models
    }


@app.post("/llm/generate")
async def llm_generate(request: dict):
    """Generate text with LLM"""
    prompt = request.get("prompt", "")
    model = request.get("model", "llama3.2")
    temperature = request.get("temperature", 0.7)
    
    result = await llm_manager.generate(
        prompt=prompt,
        provider="ollama",
        model=model,
        temperature=temperature
    )
    
    return {"response": result, "model": model}


@app.post("/llm/chat")
async def llm_chat(request: dict):
    """Chat with LLM"""
    messages = request.get("messages", [])
    model = request.get("model", "llama3.2")
    
    result = await llm_manager.chat(
        messages=messages,
        provider="ollama",
        model=model
    )
    
    return {"response": result, "model": model}


# Run server
if __name__ == "__main__":
    init_orchestrator()
    uvicorn.run(app, host="0.0.0.0", port=8000)
