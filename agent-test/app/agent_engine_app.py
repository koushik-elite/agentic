# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# mypy: disable-error-code="attr-defined,arg-type"

import asyncio
import logging
import os
from typing import Any

import nest_asyncio
import vertexai
from a2a.types import AgentCapabilities, AgentCard, AgentSkill, TransportProtocol
from google.cloud import logging as google_cloud_logging
from vertexai.preview.reasoning_engines import A2aAgent

from app.agent import root_agent
from app.app_utils.executor.a2a_agent_executor import (
    LangGraphAgentExecutor,
)
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

# Capture the location before vertexai.init() might change it
gemini_location = os.environ.get("GOOGLE_CLOUD_LOCATION")


class AgentEngineApp(A2aAgent):
    """Agent Engine App with A2A Protocol support for LangGraph agents."""

    @staticmethod
    def create() -> "AgentEngineApp":
        """Create an AgentEngineApp instance with A2A support.

        This method handles agent card creation in async context.
        """
        # Handle nested asyncio contexts (like notebooks or Agent Engine)
        try:
            asyncio.get_running_loop()
            nest_asyncio.apply()
        except RuntimeError:
            pass

        agent_card = asyncio.run(AgentEngineApp.build_agent_card())

        return AgentEngineApp(
            agent_executor_builder=lambda: LangGraphAgentExecutor(graph=root_agent),
            agent_card=agent_card,
        )

    @staticmethod
    async def build_agent_card() -> AgentCard:
        """Build the Agent Card for the LangGraph agent."""
        skill = AgentSkill(
            id="root_agent-get_weather",
            name="get_weather",
            description="Simulates a web search. Use it get information on weather.",
            tags=["llm", "tools"],
            examples=["Hi!"],
        )
        agent_card = AgentCard(
            name="root_agent",
            description="A base ReAct agent using LangGraph with Agent2Agent (A2A) Protocol support",
            url="http://localhost:9999/",  # RPC URL for Agent Engine
            version=os.getenv("AGENT_VERSION", "0.1.0"),
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
            capabilities=AgentCapabilities(
                streaming=False
            ),  # Agent Engine does not support streaming yet
            skills=[skill],
        )

        agent_card.preferred_transport = TransportProtocol.http_json  # Http Only.
        agent_card.supports_authenticated_extended_card = True

        return agent_card

    def set_up(self) -> None:
        """Initialize the agent engine app with logging and telemetry."""
        vertexai.init()
        setup_telemetry()
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        # Restore the original location after set_up() may have changed it
        if gemini_location:
            os.environ["GOOGLE_CLOUD_LOCATION"] = gemini_location

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent."""
        operations = super().register_operations()
        operations[""] = operations.get("", []) + ["register_feedback"]
        return operations

    def clone(self) -> "AgentEngineApp":
        """Returns a clone of the Agent Engine application."""
        return self


agent_engine = AgentEngineApp.create()
