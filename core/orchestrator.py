"""
AgentForge Core - Orchestration Engine
Manages agent lifecycle, task distribution, and hive mind mode.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import defaultdict
import sqlite3

from core.base import BaseAgent, AgentType, AgentConfig, AgentMemory, ToolRegistry, Task, Message


class TaskQueue:
    """Async task queue with priority support"""
    
    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: Dict[str, Task] = {}
    
    async def enqueue(self, task: Task, priority: int = 0):
        self._tasks[task.id] = task
        await self._queue.put((priority, task))
    
    async def dequeue(self) -> Task:
        priority, task = await self._queue.get()
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)
    
    def list_tasks(self, status: str = None) -> List[Task]:
        if status:
            return [t for t in self._tasks.values() if t.status == status]
        return list(self._tasks.values())
    
    @property
    def size(self) -> int:
        return self._queue.qsize()


class MessageBus:
    """Inter-agent communication bus"""
    
    def __init__(self):
        self._subscribers: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self._history: List[Message] = []
        self._max_history = 1000
    
    def subscribe(self, agent_id: str) -> asyncio.Queue:
        return self._subscribers[agent_id]
    
    def unsubscribe(self, agent_id: str):
        if agent_id in self._subscribers:
            del self._subscribers[agent_id]
    
    async def publish(self, message: Message):
        self._history.append(message)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        # Direct message
        if message.to_agent:
            queue = self._subscribers.get(message.to_agent)
            if queue:
                await queue.put(message)
        
        # Broadcast to all
        if message.to_agent == "broadcast":
            for queue in self._subscribers.values():
                await queue.put(message)
    
    def get_history(self, agent_id: str = None, limit: int = 50) -> List[Message]:
        if agent_id:
            return [m for m in self._history if m.from_agent == agent_id or m.to_agent == agent_id]
        return self._history[-limit:]


class HiveMind:
    """Collective consciousness mode - all agents think together"""
    
    def __init__(self, orchestrator: 'Orchestrator'):
        self.orchestrator = orchestrator
        self.active = False
        self._collective_thought: List[Dict] = []
    
    async def activate(self):
        self.active = True
        self._collective_thought = []
    
    async def deactivate(self):
        self.active = False
    
    async def broadcast_thought(self, agent_id: str, thought: str):
        if self.active:
            self._collective_thought.append({
                "agent_id": agent_id,
                "thought": thought,
                "timestamp": datetime.now().isoformat()
            })
    
    def get_collective(self) -> List[Dict]:
        return self._collective_thought.copy()


class Orchestrator:
    """Central orchestration engine - the brain of AgentForge"""
    
    def __init__(self, db_path: str = "memory/agent_forge.db"):
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue = TaskQueue()
        self.message_bus = MessageBus()
        self.memory = AgentMemory(db_path)
        self.tool_registry = ToolRegistry()
        self.hive_mind = HiveMind(self)
        self._agent_types: Dict[AgentType, type] = {}
        self._running = False
    
    def register_agent_type(self, agent_type: AgentType, agent_class: type):
        """Register an agent class for a type"""
        self._agent_types[agent_type] = agent_class
    
    def create_agent(self, config: AgentConfig) -> BaseAgent:
        """Factory method to create agents"""
        if config.agent_type not in self._agent_types:
            raise ValueError(f"No agent class registered for {config.agent_type}")
        
        agent_class = self._agent_types[config.agent_type]
        agent = agent_class(config, self.memory, self.tool_registry)
        self.agents[agent.id] = agent
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        return [a for a in self.agents.values() if a.agent_type == agent_type]
    
    def list_agents(self) -> List[Dict]:
        return [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role,
                "type": a.agent_type.value,
                "status": "running" if a._running else "idle"
            }
            for a in self.agents.values()
        ]
    
    async def submit_task(self, description: str, agent_type: AgentType = None, 
                         priority: int = 0, context: Dict = None) -> Task:
        """Submit a task for execution"""
        task = Task(description=description)
        
        if agent_type:
            agents = self.get_agents_by_type(agent_type)
            if agents:
                task.assigned_to = agents[0].id
        
        await self.task_queue.enqueue(task, priority)
        return task
    
    async def process_task(self, task: Task) -> Task:
        """Process a single task"""
        if task.assigned_to:
            agent = self.get_agent(task.assigned_to)
            if agent:
                return await agent.execute(task)
        
        # Auto-assign based on task analysis
        agent = await self._auto_assign(task)
        if agent:
            task.assigned_to = agent.id
            return await agent.execute(task)
        
        task.error = "No suitable agent found"
        task.status = "failed"
        return task
    
    async def _auto_assign(self, task: Task) -> Optional[BaseAgent]:
        """Auto-assign task to best agent"""
        desc = task.description.lower()
        
        # Simple keyword-based routing
        if any(k in desc for k in ["plan", "design", "architecture", "break down", "strategy"]):
            return self.get_agents_by_type(AgentType.ARCHITECT)[0] if self.get_agents_by_type(AgentType.ARCHITECT) else None
        elif any(k in desc for k in ["search", "research", "find", "analyze", "look up"]):
            return self.get_agents_by_type(AgentType.ORACLE)[0] if self.get_agents_by_type(AgentType.ORACLE) else None
        elif any(k in desc for k in ["code", "build", "write", "implement", "create"]):
            return self.get_agents_by_type(AgentType.BUILDER)[0] if self.get_agents_by_type(AgentType.BUILDER) else None
        elif any(k in desc for k in ["design", "ui", "visual", "interface", "creative"]):
            return self.get_agents_by_type(AgentType.DESIGNER)[0] if self.get_agents_by_type(AgentType.DESIGNER) else None
        elif any(k in desc for k in ["report", "analyze", "insight", "data", "metrics"]):
            return self.get_agents_by_type(AgentType.SAGE)[0] if self.get_agents_by_type(AgentType.SAGE) else None
        elif any(k in desc for k in ["run", "execute", "automate", "do", "process"]):
            return self.get_agents_by_type(AgentType.PHANTOM)[0] if self.get_agents_by_type(AgentType.PHANTOM) else None
        
        # Default to architect for complex tasks
        architects = self.get_agents_by_type(AgentType.ARCHITECT)
        return architects[0] if architects else None
    
    async def decompose_task(self, task: Task) -> List[Task]:
        """Break complex task into subtasks using Architect"""
        architects = self.get_agents_by_type(AgentType.ARCHITECT)
        if not architects:
            return [task]
        
        architect = architects[0]
        decomposition = await architect.decompose(task.description)
        
        subtasks = []
        for i, subtask_desc in enumerate(decomposition):
            subtask = Task(
                description=subtask_desc,
                assigned_to=task.assigned_to
            )
            subtasks.append(subtask)
        
        task.subtasks = subtasks
        return subtasks
    
    async def execute_parallel(self, tasks: List[Task]) -> List[Task]:
        """Execute tasks in parallel"""
        results = await asyncio.gather(
            *[self.process_task(t) for t in tasks],
            return_exceptions=True
        )
        
        completed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tasks[i].status = "failed"
                tasks[i].error = str(result)
                completed.append(tasks[i])
            else:
                completed.append(result)
        
        return completed
    
    async def start(self):
        """Start the orchestrator"""
        self._running = True
    
    async def stop(self):
        """Stop the orchestrator"""
        self._running = False
    
    async def worker_loop(self):
        """Main worker loop"""
        while self._running:
            try:
                task = await asyncio.wait_for(
                    self.task_queue.dequeue(),
                    timeout=5.0
                )
                await self.process_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        return {
            "total_agents": len(self.agents),
            "agents_by_type": {
                at.value: len(self.get_agents_by_type(at))
                for at in AgentType
            },
            "queue_size": self.task_queue.size,
            "tasks": {
                "pending": len(self.task_queue.list_tasks("pending")),
                "completed": len(self.task_queue.list_tasks("completed")),
                "failed": len(self.task_queue.list_tasks("failed"))
            },
            "hive_mind_active": self.hive_mind.active
        }
