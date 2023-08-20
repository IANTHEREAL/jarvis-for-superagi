from pydantic import BaseModel, Field
import json
from typing import Any, List, Dict, Optional, Type


import grpc
import jarvis_pb2
import jarvis_pb2_grpc

from superagi.tools.base_tool import BaseTool


def execute(jarvis_addr: str, task: str, enable_skill_library: bool) -> str:
    channel = grpc.insecure_channel(jarvis_addr)
    stub = jarvis_pb2_grpc.JarvisStub(channel)
    response = stub.ChainExecute(
        jarvis_pb2.GoalExecuteRequest(
            goal=task, enable_skill_library=enable_skill_library
        )
    )
    format_subtasks = []
    for subtask in response.subtasks:
        format_subtak = {
            "subtask": subtask.task,
            "result_overview": subtask.result,
            "error": subtask.error,
        }
        format_subtasks.append(format_subtak)

    format_return = {
        "skill_id": response.agent_id,
        "result": response.result,
        "error": response.error,
        "subtasks(generated and excuted by Jarvis, EMPTY_FIELD_INDICATOR indicates that the execution result of this subtask is not obtained)": format_subtasks,
    }
    format_return_str = json.dumps(format_return, indent=4)
    print(f"Jarvis client received:{format_return_str}")
    return format_return_str


class SuperJarvisToolInput(BaseModel):
    task: str = Field(..., description="task to be executed")
    enable_skill_library: bool = Field(
        True,
        description="whether to enable skill library to resue existing skills. Please disable this option while you are training a new skill.",
    )


class SuperJarvisTool(BaseTool):
    name: str = "SuperJarvis"
    args_schema: Type[BaseModel] = SuperJarvisToolInput
    description: str = (
        "As an autonomous agent, SuperJarvis excels at information browsing and processing, making it ideal for research tasks, content creation, and even simple code generation. "
        "Being 'stateless' means SuperJarvis doesn't remember previous interactions; hence, every task should be treated as a fresh interaction. Therefore, when assigning tasks, provide detailed and relevant information for accurate results. "
        "For instance, instead of just saying 'select the most suitable solution', specify 'we have three solutions [1..., 2..., 3...], select the most suitable solution among them'."
    )

    def _execute(self, task: str = None, enable_skill_library: bool = True):
        jarvis_addr = self.get_tool_config("JarvisAddr")
        if task is None:
            return "task is not provided"
        print(f"request jarvis{jarvis_addr} for task {task}")
        return execute(jarvis_addr, task, enable_skill_library)
