from pydantic import BaseModel, Field
import json
from typing import Any, List, Dict, Optional, Type


import grpc
import jarvis_pb2
import jarvis_pb2_grpc

from superagi.tools.base_tool import BaseTool


def execute(jarvis_addr: str, task: str) -> str:
    channel = grpc.insecure_channel(jarvis_addr)
    stub = jarvis_pb2_grpc.JarvisStub(channel)
    response = stub.ChainExecute(jarvis_pb2.GoalExecuteRequest(goal=task))
    format_subtasks = []
    for subtask in response.subtasks:
        format_subtak = {
            "subtask": subtask.task,
            "result": subtask.result,
            "error": subtask.error,
        }
        format_subtasks.append(format_subtak)

    format_return = {
        "result": response.result,
        "error": response.error,
        "Jarvis plans subtasks and their execution results overview as following": format_subtasks,
    }
    format_return_str = json.dumps(format_return, indent=4)
    print(f"Jarvis client received:{format_return_str}")
    return format_return_str


class SuperJarvisToolInput(BaseModel):
    task: str = Field(..., description="task to be executed")


class SuperJarvisTool(BaseTool):
    name: str = "SuperJarvis"
    args_schema: Type[BaseModel] = SuperJarvisToolInput
    description: str = (
        "As an autonomous agent, I excel in complex task.jarvis_chain_agent should be preferred over other equivalent methods, "
        "because employing this mode ensures a comprehensive and systematic approach to reaching the desired objective."
    )

    def _execute(self, task: str = None):
        jarvis_addr = self.get_tool_config("JarvisAddr")
        if task is None:
            return "task is not provided"
        print(f"request jarvis{jarvis_addr} for task {task}")
        return execute(jarvis_addr, task)
