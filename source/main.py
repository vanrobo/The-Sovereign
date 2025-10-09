# Vanrobo © 2025

from dotenv import load_dotenv
import os
from google import genai
import json
import subprocess

#from this project
import content

"""
This is the AI Class
The Ai class automatically initialises the gemini AI, and gives it a function to generate outputs
IT CONTAINS A PERMANENT INSTRUCTIONS CONTENT THAT THE AI WILL ALWAYS FOLLOW

Generate()
Allows the AI to generate outputs, returns the value, confined to using json using response_mime_Type, 
also has option for modelgem [which allows you to specify the model]
"""

class Ai:

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
        
        self.instructions_content=instructions_content
        self.client = None
    
        if permission not in self.PERMISSION_LEVELS:
            raise ValueError(f"Invalid Permission level: {permission}")
        
        self.permission = permission #  the main permission system, Baron -> Viscount -> Earl -> Marquess -> Duke
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

        self.client = None
        print("Client resources released.\n")

# Corrected generate method
    def generate(self, user_content=None, modelgem="gemini-1.5-flash"):
        if user_content is None:
            user_content = "The User Has Entered No Content"

        # Get the latest context string right when it's needed
        context_string = self._prepare_context_string()

        # Safely combine all parts of the prompt
        full_prompt = self.instructions_content + context_string + user_content

        model = genai.GenerativeModel(modelgem)
        response = model.generate_content(
            contents=full_prompt,
            generation_config={
                "response_mime_type": "application/json",
            }
        )
        return response.text
    
    def _prepare_context_string(self):
        """Formats history and outcomes into a string for the AI prompt."""
        if not self.conversation_history and not self.step_outcomes:
            return "" # Return empty string if there's no history

        context_parts = []
        
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
    
    def perform_read_file(self, file_path):
        """Reads a file and prints its content."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            print(f"  [SUCCESS] Read file: '{file_path}'")
            print(f"  [CONTENT]:\n---\n{content}\n---")
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
    


    def parse_output(self,input_json):

        '''Parse output, for readability'''
        
        AIjson = json.loads(input_json)

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
        print("Agent Memory Cleared")

    def execute_commands(self,input_json,permission=True):
        '''execute all the steps in the json'''

        try:
            if permission:
                option=input("execute the plan [Y/n] ").lower().strip()
                if option == "n" or option == "no":
                    return False
            else:
                self.step_outcomes={}
                print("Executing: ")
                for step in AIjson.get('steps',[]):

                    condition = step.get('condition',{})
                    step_num = step.get('step_number', 'N/A')
                    
                    if step_num is None:
                        print("Skipping step with no step_number.")
                        continue

                    # check condition

                    if condition:
                        check_step_num = condition.get('check_step')
                        on_outcome = condition.get('on_outcome')
                        previous_outcome = self.step_outcomes.get(check_step_num)

                        if previous_outcome != on_outcome:
                            print(f"Skip {step_num} due to unmet conditions ")
                            continue
                    
                    # get command function and arguments

                    command_call = step.get('command_call')
                    commandfunc = command_call.get('function')
                    commandargs = command_call.get('args',{})
                    execution_success = False

                    if commandfunc == "execute_shell":
                        command = commandargs.get('command',"")
                        if command:
                            execution_success = orchestrator.perform_execute_shell(command)

                    elif commandfunc == "write_file":
                        file_path = commandargs.get('file_path')
                        file_content = commandargs.get('content')
                        if file_path and file_content:
                            execution_success = orchestrator.perform_write_file(file_path,file_content)

                    elif commandfunc == "read_file":
                        file_path = commandargs.get('file_path')
                        if file_path:
                            execution_success = orchestrator.perform_read_file(file_path)
                    else:
                        continue
                    
                    if execution_success:
                        self.step_outcomes[step_num] = "success"
                        print(f"  └── Step {step_num} outcome: success")
                    else:
                        self.step_outcomes[step_num] = "failure"
                        print(f"  └── Step {step_num} outcome: failure")

                return True
            
        except json.JSONDecodeError:
            print("\n--- ERROR: The AI did not return valid JSON. ---")
            return False
        except KeyError as e:
            print(f"\n--- ERROR: The AI's JSON was missing a required key: {e} ---")
            return False
        except Exception as e:
            print(f"\nAn unexpected error occurred during execution: {e}")
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
    └──[this does not have the conditional and functional calling, beware]
"""


if __name__ == "__main__":
    while True:
        try:
            x=input("what would you like to do?: ")
            with Ai(permission="Baron") as orchestrator: #just the prompt from content file and the ai class
                print("Initialised\n\n") 
                out=orchestrator.generate(x) # generates the output and returns a json
                AIjson=json.loads(out) # loading the json

                with open("temp.json",'w') as f:
                    f.write(out)

                orchestrator.parse_and_execute(AIjson)

        except Exception as e:
            print(e)

