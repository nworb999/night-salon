"""
Server run scripts for the office simulation project.

These scripts provide command-line interfaces to run the simulation and coordinator servers.
Example usage:

    # Run simulation server with custom config
    python -m night_salon.scripts.run_simulation --config config.env --log-file sim.log

    # Run coordinator server with custom simulation URL
    python -m night_salon.scripts.run_coordinator --simulation-url http://localhost:8000
"""
