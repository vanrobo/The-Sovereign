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
    
    def __init__(self,instructions_content,permission):
        self.api_key = os.getenv("API_KEY")
        
        if not self.api_key:
            raise ValueError("API_KEY environment variable not found")
        
        self.instructions_content=instructions_content
        self.client = None
    
        if permission not in self.PERMISSION_LEVELS:
            raise ValueError(f"Invalid Permission level: {permission}")
        self.permission = permission #  the main permission system, Baron -> Viscount -> Earl -> Marquess -> Duke

    """
    Enter and Exit are used as the entire code should be in a with statement. 
    """

    def __enter__(self):
        print("Initializing AI Client...")
        self.client = genai.Client(api_key=self.api_key)
        return self # Return the object to be used inside the 'with' block

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Closing AI Client resources...")

        self.client = None
        print("Client resources released.")

    def generate(self, content=None, modelgem="gemini-2.5-flash"):
        if content is None:
            content="The User Has Entered No Content"
        response = self.client.models.generate_content(
            model=modelgem,
            contents=self.instructions_content+content,
            config={
                "response_mime_type": "application/json",
            }
        )
        return response.text

    """
    Tools: 
    Execute Shell [to execute a command in the terminal]
    Write to File [to write to a file path]
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
        
    def perform_execute_shell(self,command):
        """Executes a shell command."""
        try:
            # Using subprocess.run is safer and more modern
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(f"  [SUCCESS] Executed command: '{command}'")
            # You could print result.stdout if you wanted to see the command's output
            return True # Indicate success
        except subprocess.CalledProcessError as e:
            print(f"  [FAILURE] Command '{command}' failed with exit code {e.returncode}")
            print(f"  [STDERR]: {e.stderr}")
            return False # Indicate failure
        
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
    load_dotenv()
    while True:
        try:
            x=input("what would you like to do?: ")
            with Ai(content.AGENT_INSTRUCTIONS,"Baron") as orchestrator: #just the prompt from content file and the ai class
                print("Initialised\n\n") 
                out=orchestrator.generate(x) # generates the output and returns a json
                AIjson=json.loads(out) # loading the json


                for step in AIjson['steps']:
                    # --- Safely get all the data from the current step ---
                    step_num = step.get('step_number', 'N/A')
                    command_call = step.get('command_call', {})
                    function_call = command_call.get('function', 'N/A')
                    arguments = command_call.get('args', {})

                    # --- Print the primary step information ---
                    print(f"Step {step_num}:")

                    # Determine what the command is for display purposes
                    display_command = "N/A"
                    if function_call == 'execute_shell':
                        display_command = arguments.get('command', 'No command specified.')
                    elif function_call == 'write_file':
                        display_command = f"Write to file '{arguments.get('file_path', 'N/A')}'"

                    print(f"  └── Command: `{display_command}`")

                    # --- Check for and print the conditional logic ---
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
