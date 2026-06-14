# stream_runner.py
# Helper script to run scenario streams from the CLI or manually trigger updates.

import asyncio
import sys
from .scenario_engine import start_scenario_stream, stop_scenario_stream

async def main():
    if len(sys.argv) < 3:
        print("Usage: python -m backend.simulation.stream_runner [start|stop] [scenario_id]")
        return

    cmd = sys.argv[1]
    scenario_id = sys.argv[2]
    session_id = "active"

    if cmd == "start":
        print(f"Starting stream for scenario {scenario_id}...")
        res = await start_scenario_stream(session_id, scenario_id)
        print("Result:", res)
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...")
            await stop_scenario_stream(session_id)
    elif cmd == "stop":
        print("Stopping stream...")
        res = await stop_scenario_stream(session_id)
        print("Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
