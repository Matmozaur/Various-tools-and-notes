"""
Agent Chain Example

Demonstrates how to chain multiple agents together for sequential processing.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent_name: str
    success: bool
    data: Any
    metadata: dict[str, Any]


class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    async def process(self, input_data: Any) -> AgentResult:
        """Process input and return result."""
        raise NotImplementedError


class CodeReviewAgent(BaseAgent):
    """Agent for reviewing code quality."""
    
    def __init__(self):
        super().__init__("CodeReviewer")
    
    async def process(self, code: str) -> AgentResult:
        """Review code for quality and issues."""
        self.logger.info("Starting code review...")
        
        # Simulate code review process
        await asyncio.sleep(0.5)
        
        issues = [
            {"line": 10, "severity": "warning", "message": "Consider using type hints"},
            {"line": 25, "severity": "info", "message": "Could extract this to a function"}
        ]
        
        self.logger.info(f"Found {len(issues)} issues")
        
        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "code": code,
                "issues": issues,
                "rating": "B+"
            },
            metadata={"review_time": 0.5}
        )


class RefactoringAgent(BaseAgent):
    """Agent for refactoring code."""
    
    def __init__(self):
        super().__init__("Refactorer")
    
    async def process(self, review_result: dict[str, Any]) -> AgentResult:
        """Apply refactoring based on review issues."""
        self.logger.info("Starting refactoring...")
        
        code = review_result["code"]
        issues = review_result["issues"]
        
        # Simulate refactoring
        await asyncio.sleep(0.5)
        
        refactored_code = code  # In reality, would apply fixes
        
        self.logger.info(f"Refactored {len(issues)} issues")
        
        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "original_code": code,
                "refactored_code": refactored_code,
                "changes_applied": len(issues)
            },
            metadata={"refactor_time": 0.5}
        )


class TestWriterAgent(BaseAgent):
    """Agent for generating tests."""
    
    def __init__(self):
        super().__init__("TestWriter")
    
    async def process(self, refactor_result: dict[str, Any]) -> AgentResult:
        """Generate tests for refactored code."""
        self.logger.info("Generating tests...")
        
        code = refactor_result["refactored_code"]
        
        # Simulate test generation
        await asyncio.sleep(0.5)
        
        tests = [
            "def test_happy_path(): ...",
            "def test_edge_case(): ...",
            "def test_error_handling(): ..."
        ]
        
        self.logger.info(f"Generated {len(tests)} tests")
        
        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "code": code,
                "tests": tests,
                "coverage_estimate": 85
            },
            metadata={"test_count": len(tests)}
        )


class DocumentationAgent(BaseAgent):
    """Agent for generating documentation."""
    
    def __init__(self):
        super().__init__("Documenter")
    
    async def process(self, test_result: dict[str, Any]) -> AgentResult:
        """Generate documentation for code and tests."""
        self.logger.info("Generating documentation...")
        
        code = test_result["code"]
        tests = test_result["tests"]
        
        # Simulate documentation generation
        await asyncio.sleep(0.5)
        
        docs = {
            "api_docs": "# API Documentation\n...",
            "usage_examples": "# Examples\n...",
            "test_docs": "# Test Documentation\n..."
        }
        
        self.logger.info("Documentation complete")
        
        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "code": code,
                "tests": tests,
                "documentation": docs
            },
            metadata={"docs_pages": len(docs)}
        )


class AgentChain:
    """Chain multiple agents for sequential processing."""
    
    def __init__(self, agents: list[BaseAgent]):
        self.agents = agents
        self.logger = logging.getLogger(__name__)
    
    async def process(self, initial_input: Any) -> list[AgentResult]:
        """
        Process input through the chain of agents.
        
        Args:
            initial_input: Initial data to process
            
        Returns:
            List of results from each agent in the chain
        """
        results = []
        current_input = initial_input
        
        for agent in self.agents:
            self.logger.info(f"Executing {agent.name}...")
            
            try:
                result = await agent.process(current_input)
                results.append(result)
                
                if not result.success:
                    self.logger.error(f"Agent {agent.name} failed")
                    break
                
                # Pass result data to next agent
                current_input = result.data
                
            except Exception as e:
                self.logger.error(f"Agent {agent.name} raised exception: {e}")
                results.append(AgentResult(
                    agent_name=agent.name,
                    success=False,
                    data=None,
                    metadata={"error": str(e)}
                ))
                break
        
        return results
    
    def print_summary(self, results: list[AgentResult]):
        """Print summary of chain execution."""
        print("\n" + "="*60)
        print("Agent Chain Execution Summary")
        print("="*60)
        
        for result in results:
            status = "✓" if result.success else "✗"
            print(f"{status} {result.agent_name}")
            
            if result.metadata:
                for key, value in result.metadata.items():
                    print(f"  - {key}: {value}")
        
        print("="*60 + "\n")


async def main():
    """Main execution example."""
    
    # Sample code to process
    sample_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total
"""
    
    # Create agent chain
    chain = AgentChain([
        CodeReviewAgent(),
        RefactoringAgent(),
        TestWriterAgent(),
        DocumentationAgent()
    ])
    
    # Process code through the chain
    print("Processing code through agent chain...")
    print(f"Input:\n{sample_code}\n")
    
    results = await chain.process(sample_code)
    
    # Print summary
    chain.print_summary(results)
    
    # Access final result
    if results and results[-1].success:
        final_data = results[-1].data
        print("Final Output:")
        print(f"- Code reviewed and refactored")
        print(f"- {len(final_data['tests'])} tests generated")
        print(f"- Documentation created")


if __name__ == "__main__":
    asyncio.run(main())
