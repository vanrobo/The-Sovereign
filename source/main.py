# Vanrobo © 2025

from dotenv import load_dotenv
import os
from google import genai
import json
import subprocess

#from this project
import content


class Ai:
    """
    This is the AI Class
    The Ai class automatically initialises the gemini AI, and gives it a function to generate outputs
    IT CONTAINS A PERMANENT INSTRUCTIONS CONTENT THAT THE AI WILL ALWAYS FOLLOW

    Generate()
    Allows the AI to generate outputs, returns the value, confined to using json using response_mime_Type, 
    also has option for modelgem [which allows you to specify the model]
    """
    PERMISSION_LEVELS = {
            'Baron': 1,      
            'Viscount': 2,   
            'Earl': 3,       
            'Marquess': 4,   
            'Duke': 5         
        }
    
    load_dotenv()

    def __init__(self,permission='Baron',instructions_content=content.AGENT_INSTRUCTIONS,):
        self.api_key = os.getenv("API_KEY")
        
        if not self.api_key:
            raise ValueError("API_KEY environment variable not found")
        
        self.instructions_content=instructions_content()
        self.client = None
    
        if permission not in self.PERMISSION_LEVELS:
            raise ValueError(f"Invalid Permission level: {permission}")
        
        self.permission = permission #  the main permission system, Baron -> Viscount -> Earl -> Marquess -> Duke
        self.step_outcomes = {}
        self.conversation_history = []
        self.session_memory = {}

        try:
            with open("history.json", "r") as f:
                data = json.load(f)
                self.conversation_history = data.get("conversation_history", [])
                self.step_outcomes = data.get("last_execution_outcomes", {})
        except (FileNotFoundError, json.JSONDecodeError):
            self.conversation_history = []
            self.step_outcomes = {}

    """
    Enter and Exit are used as the entire code should be in a with statement. 
    """

    def __enter__(self):
        print("\nInitializing AI Client...")
        self.client = genai.Client(api_key=self.api_key)


        return self # Return the object to be used inside the 'with' block

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("\nClosing AI Client resources...")
        print("Saving Data...")

        context_string = self._prepare_context_string()

        history_to_save = {
            "conversation_history": self.conversation_history,
            "last_execution_outcomes": self.step_outcomes
        }
        with open("history.json", "w") as f: # Use 'w' to overwrite
            json.dump(history_to_save, f, indent=2)

        self.client = None
        print("Client resources released.\n")
        print("Log")
        

    @staticmethod
    def past_history():
        try:
            with open("data.txt", "r") as file:
                history = file.read()
                return history
        except FileNotFoundError:
            print("  [WARNING] No past history found, continuing.\n")

    def generate(self, user_content=None):
        if user_content is None:
            user_content = "The User Has Entered No Content"

        context_string = self._prepare_context_string()

        full_prompt = self.instructions_content + context_string + user_content

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config={
                "response_mime_type": "application/json",
            }
        )
        return response.text
    
    def _prepare_context_string(self):
        """Formats history and outcomes into a string for the AI prompt."""
        if not self.conversation_history and not self.step_outcomes:
            return "" # Return empty string if there's no history

        context_parts = []
        # Format Session Memory
        if self.session_memory:
            context_parts.append("## In-Session Memory (from read_file)")
            for key, value in self.session_memory.items():
                context_parts.append(f"### Memory Key: '{key}'")
                context_parts.append(f"Content:\n---\n{value}\n---")
            context_parts.append("---")

        # Format conversation history
        if self.conversation_history:
            context_parts.append("## Conversation History")
            for entry in self.conversation_history:
                role = "User" if entry['role'] == 'user' else "Agent"
                context_parts.append(f"{role}: {entry['content']}")
            context_parts.append("---")

        # Format step outcomes from the last execution
        if self.step_outcomes:
            context_parts.append("## Previous Execution Outcomes")
            for step_num, outcome in self.step_outcomes.items():
                context_parts.append(f"Step {step_num}: {outcome.upper()}")
            context_parts.append("---")
            
        return str("\n".join(context_parts) + "\n")

    """
    Tools: 
    Write to File [to write to a file path]
    Read File [To read the file out]
    Execute Shell [to execute a command in the terminal]
    """

    def perform_write_file(self,file_path,content):
        """Writes content to a specified file."""
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  [SUCCESS] Wrote content to '{file_path}'")
            return True # Indicate success
        except Exception as e:
            print(f"  [FAILURE] Could not write to file '{file_path}': {e}")
            return False # Indicate failure      
    
    def perform_read_file(self, file_path, memory_key):
        """Reads a file and prints its content."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            print(f"  [SUCCESS] Read file: '{file_path}'")
            print(f"  [CONTENT STORED] Storing content with key: '{memory_key}'")
            self.session_memory[memory_key] = content

            return True # Indicate success
        
        except FileNotFoundError:
            print(f"  [FAILURE] File not found: '{file_path}'")
            return False # Indicate failure
        
        except Exception as e:
            print(f"  [FAILURE] Could not read file '{file_path}': {e}")
            return False # Indicate failure

    def perform_execute_shell(self,command):
        """Executes a shell command."""
        try:
            # Using subprocess.run is safer and more modern
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(f"  [SUCCESS] Executed command: '{command}'")
            if result.stdout:
                print(f"  [STDOUT]:\n{result.stdout.strip()}")

            # Also check for stderr, as some successful commands write warnings here
            if result.stderr:
                print(f"  [STDERR]:\n{result.stderr.strip()}")

            return True # Indicate success
        except subprocess.CalledProcessError as e:
            print(f"  [FAILURE] Command '{command}' failed with exit code {e.returncode}")
            print(f"  [STDERR]: {e.stderr}")
            return False # Indicate failure

    def parse_output(self,AIjson):

        '''Parse output, for readability'''
        
        try:
            for step in AIjson['steps']:
                # Safely get all the data from the current step 
                step_num = step.get('step_number', 'N/A')
                command_call = step.get('command_call', {})
                function_call = command_call.get('function', 'N/A')
                arguments = command_call.get('args', {})
                print(f"Step {step_num}:")
                display_command = "N/A"
                if function_call == 'execute_shell':
                    display_command = arguments.get('command', 'No command specified.')
                elif function_call == 'write_file':
                    display_command = f"Write to file '{arguments.get('file_path', 'N/A')}'"

                print(f"  └── Command: `{display_command}`")

                # Check for and print the conditional logic 
                if 'condition' in step:
                    condition = step['condition']
                    check_step = condition.get('check_step', '?')
                    required_outcome = condition.get('on_outcome', '?')
                    print(f"      └── Condition: Depends on step {check_step} outcome being '{required_outcome}'")
                    print(f"          └── Full Command Call Details:")
                    print(f"              └── Function: {function_call}")
                    print(f"              └── Arguments: {arguments}")
                else:
                    print("      └── Condition: None (This step always runs)")

            print("--------------------------\n")
            print()
            has_shell_commands = False
            for step in AIjson['steps']:
                # Check if the function is 'execute_shell' before trying to print a command
                if step.get('command_call', {}).get('function') == 'execute_shell':
                    command = step['command_call'].get('args', {}).get('command')
                    if command:
                        print(command)
                        has_shell_commands = True

            if not has_shell_commands:
                print("(No raw shell commands in this plan)")
            print("-------------------------------------\n")

        except json.JSONDecodeError:
            print("\n--- ERROR: The AI did not return valid JSON. ---")
        except KeyError as e:
            print(f"\n--- ERROR: The AI's JSON was missing a required key: {e} ---")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")


    def add_to_history(self,role,content):
        '''Helper method to add entries to the history'''                                             
        self.conversation_history.append({"role": role, "content": content})
    
    def get_full_history(self):
        '''Returns full conversational history'''
        return self.conversation_history
    
    def clear_memory(self):
        '''Clears conversation history and Step Outcomes'''
        self.conversation_history = []
        self.step_outcomes = {}
        self.session_memory = {}
        print("Agent Memory Cleared")

    def _resolve_memory_references(self, args_dict):
            """
            Recursively searches through a dictionary of arguments and replaces 
            'memory://<key>' placeholders with content from self.session_memory.
            """
            resolved_args = {}
            for key, value in args_dict.items():
                if isinstance(value, str) and value.startswith("memory://"):
                    memory_key = value[9:] # Get the key name after "memory://"
                    # Replace the placeholder with actual content, default to an empty string if not found
                    resolved_args[key] = self.session_memory.get(memory_key, "")
                    print(f"    [MEMORY] Resolved '{value}' with content from session memory.")
                else:
                    resolved_args[key] = value
            return resolved_args
    
    def execute_commands(self, ai_json, permission=True):
            """Executes all the steps in the parsed AI JSON object."""
            try:
                # Check for permission if required
                if permission:
                    option = input("Execute the plan? [Y/n] ").lower().strip()
                    if option in ("n", "no"):
                        print("Execution cancelled by user.")
                        return False  # Exit the function if user denies

                # If permission is granted (or not required), proceed with execution
                self.step_outcomes = {}  # Clear outcomes from previous runs
                print("\nExecuting Plan...")

                # Directly use the ai_json dictionary passed into the function
                for step in ai_json.get('steps', []):
                    step_num = step.get('step_number')
                    condition = step.get('condition', {})

                    if step_num is None:
                        print("  [WARNING] Skipping a step because it has no 'step_number'.")
                        continue

                    # Check if the step is conditional
                    should_execute = True  # Assume the step should run unless a condition fails
                    if condition:
                        check_step_num = condition.get('check_step')
                        required_outcome = condition.get('on_outcome')
                        previous_outcome = self.step_outcomes.get(check_step_num)

                        # Check if the required outcome was met in the previous step
                        if previous_outcome != required_outcome:
                            print(f"  [SKIPPED] Step {step_num} because condition was not met (Required: '{required_outcome}'",f"Actual for Step {check_step_num}: '{previous_outcome}').")
                            should_execute = False # Do not execute this step
                    if not should_execute:
                        continue # Move to the next step in the loop

                    # Get command details and execute
                    print(f"  [RUNNING] Step {step_num}...")    
                    command_call = step.get('command_call', {})
                    command_func_name = command_call.get('function')
                    command_args = self._resolve_memory_references(command_call.get('args', {}))
                    execution_success = False

                    if command_func_name == "execute_shell":
                        command = command_args.get('command')
                        if command:
                            # Use 'self' to call methods within the same class
                            execution_success = self.perform_execute_shell(command)

                    elif command_func_name == "write_file":
                        file_path = command_args.get('file_path')
                        file_content = command_args.get('content')
                        if file_path and file_content is not None:
                            execution_success = self.perform_write_file(file_path, file_content)
                        else:
                            print(f"  [FAILURE] Step {step_num} is missing 'file_path' or 'content'.")


                    elif command_func_name == "read_file":
                        file_path = command_args.get('file_path')
                        memory_key = command_args.get('memory_key')
                        if file_path and memory_key:
                            execution_success = self.perform_read_file(file_path,memory_key)
                        else:
                            print(f"  [FAILURE] Step {step_num} is missing 'file_path'.")

                    else:
                        print(f"  [FAILURE] Unknown function '{command_func_name}' in step {step_num}.")
                        continue # Skip to the next step

                    # Record the outcome for conditional logic
                    if execution_success:
                        self.step_outcomes[step_num] = "success"
                    else:
                        self.step_outcomes[step_num] = "failure"

                print("\nExecution Finished.")
                return True

            except KeyError as e:
                print(f"\n  --- [ERROR]: The AI's JSON was missing a required key during execution: {e} ---")
                return False
            except Exception as e:
                print(f"\n  [ERROR]: An unexpected error occurred during execution: {e}")
                return False

    def parse_and_execute(self,input_json,permission=True):
        '''
        Parse and then Execute, mostly for debugging
        '''
        self.parse_output(input_json)
        self.execute_commands(input_json,permission=permission)

"""
This is just temporary, command line only, user input based output testing for a basic baron AI agent.
It outputs the following:-

1. Main Thought Process
2. All the steps, wtih reasoning and the command
3. All the steps  with command and conditions and function calls
4. All the steps without any extra formatting, to copy paste into a terminal to test. 

"""

EXIT_PHRASES = ['exit', 'quit', 'bye', 'end', 'stop', 'close','die','kys','exit program', 'quit program', 'i want to exit', 'i want to quit', 'goodbye', 'end program']


if __name__ == "__main__":
    '''
    run a one time only, chat with the Ai.  
    '''
    with Ai(permission="Baron") as orchestrator:
        print("AI Initialised and Ready.")
        while True:
            try:
                choice = input("\nwhat would you like to do?: ")
                if choice in ['quit','exit','leave','bye','q','qexit'] :
                    break
                
                orchestrator.add_to_history('user', choice)
                out = orchestrator.generate(choice)
                
                with open("temp.json", 'w') as f:
                    f.write(out)
                    
                AIjson = json.loads(out)
                orchestrator.add_to_history('agent', out)
                orchestrator.parse_and_execute(AIjson)
                

            except json.JSONDecodeError:
                print("\n--- ERROR: The AI did not return valid JSON. ---")
            except Exception as e:
                print(f"An error occurred in the main loop: {e}")
            except KeyboardInterrupt:
                break
