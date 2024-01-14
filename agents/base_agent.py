from pathlib import Path
import inspect


class BaseAgent:
    @property
    def prompts_directory(self) -> Path:
        # Get the file path of the current class's module
        module_path = Path(inspect.getfile(self.__class__)).resolve()
        prompts_dir = module_path.parent / 'prompts'
        return prompts_dir
