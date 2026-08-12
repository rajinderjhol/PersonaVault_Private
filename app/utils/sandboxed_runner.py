import json
import subprocess
import asyncio
import os

class SandboxedPluginRunner:
    def __init__(self, module_path: str, func_name: str):
        self.module_path = module_path
        self.func_name = func_name
        self.executor_path = os.path.join(os.path.dirname(__file__), "sandbox_executor.py")

    async def run(self, *args, **kwargs):
        payload = {
            "module": self.module_path,
            "function": self.func_name,
            "args": args,
            "kwargs": kwargs
        }
        
        # Run in a separate process
        process = await asyncio.create_subprocess_exec(
            "python3", self.executor_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate(input=json.dumps(payload).encode())
        
        if process.returncode != 0:
            raise Exception(f"Sandbox runner failed: {stderr.decode()}")
            
        result = json.loads(stdout.decode())
        if not result["success"]:
            raise Exception(f"Plugin execution failed: {result['error']}")
            
        return result["result"]
