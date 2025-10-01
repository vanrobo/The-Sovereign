import subprocess

# Run the 'ls -l' command on Linux/macOS or 'dir' on Windows.
# The command and its arguments are passed as a list of strings.
# For a cross-platform example, you could use: ['python', '--version']
try:
    # For Unix-like systems (Linux, macOS)
    result = subprocess.run(['ls', '-l'], capture_output=True, text=True, check=True)
except FileNotFoundError:
    # For Windows
    result = subprocess.run(['dir'], capture_output=True, text=True, check=True, shell=True)


# The standard output of the command is captured in the 'stdout' attribute.
print("Standard Output:")
print(result.stdout)

# The standard error (if any) is in the 'stderr' attribute.
print("\nStandard Error:")
print(result.stderr)

# The return code of the command is in the 'returncode' attribute.
print(f"\nReturn Code: {result.returncode}")