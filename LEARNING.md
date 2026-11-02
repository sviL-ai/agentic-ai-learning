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

### Date: 02/11/2026

1. State: It is a collection or record of the conversation, API calls, intermediate results throughout the execution of a task in a conversation. It consists of user's original goal, the current progress of the task execution, tool invoking and the output from them, intermediate analysis etc.
2. Tools: These are the functions, APIs, or other databases which are used to execute or fetch information beyond an LLM's (or Agents) external knowledge.
3. Memory: Memory is the ability of an agent to store, recall and use that information so that the agent can use it for better decision making in the present and future. If memory doesn't exist, every interation with the LLM in an agentic system will be an individual conversation. There are 2 types of memory; short-term and long-term. Short-term memory contains the context of current session which is required only to finish the current task. While long term memory holds the context for much longer period. It generally holds information like generic instructions, user preferences etc which can be useful for many sessions.
4. Control flow: It is a mechanism which decides, at each step, what happens given the current state and who or what decides that; code or model. It is different from workflow, which is having a control over the execution path. But here, we cannot pre-define the execution order, but can limit the boundary for the system to work.
5. Human-in-the-loop: It integrates the human intervention into agentic system for human judgement, approval etc. While agentic system can make decisons and execute functions, certain high-stakes decision like data deletion, money payment, sending out emails require human approval.
6. Multi agents: Systems which involve the collaboration of multiple agents to complete a task or solve a problem. Here the state and memory can be shared between agents in a multi-agent system, but they don't have to be necessarily. It depends on the system architectural design.