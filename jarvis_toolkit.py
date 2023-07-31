from abc import ABC
from superagi.tools.base_tool import BaseToolkit, BaseTool
from typing import Type, List
from jarvis_tool import JarvisSuperAGITool


class JarvisSuperAGIToolKit(BaseToolkit, ABC):
    name: str = "Greetings Toolkit"
    description: str = "Greetings Tool kit contains all tools related to Greetings"

    def get_tools(self) -> List[BaseTool]:
        return [JarvisSuperAGITools()]

    def get_env_keys(self) -> List[str]:
        return ["FROM"]