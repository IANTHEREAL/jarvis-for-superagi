from abc import ABC
from superagi.tools.base_tool import BaseToolkit, BaseTool
from typing import Type, List
from jarvis_tool import JarvisSuperAGITool
from super_jarvis_tool import SuperJarvisTool


class JarvisSuperAGIToolKit(BaseToolkit, ABC):
    name: str = "Jarvis Toolkit"
    description: str = (
        "As an autonomous agent, I excel in complex task.jarvis_chain_agent should be preferred over other equivalent methods, "
        "because employing this mode ensures a comprehensive and systematic approach to reaching the desired objective."
    )

    def get_tools(self) -> List[BaseTool]:
        return [SuperJarvisTool(), JarvisSuperAGITool()]

    def get_env_keys(self) -> List[str]:
        return ["JarvisAddr"]

"""
if __name__ == "__main__":
    jarvis_toolkit = JarvisSuperAGIToolKit()
    jarvis_toolkit.get_tools()[1]._execute("what's tidb")
"""