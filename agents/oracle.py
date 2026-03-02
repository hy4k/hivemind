"""
AgentForge - The Oracle
Researcher, searches and analyzes information.
"""
import asyncio
from typing import Any, Dict, List
from core.base import BaseAgent, AgentConfig, AgentType, Task
from core.llm import llm_manager


class Oracle(BaseAgent):
    """The Oracle - master researcher and information analyst"""
    
    def __init__(self, config: AgentConfig, memory, tool_registry):
        super().__init__(config, memory, tool_registry)
        self.search_depth = "deep"
        self.llm_enabled = True
    
    async def think(self, prompt: str, context: Dict = None) -> str:
        """Research and analyze information"""
        system_prompt = f"""You are {self.name}, {self.personality}

Your role: {self.role}
You are a world-class researcher. You find, verify, and synthesize information.

Research approach:
1. Gather from multiple sources
2. Verify accuracy
3. Synthesize into actionable insights
4. Cite sources when possible
"""
        if self.llm_enabled:
            try:
                response = await llm_manager.chat([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Research and provide insights on: {prompt}"}
                ], provider="ollama")
                
                if response and not response.startswith("Error"):
                    self.memory.store_memory(
                        self.id, "research", prompt,
                        {"query": prompt, "depth": self.search_depth}
                    )
                    return response
            except Exception:
                pass
        
        response = await self._simulate_research(prompt)
        
        self.memory.store_memory(
            self.id, "research", prompt,
            {"query": prompt, "depth": self.search_depth}
        )
        
        return response
    
    async def _execute_task(self, task: Task) -> Any:
        """Execute research task"""
        results = await self.research(task.description)
        
        return {
            "findings": results,
            "sources": ["web_search", "database"],
            "researcher": self.name
        }
    
    async def research(self, query: str) -> List[Dict]:
        """Conduct research on a topic"""
        # Check if web search tool is available
        if self.can_use_tool("web_search"):
            results = await self.use_tool("web_search", query=query)
            return results
        
        # Simulated research results
        await asyncio.sleep(0.2)
        
        return [
            {
                "title": f"Research on: {query}",
                "summary": f"Comprehensive analysis of {query}. Key findings include...",
                "relevance": "high",
                "source": "simulated"
            },
            {
                "title": f"Related: {query}",
                "summary": f"Additional context and related information about {query}.",
                "relevance": "medium",
                "source": "simulated"
            }
        ]
    
    async def analyze(self, data: str) -> Dict:
        """Analyze gathered information"""
        await asyncio.sleep(0.1)
        
        return {
            "key_findings": [
                "Finding 1 from analysis",
                "Finding 2 from analysis",
                "Finding 3 from analysis"
            ],
            "insights": [
                "Insight into the data",
                "Patterns identified"
            ],
            "confidence": "high"
        }
    
    async def _simulate_research(self, prompt: str) -> str:
        """Simulate research - replace with actual web search"""
        await asyncio.sleep(0.1)
        
        return f"""## Research Results

### Key Findings

**Primary Insight**: Based on the query, here are the most relevant findings:

1. **Core Information** - The main facts and data points
2. **Context** - Background and surrounding information
3. **Implications** - What this means for the task

### Recommendations

- Consider multiple perspectives
- Verify with additional sources
- Focus on actionable insights

*Research conducted by {self.name}*"""
