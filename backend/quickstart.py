from celesto import Computer

print("Creating Celesto Cloud sandbox...")

with Computer(provider="cloud") as computer:
    result = computer.run("uname -a")

    print("Exit code:", result.exit_code)
    print("Output:")
    print(result.stdout)
    print("Error:")
    print(result.stderr)

print("Sandbox session finished.")
