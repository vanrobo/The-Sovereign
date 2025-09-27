# Vanrobo © 2025

from dotenv import load_dotenv
import os
from google import genai
import json

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

                # all of this is just printing the output            
                print(f"AI's Thought Process: {AIjson['thought']}")
                for step in AIjson['steps']:
                    print("\n")
                    print(f"  Step {step['step_number']}: {step['reasoning']}")
                    print(f"  └── Command: `{step['command']}`")
                print()
                print("specific commands")

                print("\nThe Individuals\n")

                for steps in AIjson['steps']:
                    command_call = step['command_call']
                    function_call = command_call['function']
                    arguments = command_call['args']
                    if 'condition' not in step:
                        continue
                    else:
                        condition = step['condition']
                        check_step = condition['check_step']
                        required_outcome = condition['on_outcome']

                    print(f"Step {step['step_number']}: ")
                    print(f"  └── Command: `{step['command']}`")
                    print(f"      └── Condition: {condition}, check_step: {check_step} ")
                    print(f"          └──Required Outcome: {required_outcome}")
                    print(f"             └──Command: {command_call}, Function: {function_call}, Arguments: {arguments}")
                    
                print()
                for step in AIjson['steps']:
                    print(step['command'])

        except json.JSONDecodeError:
            print("\n--- ERROR: The AI did not return valid JSON. ---")
        except KeyError as e:
            print(f"\n--- ERROR: The AI's JSON was missing a required key: {e} ---")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
