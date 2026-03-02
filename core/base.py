"""
AgentForge Core - Base Agent Class
The foundation of all agents in the system.
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import sqlite3


class AgentType(Enum):
    ARCHITECT = "architect"      # Planning, decomposition
    ORACLE = "oracle"            # Research, search, analysis
    BUILDER = "builder"          # Code execution, building
    DESIGNER = "designer"        # UI/UX, creative
    SAGE = "sage"                # Reports, insights, analytics
    PHANTOM = "phantom"          # Execution, automation


@dataclass
class Message:
    """Inter-agent message"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str = ""
    to_agent: str = ""
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Task:
    """Task representation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    subtasks: List['Task'] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    assigned_to: Optional[str] = None


@dataclass
class AgentConfig:
    name: str
    role: str
    personality: str
    agent_type: AgentType
    tools: List[str] = field(default_factory=list)
    max_retries: int = 3
    timeout: int = 300


class ToolRegistry:
    """Central registry for agent tools"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._descriptions: Dict[str, str] = {}
    
    def register(self, name: str, func: Callable, description: str = ""):
        self._tools[name] = func
        self._descriptions[name] = description
    
    def get(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)
    
    def list_tools(self) -> Dict[str, str]:
        return self._descriptions.copy()
    
    def has_tool(self, name: str) -> bool:
        return name in self._tools


class AgentMemory:
    """SQLite-backed persistent memory for agents"""
    
    def __init__(self, db_path: str = "memory/agents.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Agent memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                agent_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Task history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                agent_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_memory(self, agent_id: str, memory_type: str, content: str, metadata: Dict = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO agent_memories (agent_id, memory_type, content, metadata) VALUES (?, ?, ?, ?)",
            (agent_id, memory_type, content, json.dumps(metadata or {}))
        )
        conn.commit()
        conn.close()
    
    def get_memories(self, agent_id: str, memory_type: str = None, limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute(
                "SELECT * FROM agent_memories WHERE agent_id = ? AND memory_type = ? ORDER BY created_at DESC LIMIT ?",
                (agent_id, memory_type, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM agent_memories WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
                (agent_id, limit)
            )
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def store_conversation(self, task_id: str, agent_id: str, role: str, content: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (task_id, agent_id, role, content) VALUES (?, ?, ?, ?)",
            (task_id, agent_id, role, content)
        )
        conn.commit()
        conn.close()
    
    def store_task(self, task: Task, agent_id: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO task_history (task_id, description, status, result, agent_id, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task.id, task.description, task.status, 
              json.dumps(task.result) if task.result else None,
              agent_id or task.assigned_to,
              task.completed_at.isoformat() if task.completed_at else None))
        conn.commit()
        conn.close()


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, config: AgentConfig, memory: AgentMemory, tool_registry: ToolRegistry):
        self.id = str(uuid.uuid4())[:8]
        self.name = config.name
        self.role = config.role
        self.personality = config.personality
        self.agent_type = config.agent_type
        self.tools = config.tools
        self.max_retries = config.max_retries
        self.timeout = config.timeout
        self.memory = memory
        self.tool_registry = tool_registry
        self._running = False
    
    async def think(self, prompt: str, context: Dict = None) -> str:
        """Process a prompt and return response"""
        raise NotImplementedError
    
    async def execute(self, task: Task) -> Task:
        """Execute a task"""
        task.status = "in_progress"
        task.assigned_to = self.id
        
        for attempt in range(self.max_retries):
            try:
                result = await asyncio.wait_for(
                    self._execute_task(task),
                    timeout=self.timeout
                )
                task.result = result
                task.status = "completed"
                task.completed_at = datetime.now()
                self.memory.store_task(task, self.id)
                return task
            except asyncio.TimeoutError:
                task.error = f"Timeout after {self.timeout}s"
            except Exception as e:
                task.error = str(e)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        task.status = "failed"
        self.memory.store_task(task, self.id)
        return task
    
    async def _execute_task(self, task: Task) -> Any:
        """Override in subclasses"""
        raise NotImplementedError
    
    def can_use_tool(self, tool_name: str) -> bool:
        return tool_name in self.tools and self.tool_registry.has_tool(tool_name)
    
    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """Use a registered tool"""
        if not self.can_use_tool(tool_name):
            raise ValueError(f"Agent {self.name} cannot use tool {tool_name}")
        
        tool = self.tool_registry.get(tool_name)
        return await tool(**kwargs)
    
    def __repr__(self):
        return f"<Agent:{self.name} ({self.agent_type.value})>"
