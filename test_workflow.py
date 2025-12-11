#!/usr/bin/env python3
"""
Simple test script to demonstrate the workflow engine
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_code_review():
    """Test the code review workflow"""
    
    print_section("Testing Code Review Workflow")
    
    # Sample code with some issues
    test_code = """
def calculate_total(items, discount=0, tax_rate=0.1):
    \"\"\"Calculate total with discount and tax\"\"\"
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    discounted = subtotal * (1 - discount)
    total = discounted * (1 + tax_rate)
    return total

def process_order(order_id, customer_info, items, payment_method):
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
    # FIXME: Implement actual charging
    pass
"""
    
    print("\n📝 Input Code:")
    print(test_code[:200] + "...")
    
    # Run the workflow
    print("\n🚀 Running workflow...")
    response = requests.post(
        f"{BASE_URL}/graph/run",
        json={
            "graph_id": "code_review_agent",
            "initial_state": {
                "code": test_code,
                "quality_threshold": 80,
                "max_iterations": 3
            }
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    
    # Display results
    print_section("Results")
    
    state = result['final_state']
    
    print(f"\n✅ Workflow Completed: {result['completed']}")
    print(f"📊 Run ID: {result['run_id']}")
    
    print(f"\n📈 Code Quality Metrics:")
    print(f"   Quality Score: {state.get('quality_score', 'N/A')}/100")
    print(f"   Functions Found: {state.get('functions_count', 0)}")
    print(f"   Average Complexity: {state.get('avg_complexity', 0):.1f}")
    print(f"   Max Complexity: {state.get('max_complexity', 0)}")
    print(f"   Issues Detected: {state.get('issues_count', 0)}")
    
    print(f"\n🔍 Functions Analyzed:")
    for func in state.get('functions', [])[:5]:  # Show first 5
        print(f"   • {func['name']}: complexity={func.get('complexity', 'N/A')}, "
              f"args={func.get('args_count', 0)}, "
              f"docstring={'✓' if func.get('has_docstring') else '✗'}")
    
    print(f"\n⚠️  Issues Found:")
    for issue in state.get('issues', [])[:5]:  # Show first 5
        print(f"   • {issue.get('message', 'Unknown issue')}")
    
    print(f"\n💡 Suggestions:")
    for suggestion in state.get('suggestions', []):
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(suggestion.get('priority', 'low'), "⚪")
        print(f"   {priority_emoji} {suggestion.get('message', 'No message')}")
    
    print(f"\n📋 Execution Summary:")
    print(f"   Total Steps: {len(result['execution_log'])}")
    print(f"   Loop Iterations: {state.get('loop_iteration', 0)}")
    
    # Show workflow flow
    print(f"\n🔄 Workflow Flow:")
    nodes_executed = []
    for log in result['execution_log']:
        node_id = log['node_id']
        if node_id not in ['engine', 'loop'] and node_id not in nodes_executed:
            nodes_executed.append(node_id)
    
    print(f"   {' → '.join(nodes_executed)}")
    
    if result.get('error'):
        print(f"\n❌ Error: {result['error']}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  WORKFLOW ENGINE - TEST SCRIPT")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        print("✓ Server is running")
    except requests.exceptions.RequestException:
        print("❌ Server is not running!")
        print("   Please start it with: python main.py")
        exit(1)
    
    # Run test
    test_code_review()
    
    print("\n" + "=" * 60)
    print("  Test Complete!")
    print("=" * 60 + "\n")

