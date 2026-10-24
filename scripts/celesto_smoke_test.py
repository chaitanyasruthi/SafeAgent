"""Phase 1: minimal Celesto Cloud connection test.
Runs ONE command inside a Celesto sandbox (never on the host)."""
import os
import sys

from celesto import Computer

if not os.environ.get("CELESTO_API_KEY"):
    sys.exit("CELESTO_API_KEY is not set.")

with Computer(provider="cloud") as computer:
    print("Sandbox object type:", type(computer))
    print("Public attributes:", [a for a in dir(computer) if not a.startswith("_")])
    result = computer.run("echo hello-from-celesto && uname -a")
    print("exit_code:", result.exit_code)
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)

print("Done. Sandbox context exited (cleanup should have run).")
