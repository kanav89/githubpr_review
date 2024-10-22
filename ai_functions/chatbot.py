import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Sequence, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

def create_chatbot(query: str, context: str) -> Dict[str, Any]:
    load_dotenv()

    model = ChatAnthropic(model="claude-3-5-sonnet-20240620")

    class State(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        context: str

    workflow = StateGraph(state_schema=State)

    def call_model(state: State):
        chain = prompt | model
        response = chain.invoke(state)
        return {"messages": [response]}

    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)

    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a helpful code assistant that can answer questions and help with tasks. Use this {context} from the pull request to answer the user's question",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])

    config = {"configurable": {"thread_id": "abc123"}}

    input_messages = [HumanMessage(content=query)]
    output = app.invoke({"messages": input_messages, "context": context}, config)
    return output["messages"][-1].content

