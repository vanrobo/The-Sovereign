import subprocess

# Execute a simple command and capture output
# 'dir' is a built-in Windows shell command, so we need shell=True to execute it.
try:
    result = subprocess.run('dir', shell=True, capture_output=True, text=True, check=True)
    print("--- Directory Listing ---")
    print(result.stdout)
    if result.stderr:
        print("--- Errors ---") 
        print(result.stderr)
except FileNotFoundError:
    print("Error: The 'dir' command is not available.")
except subprocess.CalledProcessError as e:
    print(f"Command failed with return code {e.returncode}")
    print(e.stderr)


# Execute a command with shell=True
# This command works similarly on both platforms when shell=True is used.
result_shell = subprocess.run('echo "Hello from the Windows shell!"', shell=True, capture_output=True, text=True)
print("\n--- Echo Command ---")
print(result_shell.stdout)