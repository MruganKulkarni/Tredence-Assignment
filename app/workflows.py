"""
Example Workflows - Code Review Mini-Agent
"""
from app.engine import WorkflowEngine, NodeType
from app.tools import registry


def create_code_review_workflow(engine: WorkflowEngine) -> str:
    """
    Create the Code Review Mini-Agent workflow:
    1. Extract functions
    2. Check complexity
    3. Detect basic issues
    4. Suggest improvements
    5. Loop until quality_score >= threshold
    """
    
    # Define loop condition function
    def should_continue_loop(state):
        """Check if we should continue the loop"""
        quality_score = state.get("quality_score", 0)
        threshold = state.get("quality_threshold", 80)
        iteration = state.get("loop_iteration", 0)
        max_iterations = state.get("max_iterations", 5)
        
        # Continue if quality is below threshold and we haven't exceeded max iterations
        should_continue = quality_score < threshold and iteration < max_iterations
        
        if should_continue:
            # Update iteration count only if we're continuing
            state.update(loop_iteration=iteration + 1)
            state.log("loop", f"Loop continuing: iteration={iteration + 1}, quality_score={quality_score}, threshold={threshold}")
        else:
            state.log("loop", f"Loop terminating: quality_score={quality_score}, threshold={threshold}, iteration={iteration}")
        
        return should_continue
    
    # Define nodes
    nodes = {
        "extract": {
            "name": "Extract Functions",
            "func": "extract_functions",
            "type": "standard"
        },
        "complexity": {
            "name": "Check Complexity",
            "func": "check_complexity",
            "type": "standard"
        },
        "detect": {
            "name": "Detect Issues",
            "func": "detect_issues",
            "type": "standard"
        },
        "suggest": {
            "name": "Suggest Improvements",
            "func": "suggest_improvements",
            "type": "standard"
        },
        "loop_check": {
            "name": "Check Quality Loop",
            "func": lambda state: state.log("loop_check", "Checking if quality threshold is met"),
            "type": "loop",
            "loop_condition_func": should_continue_loop
        }
    }
    
    # Define edges (workflow sequence)
    edges = {
        "extract": "complexity",
        "complexity": "detect",
        "detect": "suggest",
        "suggest": "loop_check",
        "loop_check": "extract"  # Loop back to extract if condition is met
    }
    
    graph_id = "code_review_agent"
    engine.create_graph(graph_id, nodes, edges)
    
    return graph_id


def get_example_code() -> str:
    """Get example Python code for testing"""
    return '''
def calculate_total(items, discount=0, tax_rate=0.1):
    """Calculate total with discount and tax"""
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    discounted = subtotal * (1 - discount)
    total = discounted * (1 + tax_rate)
    return total

def process_order(order_id, customer_info, items, payment_method):
    """Process a customer order"""
    # TODO: Add validation
    total = calculate_total(items)
    if payment_method == 'credit':
        charge_credit_card(customer_info, total)
    elif payment_method == 'paypal':
        charge_paypal(customer_info, total)
    else:
        raise ValueError("Invalid payment method")
    
    print(f"Order {order_id} processed")
    return {"order_id": order_id, "total": total}

def charge_credit_card(customer, amount):
    """Charge credit card"""
    # FIXME: Implement actual charging
    pass

def charge_paypal(customer, amount):
    """Charge PayPal"""
    pass
'''

