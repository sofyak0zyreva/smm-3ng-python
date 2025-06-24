#!/usr/bin/env python3
import sys
import os
from agent import start_agent


def usage():
    print("Usage: python3 main.py <command> [args]")
    print("Command:")
    print(
        "\tstart algoname instancename url  - start named module and connect to core url"
    )


def main():
    if len(sys.argv) < 2:
        usage()
        return 0

    command = sys.argv[1]

    if command == "start":
        if len(sys.argv) < 5:
            usage()
            return 1

        # Run in the background (daemon mode)
        if os.fork() > 0:
            return 0  # Parent process exits

        os.setsid()  # Create new session
        if os.fork() > 0:
            return 0  # First child exits

        # Start the agent
        start_agent(sys.argv[2], sys.argv[3], sys.argv[4])

    else:
        usage()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
