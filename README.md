# Workflow Engine - A Simplified LangGraph Implementation

A minimal workflow/graph engine built with Python and FastAPI, similar to LangGraph. This system allows you to define sequences of steps (nodes), connect them with edges, maintain shared state, and execute workflows end-to-end via REST APIs.

## Features

### Core Workflow Engine
- **Nodes**: Python functions that read and modify shared state
- **State**: Dictionary-based state that flows through the workflow
- **Edges**: Define which node runs after which
- **Branching**: Conditional routing based on state values
- **Looping**: Support for loops that run until a condition is met

### Tool Registry
- Simple dictionary-based registry for Python functions
- Tools can be registered and called by nodes
- Built-in code review tools included

### FastAPI Endpoints
- `POST /graph/create` - Create a new workflow graph
- `POST /graph/run` - Execute a workflow with initial state
- `GET /graph/state/{run_id}` - Get the current state of a workflow run
- `GET /tools` - List all available tools

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the FastAPI server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI) is available at `http://localhost:8000/docs`

## Example: Code Review Mini-Agent

The project includes a pre-built Code Review workflow that demonstrates the engine's capabilities:

1. **Extract functions** from Python code
2. **Check complexity** (cyclomatic complexity)
3. **Detect basic issues** (long functions, missing docstrings, etc.)
4. **Suggest improvements** based on findings
5. **Loop** until quality_score >= threshold

### Running the Example

The `code_review_agent` graph is automatically created when the server starts. You can run it with:

```bash
curl -X POST "http://localhost:8000/graph/run" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "code_review_agent",
    "initial_state": {
      "code": "def hello(): print(\"world\")\ndef goodbye(): pass",
      "quality_threshold": 80,
      "max_iterations": 5
    }
  }'
```

## API Usage

### Create a Graph

```bash
POST /graph/create
{
  "graph_id": "my_graph",
  "nodes": {
    "node1": {
      "name": "First Node",
      "func": "extract_functions",
      "type": "standard"
    },
    "node2": {
      "name": "Second Node",
      "func": "check_complexity",
      "type": "standard"
    }
  },
  "edges": {
    "node1": "node2"
  }
}
```

### Run a Graph

```bash
POST /graph/run
{
  "graph_id": "my_graph",
  "initial_state": {
    "code": "your code here"
  }
}
```

### Get Run State

```bash
GET /graph/state/{run_id}
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── engine.py          # Core workflow engine
│   ├── tools.py            # Tool registry and code review tools
│   ├── api.py              # FastAPI endpoints
│   └── workflows.py        # Example workflows
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## How the Workflow Engine Works

1. **Graph Creation**: Define nodes (functions) and edges (connections)
2. **State Management**: Each workflow run has a unique state that flows through nodes
3. **Node Execution**: Nodes receive state, execute their function, and can modify state
4. **Routing**: After execution, the engine follows edges to the next node
5. **Conditional Logic**: Conditional nodes can route to different nodes based on state
6. **Looping**: Loop nodes check a condition and can loop back to previous nodes

## What the Engine Supports

- ✅ Standard nodes (sequential execution)
- ✅ Conditional routing (branching)
- ✅ Looping (repeat until condition)
- ✅ Shared state across nodes
- ✅ Execution logging
- ✅ Tool registry system
- ✅ Error handling
- ✅ Run state tracking

## What I Would Improve with More Time

1. **Persistence**: Currently graphs and runs are stored in memory. I would add:
   - SQLite/PostgreSQL database for persistence
   - Graph versioning
   - Run history and analytics

2. **Async Support**: 
   - Async node execution for I/O-bound operations
   - Background task execution
   - WebSocket streaming for real-time logs

3. **Advanced Features**:
   - Parallel node execution
   - Sub-graphs (nested workflows)
   - Retry logic for failed nodes
   - Timeout handling
   - State checkpoints

4. **Developer Experience**:
   - Visual graph editor
   - Better error messages and debugging
   - Graph validation before execution
   - Type checking for state

5. **Testing**:
   - Comprehensive unit tests
   - Integration tests
   - Performance benchmarks

6. **Documentation**:
   - More examples
   - API usage guides
   - Architecture documentation

## Code Quality

The codebase focuses on:
- **Clarity**: Clean, readable Python code
- **Structure**: Well-organized modules with clear responsibilities
- **Correctness**: Proper error handling and edge case management
- **Simplicity**: No over-engineering, just what's needed

## License

This is a coding assignment submission.

