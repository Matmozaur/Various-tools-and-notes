# Agent Configuration Examples

This directory contains example configuration files for different types of AI agents.

## Configuration Files

- **code_reviewer.yaml** - Configuration for code review agents
- **documentation_agent.yaml** - Configuration for documentation generation agents
- **refactor_agent.yaml** - Configuration for code refactoring agents
- **test_writer.yaml** - Configuration for test generation agents

## Configuration Schema

All agent configuration files follow this general schema:

```yaml
agent:
  name: string              # Unique identifier for the agent
  type: string              # Agent type (review, documentation, refactor, test)
  model: string             # AI model to use
  version: string           # Configuration version
  
  parameters:
    temperature: float      # Sampling temperature (0.0-1.0)
    max_tokens: int         # Maximum tokens in response
    top_p: float           # Nucleus sampling parameter
    
  capabilities:             # List of agent capabilities
    - capability_1
    - capability_2
    
  constraints:
    max_iterations: int    # Maximum processing iterations
    timeout_seconds: int   # Timeout for operations
    
  prompts:
    system: string         # Path to system prompt
    templates:             # List of template paths
      - template_path
      
  tools:                   # Available tools for the agent
    - name: string
      enabled: boolean
```

## Usage

### Python

```python
import yaml

def load_agent_config(config_name: str) -> dict:
    with open(f"agent_configs/{config_name}.yaml") as f:
        return yaml.safe_load(f)

# Usage
config = load_agent_config("code_reviewer")
agent = CodeReviewAgent(config['agent'])
```

### Environment Variables

Configuration files support environment variable substitution:

```yaml
agent:
  api_key: ${ANTHROPIC_API_KEY}
  model: ${AGENT_MODEL:-claude-sonnet-4.5}  # with default
```

## Customization

To create a custom configuration:

1. Copy an existing configuration file
2. Modify the parameters for your use case
3. Update the prompts section to reference your custom prompts
4. Adjust capabilities and constraints as needed

## Validation

Validate your configuration using the schema:

```python
from jsonschema import validate
import yaml

with open("schema.json") as f:
    schema = json.load(f)
    
with open("agent_configs/custom_agent.yaml") as f:
    config = yaml.safe_load(f)
    
validate(instance=config, schema=schema)
```

## Best Practices

1. **Version your configs**: Include a version field for tracking changes
2. **Use defaults**: Provide sensible defaults for optional parameters
3. **Document changes**: Add comments explaining configuration choices
4. **Test configurations**: Validate configs before deployment
5. **Environment-specific**: Use separate configs for dev/staging/prod

## Examples

See individual configuration files for specific examples of each agent type.
