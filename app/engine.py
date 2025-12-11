"""
Core Workflow Engine - A simplified LangGraph-like system
"""
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class NodeType(Enum):
    """Types of nodes in the workflow"""
    STANDARD = "standard"
    CONDITIONAL = "conditional"
    LOOP = "loop"


@dataclass
class Node:
    """Represents a node in the workflow graph"""
    id: str
    name: str
    func: Callable
    node_type: NodeType = NodeType.STANDARD
    condition_func: Optional[Callable] = None  # For conditional routing
    loop_condition_func: Optional[Callable] = None  # For loop termination


@dataclass
class WorkflowState:
    """Shared state that flows through the workflow"""
    data: Dict[str, Any] = field(default_factory=dict)
    current_node: Optional[str] = None
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    completed: bool = False
    error: Optional[str] = None

    def update(self, **kwargs):
        """Update state data"""
        self.data.update(kwargs)
    
    def get(self, key: str, default=None):
        """Get value from state data"""
        return self.data.get(key, default)
    
    def log(self, node_id: str, message: str, result: Any = None):
        """Add entry to execution log"""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "node_id": node_id,
            "message": message,
            "result": result
        })


class WorkflowEngine:
    """Main workflow engine that executes graphs"""
    
    def __init__(self):
        self.graphs: Dict[str, 'Graph'] = {}
        self.runs: Dict[str, WorkflowState] = {}
    
    def create_graph(self, graph_id: str, nodes: Dict[str, Dict], edges: Dict[str, str]) -> str:
        """Create a new graph from node and edge definitions"""
        graph = Graph(graph_id)
        
        # Create nodes
        for node_id, node_def in nodes.items():
            func_name = node_def.get("func")
            if not func_name:
                raise ValueError(f"Node {node_id} must have a 'func' field")
            
            node_type = NodeType(node_def.get("type", "standard"))
            condition_func = node_def.get("condition_func")
            loop_condition_func = node_def.get("loop_condition_func")
            
            graph.add_node(
                node_id=node_id,
                name=node_def.get("name", node_id),
                func=func_name,  # Will be resolved later
                node_type=node_type,
                condition_func=condition_func,
                loop_condition_func=loop_condition_func
            )
        
        # Add edges
        for from_node, to_node in edges.items():
            graph.add_edge(from_node, to_node)
        
        self.graphs[graph_id] = graph
        return graph_id
    
    def run_graph(
        self, 
        graph_id: str, 
        initial_state: Dict[str, Any],
        start_node: Optional[str] = None,
        tool_registry: Optional['ToolRegistry'] = None
    ) -> WorkflowState:
        """Execute a graph with initial state"""
        if graph_id not in self.graphs:
            raise ValueError(f"Graph {graph_id} not found")
        
        graph = self.graphs[graph_id]
        state = WorkflowState(data=initial_state.copy())
        self.runs[state.run_id] = state
        
        # Resolve function references and set tool registry
        graph.resolve_functions(tool_registry)
        
        # Determine start node
        current_node_id = start_node or graph.get_start_node()
        if not current_node_id:
            state.error = "No start node found"
            state.completed = True
            return state
        
        state.log("engine", f"Starting workflow from node: {current_node_id}")
        
        visited_nodes = set()
        max_iterations = 1000  # Prevent infinite loops
        iteration = 0
        
        try:
            while current_node_id and iteration < max_iterations:
                iteration += 1
                
                if current_node_id not in graph.nodes:
                    state.error = f"Node {current_node_id} not found in graph"
                    break
                
                node = graph.nodes[current_node_id]
                state.current_node = current_node_id
                
                # Execute node first
                state.log(node.id, f"Executing node: {node.name}")
                result = node.func(state)
                
                if result:
                    state.log(node.id, f"Node completed", result)
                
                # Handle loop nodes - check condition after executing
                if node.node_type == NodeType.LOOP and node.loop_condition_func:
                    should_continue = node.loop_condition_func(state)
                    if should_continue:
                        # Loop condition is True, continue looping (follow edge which loops back)
                        state.log(node.id, "Loop condition met, continuing loop")
                        current_node_id = graph.get_next_node(current_node_id, state)
                    else:
                        # Loop condition is False, exit loop (don't follow the loop edge)
                        state.log(node.id, "Loop condition not met, exiting loop")
                        current_node_id = None  # End workflow when loop exits
                    continue
                
                # Handle conditional routing
                if node.node_type == NodeType.CONDITIONAL and node.condition_func:
                    next_node = node.condition_func(state)
                    if next_node and next_node in graph.nodes:
                        current_node_id = next_node
                    else:
                        current_node_id = graph.get_next_node(current_node_id, state)
                else:
                    current_node_id = graph.get_next_node(current_node_id, state)
                
                # Check for completion
                if not current_node_id:
                    state.log("engine", "Workflow completed")
                    state.completed = True
                    break
                
                # Prevent infinite loops (simple check)
                if current_node_id in visited_nodes and node.node_type != NodeType.LOOP:
                    visited_nodes.clear()
                visited_nodes.add(current_node_id)
            
            if iteration >= max_iterations:
                state.error = "Maximum iterations reached"
                state.completed = True
            
        except Exception as e:
            state.error = str(e)
            state.completed = True
            state.log("engine", f"Error: {str(e)}")
        
        return state
    
    def get_run_state(self, run_id: str) -> Optional[WorkflowState]:
        """Get the state of a workflow run"""
        return self.runs.get(run_id)


class Graph:
    """Represents a workflow graph with nodes and edges"""
    
    def __init__(self, graph_id: str):
        self.graph_id = graph_id
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, str] = {}  # from_node -> to_node
        self.tool_registry: Optional['ToolRegistry'] = None
    
    def add_node(
        self,
        node_id: str,
        name: str,
        func: Any,  # Can be string (tool name) or callable
        node_type: NodeType = NodeType.STANDARD,
        condition_func: Optional[Callable] = None,
        loop_condition_func: Optional[Callable] = None
    ):
        """Add a node to the graph"""
        self.nodes[node_id] = Node(
            id=node_id,
            name=name,
            func=func,  # Will be resolved later
            node_type=node_type,
            condition_func=condition_func,
            loop_condition_func=loop_condition_func
        )
    
    def add_edge(self, from_node: str, to_node: str):
        """Add an edge between nodes"""
        if from_node not in self.nodes:
            raise ValueError(f"Source node {from_node} not found")
        if to_node not in self.nodes:
            raise ValueError(f"Target node {to_node} not found")
        self.edges[from_node] = to_node
    
    def resolve_functions(self, tool_registry: Optional['ToolRegistry']):
        """Resolve function references to actual callables"""
        self.tool_registry = tool_registry
        for node in self.nodes.values():
            if isinstance(node.func, str):
                # It's a tool name, resolve it
                if tool_registry and tool_registry.has_tool(node.func):
                    node.func = tool_registry.get_tool(node.func)
                else:
                    raise ValueError(f"Tool '{node.func}' not found in registry")
            elif not callable(node.func):
                raise ValueError(f"Node {node.id} has invalid function")
    
    def get_start_node(self) -> Optional[str]:
        """Find the start node (node with no incoming edges)"""
        if not self.nodes:
            return None
        
        # Find nodes that are not targets of any edge
        target_nodes = set(self.edges.values())
        start_nodes = [nid for nid in self.nodes.keys() if nid not in target_nodes]
        
        if start_nodes:
            return start_nodes[0]
        
        # If all nodes are targets, return the first node
        return list(self.nodes.keys())[0] if self.nodes else None
    
    def get_next_node(self, current_node: str, state: WorkflowState) -> Optional[str]:
        """Get the next node based on edges"""
        return self.edges.get(current_node)

