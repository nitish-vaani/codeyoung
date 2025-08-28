from __future__ import annotations

from livekit.agents import JobContext, cli, WorkerOptions
from .helper.entrypoint_handler import handle_entrypoint

def prewarm_fnc(proc):
    """Prewarm function for session initialization"""
    pass

async def entrypoint(ctx: JobContext):
    """Main entrypoint for the agent - delegates to handler"""
    await handle_entrypoint(ctx)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm_fnc,
            agent_name="Codeyoung Agent",
        )
    )
