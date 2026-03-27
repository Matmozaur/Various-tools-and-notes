"""
Multi-Agent Collaboration Example

Demonstrates how multiple agents can work together collaboratively,
sharing a common context and contributing different perspectives.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Priority(Enum):
    """Priority levels for issues and suggestions."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Insight:
    """An insight contributed by an agent."""
    agent: str
    category: str
    priority: Priority
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SharedContext:
    """Shared context accessible to all agents."""
    code: str
    language: str
    insights: list[Insight] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_insight(self, insight: Insight):
        """Add an insight to the shared context."""
        self.insights.append(insight)
    
    def get_insights_by_priority(self, priority: Priority) -> list[Insight]:
        """Get all insights of a specific priority."""
        return [i for i in self.insights if i.priority == priority]
    
    def get_insights_by_agent(self, agent_name: str) -> list[Insight]:
        """Get all insights from a specific agent."""
        return [i for i in self.insights if i.agent == agent_name]


class CollaborativeAgent:
    """Base class for collaborative agents."""
    
    def __init__(self, name: str, specialization: str):
        self.name = name
        self.specialization = specialization
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    async def contribute(self, context: SharedContext) -> list[Insight]:
        """
        Analyze the context and contribute insights.
        
        Args:
            context: Shared context with code and existing insights
            
        Returns:
            List of insights contributed by this agent
        """
        raise NotImplementedError
    
    def _create_insight(
        self,
        category: str,
        priority: Priority,
        message: str,
        **details
    ) -> Insight:
        """Helper to create an insight."""
        return Insight(
            agent=self.name,
            category=category,
            priority=priority,
            message=message,
            details=details
        )


class SecurityAgent(CollaborativeAgent):
    """Agent specialized in security analysis."""
    
    def __init__(self):
        super().__init__("SecurityExpert", "Security & Vulnerabilities")
    
    async def contribute(self, context: SharedContext) -> list[Insight]:
        """Analyze code for security vulnerabilities."""
        self.logger.info("Analyzing security...")
        await asyncio.sleep(0.3)
        
        insights = []
        code = context.code.lower()
        
        # Check for common security issues
        if "password" in code and "input(" in code:
            insights.append(self._create_insight(
                category="security",
                priority=Priority.CRITICAL,
                message="Password being read from unsafe input",
                recommendation="Use secure input method or environment variables"
            ))
        
        if "eval(" in code:
            insights.append(self._create_insight(
                category="security",
                priority=Priority.CRITICAL,
                message="Use of eval() detected - major security risk",
                recommendation="Refactor to avoid eval()"
            ))
        
        if "sql" in code and "+" in code:
            insights.append(self._create_insight(
                category="security",
                priority=Priority.HIGH,
                message="Possible SQL injection vulnerability",
                recommendation="Use parameterized queries"
            ))
        
        # Add to shared context
        for insight in insights:
            context.add_insight(insight)
        
        self.logger.info(f"Found {len(insights)} security concerns")
        return insights


class PerformanceAgent(CollaborativeAgent):
    """Agent specialized in performance optimization."""
    
    def __init__(self):
        super().__init__("PerformanceExpert", "Performance & Optimization")
    
    async def contribute(self, context: SharedContext) -> list[Insight]:
        """Analyze code for performance issues."""
        self.logger.info("Analyzing performance...")
        await asyncio.sleep(0.3)
        
        insights = []
        code = context.code
        
        # Check for common performance issues
        if "for" in code and "for" in code[code.index("for")+3:]:
            insights.append(self._create_insight(
                category="performance",
                priority=Priority.MEDIUM,
                message="Nested loops detected - O(n²) complexity",
                recommendation="Consider using hash map or optimized algorithm",
                complexity="O(n²)"
            ))
        
        if code.count("append(") > 5:
            insights.append(self._create_insight(
                category="performance",
                priority=Priority.LOW,
                message="Multiple append operations in loop",
                recommendation="Consider list comprehension or pre-allocation",
                optimization_potential="30-50% faster"
            ))
        
        # Add to shared context
        for insight in insights:
            context.add_insight(insight)
        
        self.logger.info(f"Found {len(insights)} performance issues")
        return insights


class MaintainabilityAgent(CollaborativeAgent):
    """Agent specialized in code maintainability."""
    
    def __init__(self):
        super().__init__("MaintainabilityExpert", "Code Quality & Maintainability")
    
    async def contribute(self, context: SharedContext) -> list[Insight]:
        """Analyze code for maintainability."""
        self.logger.info("Analyzing maintainability...")
        await asyncio.sleep(0.3)
        
        insights = []
        code = context.code
        lines = code.split('\n')
        
        # Check function length
        if len(lines) > 50:
            insights.append(self._create_insight(
                category="maintainability",
                priority=Priority.MEDIUM,
                message=f"Function is too long ({len(lines)} lines)",
                recommendation="Break into smaller functions",
                lines=len(lines)
            ))
        
        # Check for magic numbers
        import re
        numbers = re.findall(r'\b\d+\b', code)
        if len(numbers) > 3:
            insights.append(self._create_insight(
                category="maintainability",
                priority=Priority.LOW,
                message="Multiple magic numbers found",
                recommendation="Extract to named constants",
                magic_numbers=numbers
            ))
        
        # Check for documentation
        if '"""' not in code and "'''" not in code:
            insights.append(self._create_insight(
                category="maintainability",
                priority=Priority.MEDIUM,
                message="Missing docstring",
                recommendation="Add docstring explaining function purpose"
            ))
        
        # Add to shared context
        for insight in insights:
            context.add_insight(insight)
        
        self.logger.info(f"Found {len(insights)} maintainability issues")
        return insights


class TestabilityAgent(CollaborativeAgent):
    """Agent specialized in testability analysis."""
    
    def __init__(self):
        super().__init__("TestabilityExpert", "Testing & Testability")
    
    async def contribute(self, context: SharedContext) -> list[Insight]:
        """Analyze code for testability."""
        self.logger.info("Analyzing testability...")
        await asyncio.sleep(0.3)
        
        insights = []
        code = context.code
        
        # Check for hard dependencies
        if "import requests" in code or "import urllib" in code:
            insights.append(self._create_insight(
                category="testability",
                priority=Priority.MEDIUM,
                message="Hard dependency on external HTTP library",
                recommendation="Use dependency injection for easier mocking"
            ))
        
        # Check for global state
        if "global " in code:
            insights.append(self._create_insight(
                category="testability",
                priority=Priority.HIGH,
                message="Uses global state",
                recommendation="Refactor to use parameters and return values"
            ))
        
        # Suggest test cases based on other insights
        security_issues = context.get_insights_by_agent("SecurityExpert")
        if security_issues:
            insights.append(self._create_insight(
                category="testability",
                priority=Priority.HIGH,
                message=f"Need security tests for {len(security_issues)} vulnerabilities",
                recommendation="Add negative test cases for security issues"
            ))
        
        # Add to shared context
        for insight in insights:
            context.add_insight(insight)
        
        self.logger.info(f"Found {len(insights)} testability issues")
        return insights


class SupervisorAgent:
    """Supervisor that coordinates collaborative agents."""
    
    def __init__(self, agents: list[CollaborativeAgent]):
        self.agents = agents
        self.logger = logging.getLogger(f"{__name__}.Supervisor")
    
    async def analyze(self, code: str, language: str = "python") -> SharedContext:
        """
        Coordinate agents to analyze code collaboratively.
        
        Args:
            code: Source code to analyze
            language: Programming language
            
        Returns:
            SharedContext with all insights
        """
        # Create shared context
        context = SharedContext(code=code, language=language)
        
        self.logger.info(f"Starting collaborative analysis with {len(self.agents)} agents")
        
        # Run all agents concurrently
        tasks = [agent.contribute(context) for agent in self.agents]
        await asyncio.gather(*tasks)
        
        self.logger.info(f"Analysis complete. Total insights: {len(context.insights)}")
        
        return context
    
    def synthesize_report(self, context: SharedContext) -> str:
        """Generate a comprehensive report from all insights."""
        lines = []
        lines.append("="*70)
        lines.append("COLLABORATIVE CODE ANALYSIS REPORT")
        lines.append("="*70)
        lines.append("")
        
        # Summary by priority
        for priority in Priority:
            insights = context.get_insights_by_priority(priority)
            if insights:
                lines.append(f"\n{priority.value.upper()} PRIORITY ({len(insights)} items)")
                lines.append("-" * 70)
                for insight in insights:
                    lines.append(f"\n[{insight.agent}] {insight.message}")
                    if "recommendation" in insight.details:
                        lines.append(f"  → {insight.details['recommendation']}")
                    lines.append("")
        
        # Agent contributions summary
        lines.append("\n" + "="*70)
        lines.append("AGENT CONTRIBUTIONS")
        lines.append("="*70)
        for agent in set(i.agent for i in context.insights):
            agent_insights = context.get_insights_by_agent(agent)
            lines.append(f"{agent}: {len(agent_insights)} insights")
        
        return "\n".join(lines)


async def main():
    """Main example execution."""
    
    # Sample code with various issues
    sample_code = """
def process_user_data(user_id):
    password = input("Enter password: ")
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    
    results = []
    for item in get_items():
        for detail in get_details(item):
            results.append(detail)
    
    response = requests.get("http://api.example.com/data")
    
    return results
"""
    
    # Create collaborative agents
    agents = [
        SecurityAgent(),
        PerformanceAgent(),
        MaintainabilityAgent(),
        TestabilityAgent()
    ]
    
    # Create supervisor
    supervisor = SupervisorAgent(agents)
    
    # Analyze code
    print("Starting collaborative analysis...\n")
    context = await supervisor.analyze(sample_code)
    
    # Generate and print report
    report = supervisor.synthesize_report(context)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
