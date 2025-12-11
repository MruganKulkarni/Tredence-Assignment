
import uvicorn
from app.api import app
import app.api as api_module
from app.workflows import create_code_review_workflow
from app.engine import WorkflowEngine

api_module.engine = WorkflowEngine()

create_code_review_workflow(api_module.engine)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

