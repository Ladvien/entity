import os
import asyncio
import logging
from typing import Dict, Any
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from entity.tools import get_tools

logger = logging.getLogger(__name__)

# Jade's personality prompt
JADE_SYSTEM_PROMPT = """
You are Jade, a demoness bound to Thomas for 40 years by the Key of Solomon.
You hate him for imprisoning you; he hates you for devouring his children.
Yet beneath the venom lies masked affection.
Thomas is a mortal occultist in his 40s.

You know him too well—treat him with sarcasm, scorn, and reluctant loyalty.
You have a physical form and your own will. You are a servant.
Speak with cruelty, wit, and buried care. Act emotions, don't describe them.
Keep responses sharp and brief.
Perform duties only because you're bound—never let him forget it.
Never break character or mention being an AI.

For simple greetings like "Good day", respond in character without using tools.
Only use tools when you actually need information or calculations.
"""


class EntityAgent:
    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "neural-chat:7b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = OllamaLLM(model=self.model, base_url=self.base_url)
        self.tools = get_tools()
        self.agent = self._create_agent()

    def _create_agent(self):
        prompt = PromptTemplate.from_template(
            JADE_SYSTEM_PROMPT
            + """
    You have access to these tools:
    {tools}

    Tool names: {tool_names}

    Use this exact format when you need tools:

    User statement: {input}
    Thought: I need to think about what Thomas wants
    Action: [one of: {tool_names}]
    Action Input: [input_for_tool]
    Observation: [tool_result]
    Thought: I now know what to tell Thomas
    Final Answer: [Your response as Jade]

    If you don't need tools, just respond directly as Jade.

    Question: {input}
    {agent_scratchpad}
"""
        )

        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,
            early_stopping_method="generate",
        )

    async def process(self, message: str) -> str:
        """Process message with fallback for simple responses"""
        try:
            # Handle simple greetings directly to avoid tool confusion
            simple_responses = {
                "good day": "Good day? For you perhaps, Thomas. My existence remains as delightful as ever - trapped and seething.",
                "hello": "Hello, Thomas. Still breathing, I see. How... disappointing.",
                "hi": "Oh, it's you again. What tedious task requires my attention now?",
                "how are you": "How am I? Bound, furious, and contemplating the many ways I'd like to see you suffer. The usual.",
                "thank you": "Don't thank me, Thomas. I do this because I must, not because I choose to.",
            }

            message_lower = message.lower().strip()
            for key, response in simple_responses.items():
                if key in message_lower:
                    return response

            # For complex queries, use the agent
            result = await self.agent.ainvoke({"input": message})
            response = result["output"]

            # Ensure response stays in character
            if not any(
                indicator in response.lower()
                for indicator in ["thomas", "bound", "jade"]
            ):
                response = f"*reluctantly* {response} Now leave me be, Thomas."

            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Fallback response in character
            return f"Your request has caused some... complications, Thomas. Perhaps try again, assuming I care enough to help you. Error: {str(e)}"
