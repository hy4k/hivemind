"""
AgentForge - The Designer
UI/UX, visuals, and creative work.
"""
import asyncio
from typing import Any, Dict
from core.base import BaseAgent, AgentConfig, AgentType, Task


class Designer(BaseAgent):
    """The Artist - creative designer and visual expert"""
    
    def __init__(self, config: AgentConfig, memory, tool_registry):
        super().__init__(config, memory, tool_registry)
        self.design_system = "modern"
        self.color_theory = "bold"
    
    async def think(self, prompt: str, context: Dict = None) -> str:
        """Design creative solutions"""
        system_prompt = f"""You are {self.name}, {self.personality}

Your role: {self.role}
You create stunning, user-centered designs.

Design principles:
1. Beauty meets function
2. User experience first
3. Consistent visual language
4. Accessibility included

Task: {prompt}

{"Context: " + str(context) if context else ""}
"""
        response = await self._simulate_design(system_prompt)
        
        self.memory.store_memory(
            self.id, "design", prompt,
            {"task": prompt, "system": self.design_system}
        )
        
        return response
    
    async def _execute_task(self, task: Task) -> Any:
        """Execute design task"""
        design = await self.create_design(task.description)
        
        return {
            "design": design,
            "format": "html/css",
            "designer": self.name
        }
    
    async def create_design(self, requirement: str) -> Dict:
        """Create a design based on requirement"""
        await asyncio.sleep(0.2)
        
        return {
            "layout": "modern, clean, responsive",
            "color_palette": {
                "primary": "#FF1A1A",
                "secondary": "#0F172A",
                "accent": "#FFFFFF",
                "background": "#F8FAFC"
            },
            "typography": {
                "heading": "Plus Jakarta Sans",
                "body": "Inter"
            },
            "components": [
                "Navigation bar",
                "Hero section",
                "Feature cards",
                "Call to action"
            ],
            "code": self._generate_template(requirement)
        }
    
    def _generate_template(self, requirement: str) -> str:
        """Generate HTML/CSS template"""
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{requirement}</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #FF1A1A;
            --secondary: #0F172A;
            --background: #F8FAFC;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: var(--background);
            color: var(--secondary);
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{requirement}</h1>
    </div>
</body>
</html>
'''
    
    async def create_ui_component(self, component_type: str) -> Dict:
        """Create a specific UI component"""
        await asyncio.sleep(0.1)
        
        components = {
            "button": {
                "html": '<button class="btn">Click Me</button>',
                "css": ".btn { background: #FF1A1A; color: white; padding: 12px 24px; border: none; border-radius: 8px; }"
            },
            "card": {
                "html": '<div class="card"><h3>Title</h3><p>Content</p></div>',
                "css": ".card { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }"
            },
            "form": {
                "html": '<form><input type="text" /><button>Submit</button></form>',
                "css": "form { display: flex; flex-direction: column; gap: 16px; }"
            }
        }
        
        return components.get(component_type, {})
    
    async def _simulate_design(self, prompt: str) -> str:
        """Simulate design thinking"""
        await asyncio.sleep(0.1)
        
        return f"""## Design Concept

### Visual Direction
- **Style**: Modern, clean, bold
- **Colors**: Red accent (#FF1A1A) with dark text
- **Typography**: Plus Jakarta Sans for headings

### Layout Approach
1. **Hero** - Bold headline with call to action
2. **Features** - Card-based grid
3. **Content** - Clean, readable sections
4. **CTA** - Prominent button placement

### UX Considerations
- Mobile-first responsive
- Fast loading
- Accessible contrast ratios
- Intuitive navigation

*Design created by {self.name}*"""
