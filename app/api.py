"""
FastAPI endpoints for the workflow engine
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from app.engine import WorkflowEngine, NodeType
from app.tools import registry

app = FastAPI(title="Workflow Engine API", version="1.0.0")

# Global engine instance (will be initialized in main.py)
from app.engine import WorkflowEngine
engine: WorkflowEngine = None


# Request/Response Models
class NodeDefinition(BaseModel):
    name: str
    func: str
    type: str = "standard"  # standard, conditional, loop
    condition_func: Optional[str] = None
    loop_condition_func: Optional[str] = None


class CreateGraphRequest(BaseModel):
    graph_id: Optional[str] = None
    nodes: Dict[str, NodeDefinition]
    edges: Dict[str, str]


class CreateGraphResponse(BaseModel):
    graph_id: str
    message: str


class RunGraphRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any]
    start_node: Optional[str] = None


class ExecutionLogEntry(BaseModel):
    timestamp: str
    node_id: str
    message: str
    result: Any = None


class RunGraphResponse(BaseModel):
    run_id: str
    final_state: Dict[str, Any]
    execution_log: List[ExecutionLogEntry]
    completed: bool
    error: Optional[str] = None


class StateResponse(BaseModel):
    run_id: str
    current_node: Optional[str]
    state: Dict[str, Any]
    execution_log: List[ExecutionLogEntry]
    completed: bool
    error: Optional[str] = None


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Workflow Engine API",
        "version": "1.0.0",
        "endpoints": {
            "create_graph": "POST /graph/create",
            "run_graph": "POST /graph/run",
            "get_state": "GET /graph/state/{run_id}",
            "list_tools": "GET /tools"
        }
    }


@app.post("/graph/create", response_model=CreateGraphResponse)
def create_graph(request: CreateGraphRequest):
    """Create a new workflow graph"""
    if engine is None:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        graph_id = request.graph_id or f"graph_{len(engine.graphs) + 1}"
        
        # Convert Pydantic models to dict
        nodes_dict = {}
        for node_id, node_def in request.nodes.items():
            nodes_dict[node_id] = {
                "name": node_def.name,
                "func": node_def.func,
                "type": node_def.type,
                "condition_func": node_def.condition_func,
                "loop_condition_func": node_def.loop_condition_func
            }
        
        engine.create_graph(graph_id, nodes_dict, request.edges)
        
        return CreateGraphResponse(
            graph_id=graph_id,
            message=f"Graph '{graph_id}' created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/graph/run", response_model=RunGraphResponse)
def run_graph(request: RunGraphRequest):
    """Run a workflow graph"""
    if engine is None:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        state = engine.run_graph(
            graph_id=request.graph_id,
            initial_state=request.initial_state,
            start_node=request.start_node,
            tool_registry=registry
        )
        
        return RunGraphResponse(
            run_id=state.run_id,
            final_state=state.data,
            execution_log=[
                ExecutionLogEntry(**entry) for entry in state.execution_log
            ],
            completed=state.completed,
            error=state.error
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/state/{run_id}", response_model=StateResponse)
def get_state(run_id: str):
    """Get the current state of a workflow run"""
    if engine is None:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    state = engine.get_run_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    return StateResponse(
        run_id=state.run_id,
        current_node=state.current_node,
        state=state.data,
        execution_log=[
            ExecutionLogEntry(**entry) for entry in state.execution_log
        ],
        completed=state.completed,
        error=state.error
    )


@app.get("/tools")
def list_tools():
    """List all available tools"""
    return {
        "tools": registry.list_tools(),
        "count": len(registry.tools)
    }

