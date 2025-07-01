# Agno Cooking Agent 🍝

A lightweight, high-performance cooking agent built with the Agno framework that can extract recipe information from natural language and generate detailed cooking instructions.

## Features

- **Fast Agent Processing**: Uses Agno's ultra-fast agent instantiation (~2μs per agent)
- **Low Memory Footprint**: Minimal memory usage (~3.75 KiB per agent)
- **Natural Language Processing**: Extracts dish names, serving sizes, and file paths from user input
- **Recipe Generation**: Creates detailed, step-by-step cooking instructions
- **File Management**: Automatically saves recipes to specified files
- **Observability**: Integrated with Maxim for logging and monitoring
- **Structured Output**: Uses Pydantic models for consistent data handling

## Architecture

The cooking agent consists of two specialized agents:

1. **Extraction Agent**: Parses user input to extract:
   - Dish name
   - Number of people to serve
   - Output file name (optional)

2. **Chef Agent**: Generates detailed recipes including:
   - Ingredient lists with quantities
   - Step-by-step cooking instructions
   - Cooking time and difficulty level
   - Special tips and variations

## Installation

1. Install dependencies:
```bash
pip install -e .
```

2. Set up environment variables in `.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
MAXIM_API_KEY=your_maxim_api_key_here  # Optional for logging
MAXIM_BASE_URL=your_maxim_base_url     # Optional for logging
MAXIM_LOG_REPO_ID=your_repo_id         # Optional for logging
```

## Usage

### Basic Usage

```python
from agent import cooking_team

# Process a cooking request
result = cooking_team.process_request(
    "I want a recipe for Spaghetti Carbonara to serve 4 people save to carbonara.md"
)

print(f"Generated recipe for: {result['extraction']['dish_name']}")
print(f"Serves: {result['extraction']['number_served']} people")
print(f"Status: {result['status']}")
```

### Run the Test Script

```bash
python test_agent.py
```

### Run the Main Agent

```bash
python agent.py
```

## Example Interactions

### Input:
```
"I want a recipe for Chicken Tikka Masala for 6 people save to tikka_masala.md"
```

### Output:
- **Extraction**: `{"dish_name": "Chicken Tikka Masala", "number_served": 6, "file_name": "tikka_masala.md"}`
- **Recipe**: Complete recipe with ingredients and instructions
- **File**: Recipe saved to `tikka_masala.md`

## Performance Comparison

| Framework | Agent Instantiation | Memory Usage | Performance |
|-----------|-------------------|--------------|-------------|
| Agno      | ~2μs              | ~3.75 KiB    | ⚡ Ultra-fast |
| CrewAI    | ~20ms             | ~137 KiB     | 🐌 Slower    |

*Agno is ~10,000x faster and uses ~50x less memory than traditional frameworks*

## Key Benefits of Agno

1. **Blazing Fast**: Ultra-fast agent instantiation and processing
2. **Memory Efficient**: Minimal memory footprint for scalable deployments
3. **Model Agnostic**: Works with any OpenAI-compatible model
4. **Native Multimodal**: Built-in support for text, images, audio, and video
5. **Built-in Observability**: Real-time monitoring and debugging
6. **Structured Output**: Consistent data handling with Pydantic models

## File Structure

```
cooking-agent/
├── agent.py              # Main Agno cooking agent
├── test_agent.py         # Test script
├── pyproject.toml        # Dependencies
├── README.md            # Documentation
└── .env                 # Environment variables
```

## Customization

### Adding New Tools

```python
from agno.tools import tool

@tool(show_result=True)
def nutrition_calculator(ingredients: str) -> str:
    """Calculate nutritional information for ingredients."""
    # Your implementation here
    return "Nutritional information..."

# Add to chef agent
chef_agent.tools.append(nutrition_calculator)
```

### Modifying Agent Instructions

```python
chef_agent.instructions = [
    "You are a health-conscious chef",
    "Focus on nutritious, balanced meals",
    "Include calorie counts and dietary information",
    "Suggest healthy substitutions"
]
```

## Monitoring and Logging

The agent includes built-in integration with Maxim for:
- Real-time agent monitoring
- Performance tracking
- Error logging
- Session management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test_agent.py`
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the [Agno documentation](https://docs.agno.com/)
- Review the test cases in `test_agent.py`
- Examine the agent implementation in `agent.py`

---

*Built with ❤️ using the Agno framework*
