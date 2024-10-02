from abc import ABC, abstractmethod
from typing import AsyncIterator, List
from langchain.schema import HumanMessage, AIMessage
from langfuse.decorators import observe, langfuse_context
import logging
from langfuse.openai import AsyncOpenAI
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

class BaseModelInterface(ABC):
    @abstractmethod
    async def generate_stream(self, messages: List[HumanMessage | AIMessage]) -> AsyncIterator[str]:
        pass

    @abstractmethod
    async def generate(self, messages: List[HumanMessage | AIMessage]) -> str:
        pass

class BaseModel(BaseModelInterface):
    def __init__(self, model_name: str):
        self.model_name = model_name

    def handle_error(self, e: Exception) -> str:
        error_message = f"Error: {str(e)}"
        logger.error(f"Error in {self.__class__.__name__}: {error_message}", exc_info=True)
        return error_message

    def log_response(self, response: str):
        logger.info(f"Complete {self.__class__.__name__} response: {response[:100]}...")  # Log first 100 chars

class OpenAIModel(BaseModel):
    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name)
        self.client = AsyncOpenAI(api_key=api_key)

    @observe(as_type="generation")
    async def generate_stream(self, messages: List[HumanMessage | AIMessage]) -> AsyncIterator[str]:
        async def stream_generator():
            try:
                openai_messages = [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} for m in messages]
                langfuse_context.update_current_observation(
                    input=openai_messages,
                    model=self.model_name,
                    metadata={"stream": True}
                )

                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=openai_messages,
                    stream=True
                )

                total_tokens = 0
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                        total_tokens += 1

                langfuse_context.update_current_observation(
                    usage={
                        "total_tokens": total_tokens
                    }
                )

            except Exception as e:
                error_message = self.handle_error(e)
                yield error_message
        
        return stream_generator()

    @observe(as_type="generation")
    async def generate(self, messages: List[HumanMessage | AIMessage]) -> str:
        try:
            openai_messages = [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} for m in messages]
            langfuse_context.update_current_observation(
                input=openai_messages,
                model=self.model_name,
                metadata={"stream": False}
            )

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
            )
            complete_response = response.choices[0].message.content
            self.log_response(complete_response)

            langfuse_context.update_current_observation(
                output=complete_response,
                usage={
                    "total_tokens": response.usage.total_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            )

            return complete_response
        except Exception as e:
            error_message = self.handle_error(e)
            langfuse_context.update_current_observation(
                output=error_message,
                level="ERROR"
            )
            return error_message

class AnthropicModel(BaseModel):
    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name)
        self.client = AsyncAnthropic(api_key=api_key)

    @observe(as_type="generation")
    async def generate_stream(self, messages: List[HumanMessage | AIMessage]) -> AsyncIterator[str]:
        async def stream_generator():
            try:
                anthropic_messages = [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} for m in messages]
                langfuse_context.update_current_observation(
                    input=anthropic_messages,
                    model=self.model_name,
                    metadata={"stream": True}
                )

                response = await self.client.messages.create(
                    model=self.model_name,
                    messages=anthropic_messages,
                    max_tokens=1000,
                    stream=True
                )

                total_tokens = 0
                async for chunk in response:
                    if chunk.delta.text:
                        yield chunk.delta.text
                        total_tokens += 1

                langfuse_context.update_current_observation(
                    usage={
                        "total_tokens": total_tokens
                    }
                )

            except Exception as e:
                error_message = self.handle_error(e)
                yield error_message
        
        return stream_generator()

    @observe(as_type="generation")
    async def generate(self, messages: List[HumanMessage | AIMessage]) -> str:
        try:
            anthropic_messages = [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} for m in messages]
            langfuse_context.update_current_observation(
                input=anthropic_messages,
                model=self.model_name,
                metadata={"stream": False}
            )

            response = await self.client.messages.create(
                model=self.model_name,
                messages=anthropic_messages,
                max_tokens=1000,
            )

            complete_response = response.content[0].text
            self.log_response(complete_response)

            langfuse_context.update_current_observation(
                output=complete_response,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            )

            return complete_response
        except Exception as e:
            error_message = self.handle_error(e)
            langfuse_context.update_current_observation(
                output=error_message,
                level="ERROR"
            )
            return error_message

class ModelFactory:
    @staticmethod
    def create_model(provider: str, model_name: str, api_key: str) -> BaseModelInterface:
        if provider.lower() == "openai":
            return OpenAIModel(model_name, api_key)
        elif provider.lower() == "anthropic":
            return AnthropicModel(model_name, api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
