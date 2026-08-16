"""A **synthetic, non-counted** opponent process for the boot integration tests.

This is not another team, not a league participant and not tournament evidence.
It exists for exactly one reason: the shipped CLI is `MaRs-777`, and Step-0
correctly refuses a peer that authors our own participant subtree, so a real
process-level proof needs a counterparty with a *different* group id. That
identity is supplied here, by test construction, and never by the shipped
entrypoint - `GROUP_CODE` stays `MaRs-777` in both role repositories and
anti-self-play is untouched.

Everything else it runs is production: the real composition, the real transport,
the real `AutonomousBoot`, the real `SeriesDriver` and the repository's own
`StrategyPort`. It chooses its own actions and gives this process nothing but
protocol messages.

Guarded under `__main__` so Windows' spawn start method re-imports it safely,
and it sets up its own paths because a child process gets no conftest.
"""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
for _directory in sorted(TESTS.iterdir()):
    if _directory.is_dir() and _directory.name != "__pycache__":
        sys.path.insert(0, str(_directory))


def main(
    role_name: str, port: int, opponent: str, root: str, variant: str = "same", trace: str = ""
) -> int:
    """Run one whole series as the distinct-group opponent, then stop.

    *variant* selects this side's boot config candidate: `same` is the shared
    one, `other` is an equally legal config differing only in the NEGOTIABLE
    `hint_max_words`, so a mismatch can be exercised without bending a FIXED
    value.

    *trace* names a file this process records its own inbound turn handlers
    into. It is installed here, on the synthetic side, and changes nothing the
    handlers decide - the shipped CLI never sees it.
    """
    import asyncio
    import dataclasses

    import composed_builders as compose
    import r7_builders as r7
    from r16_builders import GROUP_B

    from mars777_police.agent_runtime import AgentRuntime
    from mars777_police.app.sealed_record_values import ActorRole
    from mars777_police.autonomous_boot import AutonomousBoot
    from mars777_police.composition import compose_agent
    from mars777_police.domain.config_sections import WorldTerms
    from mars777_police.infra.settings import RuntimeSettings

    if variant == "slow":
        config = r7.SLOW
    elif variant == "same":
        config = r7.CONFIG
    else:
        config = dataclasses.replace(
            r7.CONFIG, world=WorldTerms(map_area=r7.CONFIG.world.map_area, hint_max_words=12)
        )
    role = ActorRole(role_name)
    base = compose.settings_for(role, opponent, port)
    settings = RuntimeSettings(
        base.role, base.local, base.key_id, base.secret, base.opponent, Path(root)
    )
    if trace:
        import process_trace

        from mars777_police.transport.peer_operations import InboundPeerOperations

        recorder = process_trace.HandlerTrace(Path(trace))
        process_trace.install(InboundPeerOperations, recorder)
        process_trace.install_dispatch(recorder)
        process_trace.install_session(recorder)
        process_trace.install_streams(recorder)
        process_trace.install_heartbeat(recorder)

    composition = compose_agent(settings, compose.identity_for(GROUP_B, "group_b"), GROUP_B)
    runtime = AgentRuntime(composition, settings.local.host, port)

    import os

    import process_trace

    applied = process_trace.apply_event_loop(os.environ.get("MARS777_TEST_EVENT_LOOP", ""))
    print(f"test event loop policy: {applied}", file=sys.stderr)

    asyncio.run(AutonomousBoot(runtime, settings, config, role).run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], *sys.argv[5:7]))
