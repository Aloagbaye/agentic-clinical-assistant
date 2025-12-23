# Workflow Engine

The workflow engine orchestrates the execution of agent workflows, managing state transitions, error handling, and progress tracking.

## Architecture

```
┌─────────────────┐
│  API Endpoint   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WorkflowExecutor│  ← Manages background tasks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WorkflowEngine  │  ← Orchestrates workflow steps
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Celery Tasks   │  ← Executes agent steps
└─────────────────┘
```

## Components

### WorkflowState

Tracks the complete state of a workflow execution:

- **Status**: Current workflow status (pending, running, completed, etc.)
- **Step Results**: Results from each workflow step
- **Progress**: Current step and completion status
- **Outputs**: Final answer, citations, errors

### WorkflowEngine

Orchestrates workflow execution:

1. **Initialization**: Sets up workflow state
2. **Execution**: Runs workflow steps sequentially
3. **State Management**: Tracks progress and results
4. **Error Handling**: Handles failures and rollback
5. **Finalization**: Updates database with final state

### WorkflowExecutor

Manages workflow execution in background:

- **Background Tasks**: Executes workflows asynchronously
- **State Tracking**: Maintains running workflows
- **Cancellation**: Supports workflow cancellation
- **State Retrieval**: Gets current workflow state

## Workflow Steps

### 1. Intake Agent

- **Purpose**: Classify request and assess risk
- **Input**: User request text
- **Output**: Request plan with type, risk, and required tools
- **Duration**: ~5-10 seconds

### 2. Retrieval Agent

- **Purpose**: Find relevant evidence
- **Input**: Request text + filters from intake
- **Output**: Evidence bundles with documents and scores
- **Duration**: ~10-30 seconds

### 3. Synthesis Agent

- **Purpose**: Generate draft answer
- **Input**: Request text + evidence
- **Output**: Draft answer with citations
- **Duration**: ~20-60 seconds

### 4. Verifier Agent

- **Purpose**: Verify safety and grounding
- **Input**: Draft answer
- **Output**: Verification result (pass/fail)
- **Duration**: ~5-15 seconds

## Usage

### Starting a Workflow

```python
from agentic_clinical_assistant.workflow.executor import get_executor
import uuid

executor = get_executor()
run_id = uuid.uuid4()

# Start workflow in background
await executor.execute_workflow(
    run_id=run_id,
    request_text="What is the policy for sepsis treatment?",
    user_id="doctor123"
)
```

### Getting Workflow State

```python
# Get current state
state = await executor.get_workflow_state(run_id)
print(f"Status: {state['status']}")
print(f"Progress: {state.get('steps_completed', 0)}/{state.get('total_steps', 4)}")
```

### Cancelling a Workflow

```python
# Cancel running workflow
cancelled = await executor.cancel_workflow(run_id)
if cancelled:
    print("Workflow cancelled")
```

### Direct Engine Usage

```python
from agentic_clinical_assistant.workflow.engine import WorkflowEngine
import uuid

run_id = uuid.uuid4()
engine = WorkflowEngine(run_id)

# Initialize
await engine.initialize(
    request_text="What is the policy for sepsis treatment?",
    user_id="doctor123"
)

# Execute
final_state = await engine.execute()

# Get state
current_state = await engine.get_state()
```

## State Transitions

```
PENDING → RUNNING → INTAKE → RETRIEVAL → SYNTHESIS → VERIFICATION → COMPLETED
                                                              ↓
                                                         ABSTAINED
                                                              ↓
                                                          FAILED
```

## Error Handling

The workflow engine handles errors at multiple levels:

1. **Step-Level**: Individual step failures are caught and logged
2. **Workflow-Level**: Workflow status updated to FAILED
3. **Database**: All errors logged to audit tables
4. **Rollback**: Partial state preserved for debugging

## Progress Tracking

Progress is tracked at multiple levels:

- **Workflow Status**: Overall workflow state
- **Current Step**: Which step is currently executing
- **Steps Completed**: Number of completed steps
- **Total Steps**: Total number of steps (4)

## Integration

### API Integration

The workflow executor is integrated with the API:

- `/agent/run`: Starts workflow execution
- `/agent/status/{run_id}`: Gets workflow state
- `/agent/cancel/{run_id}`: Cancels workflow

### Database Integration

All workflow state is persisted:

- **AgentRun**: Main run record
- **ToolCall**: Individual tool invocations
- **EvidenceRetrieval**: Evidence retrieval logs
- **GroundingVerification**: Verification results

## Testing

Run workflow tests:

```bash
pytest tests/test_workflow.py -v
```

## Next Steps

- Add workflow visualization
- Implement workflow retry logic
- Add workflow timeout handling
- Implement workflow prioritization

