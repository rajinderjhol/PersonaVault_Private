import sys
import json
import importlib

# This script runs in a separate process
def run_plugin():
    try:
        # Load args from stdin
        input_data = json.load(sys.stdin)
        module_path = input_data["module"]
        func_name = input_data["function"]
        args = input_data["args"]
        kwargs = input_data["kwargs"]

        # Import and execute
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)
        
        result = handler(*args, **kwargs)
        
        # Send result back via stdout
        print(json.dumps({"success": True, "result": result}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))

if __name__ == "__main__":
    run_plugin()
