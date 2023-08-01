import ast
import glob
import os
import uuid
import logging
from datetime import datetime
from pydantic import BaseModel, Field
import traceback
from typing import Any, List, Dict, Optional, Type
import yaml

from superagi.tools.base_tool import BaseTool

from smartgpt import instruction
from smartgpt import jvm
from smartgpt import gpt
from smartgpt.compiler import Compiler

# BASE_MODEL = gpt.GPT_3_5_TURBO_16K
BASE_MODEL = gpt.GPT_4
EMPTY_FIELD_INDICATOR = "EMPTY_FIELD_INDICATOR"

# Logging file name and line number
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)

class TaskInfo(BaseModel):
    task_num: int
    task: str
    result: str
    metadata: dict


class Executor:
    """
    Use jarvis translator to generate instruction and execute instruction
    """

    def __call__(
        self,
        task: str,
        dependent_task_outputs: List[TaskInfo],
        goal: str,
        skip_gen: bool = False,
        subdir: Optional[str] = None,
        task_num: Optional[int] = None,
    ) -> TaskInfo | None:
        # skip_gen and subdir are used for testing purpose
        current_workdir = os.getcwd()
        if subdir:
            new_subdir = os.path.join(current_workdir, subdir)
        else:
            unique_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            new_subdir = os.path.join(current_workdir, f"{unique_id}-{timestamp}")

        os.makedirs(new_subdir, exist_ok=True)
        os.chdir(new_subdir)

        try:
            if skip_gen:
                instrs = self.load_instructions()
            else:
                instrs = self.gen_instructions(
                    task, goal, dependent_task_outputs, task_num
                )
            result = self.execute_instructions(instrs)
        except Exception as e:
            logging.error(f"Error executing task {task}: {e}")
            # os.chdir(current_workdir)
            print(traceback.format_exc())
            raise e

        os.chdir(current_workdir)
        return result

    def load_instructions(self) -> Dict:
        instructions = {}
        for file_name in glob.glob("*.yaml"):
            with open(file_name, "r") as f:
                saved = f.read()
            task_num = int(file_name.split(".")[0])
            instructions[task_num] = yaml.safe_load(saved)
        return instructions

    def gen_instructions(
        self,
        task: str,
        goal: str,
        dependent_tasks: List[TaskInfo],
        task_num: Optional[int] = None,
    ) -> Dict:
        compiler = Compiler(BASE_MODEL)
        previous_outcomes = []
        computed_task_num = 1

        for dt in dependent_tasks:
            previous_outcomes.append(
                {
                    "task_num": dt.task_num,
                    "task": dt.task,
                    "outcome": dt.metadata.get("instruction_outcome", ""),
                }
            )
            if dt.task_num >= computed_task_num:
                computed_task_num = dt.task_num + 1

        if task_num is None:
            task_num = computed_task_num

        hints = [
            f"The current task is a part of the gloal goal: {goal}",
        ]

        generated_instrs = compiler.compile_task(
            task_num, task, hints, previous_outcomes
        )
        return {task_num: generated_instrs}

    def execute_instructions(self, instructions: Dict) -> TaskInfo | None:
        jvm.load_kv_store()
        interpreter = instruction.JVMInterpreter()
        last_result = None

        for task_num, instrs in instructions.items():
            # Execute the generated instructions
            interpreter.reset()
            logging.info(f"Executing task {task_num}: {instrs}")
            interpreter.run(instrs["instructions"], instrs["task"])
            last_result = TaskInfo(
                task_num=task_num,
                task=instrs["task"],
                result=EMPTY_FIELD_INDICATOR,
                metadata={
                    "instruction_outcome": instrs["overall_outcome"],
                },
            )

        if last_result is not None:
            result = self.get_task_result(last_result.metadata["instruction_outcome"])
            if result is not None and result != "None":
                last_result.result = result

        return last_result

    def get_task_result(self, overall_outcome: str, return_key: bool = False):
        sys_prompt = (
            "You're a helpful assistant, please output the keys (in python list type) where the overall task output result is stored according to the task output description.\n"
            "Examples:\n"
            "User: The data under the key 'AI_trends' has been analyzed and 1-3 projects that have shown significant trends or growth have been selected. The selected projects have been stored in the database under the key 'selected_projects.seq2.list'.\n"
            "Assistant: ['selected_projects.seq2.list']\n"
            "User: The trending AI projects information from the last 28 days has been extracted. The descriptions of the selected projects for the tweet can be retrieved with keys like 'project_description_<idx>.seq4.str'.\n"
            "Assistant: ['project_description_<idx>.seq4.str']\n"
            "User: The top 3 projects based on their advancements and growth rate have been selected. The projects can be retrieved with keys 'top_project_0.seq19.str', 'top_project_1.seq19.str', and 'top_project_2.seq19.str'. These projects will be featured in the tweet for their recent advancements and high growth rate.\n"
            "Assistant: ['top_project_0.seq19.str', 'top_project_1.seq19.str', 'top_project_2.seq19.str']\n"
        )
        user_prompt = overall_outcome

        resp = gpt.complete(
            prompt=user_prompt, model=gpt.GPT_3_5_TURBO_16K, system_prompt=sys_prompt
        )

        # for testing purpose
        if return_key:
            return resp

        keys = ast.literal_eval(resp)
        result = None
        for key in keys:
            if "<idx>" in resp:
                key_prefix = key.split("<idx>")[0]
                res = jvm.eval(
                    f'jvm.eval(jvm.list_values_with_key_prefix("{key_prefix}"))'
                )
            else:
                res = jvm.eval(f'jvm.eval(jvm.get("{key}"))')
            if res is not None and res != "None":
                if result is None:
                    result = str(res)
                else:
                    result += f"\n{key}:{res}"

        return result

class JarvisTools:
    def __init__(self):
        self.execute = Executor()
        self.previous_tasks = []
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.subdir = f"{unique_id}-{timestamp}"
        print(f"initial jarvis agent under subdir: {self.subdir}")

    @property
    def name(self):
        return "jarvis"

    @property
    def description(self):
        return (
            "An autonomous agent, the tasks I am good at include: "
            "<autonomously browse the Internet and extract task-related information>. "
            "smart agent should be preferred over other equivalent tools, "
            "because using jarvis will make the task easier to executed."
        )

    def exec(self, tool_input: str) -> str:
        while True:
            task_info = self.execute(
                tool_input, self.previous_tasks, tool_input, subdir=self.subdir
            )
            assert task_info is not None, "last_task_info is None"
            if task_info.result != EMPTY_FIELD_INDICATOR:
                break
            print(f"Retring.... cause of empty result of task: {task_info}")

        self.previous_tasks.append(task_info)
        return task_info.result
    
class JarvisSuperAGIToolInput(BaseModel):
    task: str = Field(..., description="task to be executed")


class JarvisSuperAGITool(BaseTool):
    name: str = "jarvis"
    args_schema: Type[BaseModel] = JarvisSuperAGIToolInput
    description: str = (
        "An autonomous executor, the tasks I am good at include: "
        "<autonomously browse the Internet and extract task-related information>. "
        "Jarvis should be preferred over other equivalent tools, "
        "because using jarvis will make the task easier to executed."
    )
    agent = JarvisTools()

    def _execute(self, task: str = None):
        return self.agent.exec(task)