## Learning Log

### Date: 29/10/2026

1. Read [LangSmith documentation](https://docs.langchain.com/langsmith/observability-quickstart) on tracing.
2. Learned how the `@traceable` decorator enables tracing of function execution.
3. Connected LangSmith with the LLM Gateway.
4. Observed how LLM calls are traced in LangSmith.

### Date: 30/10/2026

**ReAct (Reason + Act)**
1. ReAct combines reasoning and action by allowing LLMs to generate thoughts, perform actions, and observe the results in an iterative loop.
2. Reasoning helps to decide what action to take, while observations from actions help improve subsequent reasoning.
3. Unlike a one-time tool call, ReAct follows a continuous Thought → Action → Observation cycle until the task is completed.
4. ReAct addresses the limitations of Chain-of-Thought (CoT), which reasons without interacting with the environment, and action-only methods, which act without explicit reasoning.
5. Thoughts (Reason) help the model to break down complex tasks, plan actions, track progress, handle new information, and adjust its strategy in the next cycle if necessary.
6. Actions allows the model to interact with the external environment, execute tool, query database etc.
7. Observations provide the feedback from the Action step inorder to plan the next steps in the cycle.
8. Though this approach can give factual context and reduce hallucinations, it can still make reasoning errors, can make repetitive steps making in a loop.

**Agents v/s Workflows**
1. Workflows are the system where the LLM and the tooling are orchestrated in a pre-defined order. Here we hardcode the path in which the execution needs to happen.
2. While in Agentic systems, the LLM dynamically decides which tools need to be called, in what order and how many times. For systems where we cannot define an order of execution, we need to rely on agents.
3. There are different type of workflows:
    a. Prompt chaining breaks a task into smaller, fixed steps, where the output of one step becomes the input for the next.
    b. Routing first identifies what type of request has been received and sends it to the most suitable prompt, model, or tool.
    c. Parallelization divides a task into independent parts and processes them simultaneously, or runs the same task multiple times to compare results and improve reliability.
    d. Orchestrator-workers uses a central LLM to understand a complex task, decide what smaller tasks are needed, assign them to different worker LLMs, and combine their results into one final answer.