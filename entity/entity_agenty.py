import ollama
from langchain.agents import (
    AgentExecutor,
    create_tool_calling_agent,
    create_react_agent,
)
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from entity.tools import get_tools
import os


class EntityAgent:
    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.llm = OllamaLLM(model=self.model, base_url=os.getenv("OLLAMA_BASE_URL"))
        self.tools = get_tools()
        self.agent = self._create_agent()

    def _create_agent(self):
        # Use ReAct agent instead of tool calling agent
        prompt = PromptTemplate.from_template(
            """
    Answer the following questions as best you can. You have access to the following tools:

    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought: {agent_scratchpad}"""
        )

        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )

    async def process(self, message: str) -> str:
        try:
            result = await self.agent.ainvoke({"input": message})
            return result["output"]
        except Exception as e:
            return f"Error: {str(e)}"
