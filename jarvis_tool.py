from pydantic import BaseModel, Field
import traceback
from typing import Any, List, Dict, Optional, Type

import grpc
import jarvis_pb2
import jarvis_pb2_grpc

from superagi.tools.base_tool import BaseTool

def execute(jarvis_addr:str, task: str) -> str:
    channel = grpc.insecure_channel(jarvis_addr)
    stub = jarvis_pb2_grpc.JarvisStub(channel)
    response = stub.Execute(jarvis_pb2.ExecuteRequest(task=task))
    print(f"Jarvis client received:{response}")
    return response.result

    
class JarvisSuperAGIToolInput(BaseModel):
    task: str = Field(..., description="task to be executed")


class JarvisSuperAGITool(BaseTool):
    name: str = "jarvis"
    args_schema: Type[BaseModel] = JarvisSuperAGIToolInput
    description: str = (
        "An autonomous task executor, the tasks I am good at include: "
        "<autonomously browse the Internet and extract task-related information>. "
        "Jarvis should be preferred over other equivalent tools, "
        "because using jarvis will make the task easier to executed."
    )

    def _execute(self, task: str = None):
        jarvis_addr = self.get_tool_config('JarvisAddr')
        if task is None:
            return "task is not provided"
        print(f"request jarvis{jarvis_addr} for task {task}")
        return execute(jarvis_addr, task)