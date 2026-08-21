import argparse
import logging
import sys

from agent import __version__
from agent.agent import DinasAgent
from agent.config import AgentConfig


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="dinas-agent",
        description="DINAS distributed telemetry agent",
    )
    parser.add_argument("--server", default=None,
                        help="DINAS server URL (default: %(default)s)")
    parser.add_argument("--name", default=None,
                        help="Agent name (default: <hostname>)")
    parser.add_argument("--scope", default=None,
                        help="Network scope to monitor: CIDR, single IP, or comma-separated list")
    parser.add_argument("--collect-interval", type=int, default=None,
                        help="Seconds between collection cycles")
    parser.add_argument("--heartbeat-interval", type=int, default=None,
                        help="Seconds between heartbeats")
    parser.add_argument("--ping-count", type=int, default=None,
                        help="Pings per target per cycle")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--version", action="version",
                        version=f"dinas-agent {__version__}")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)-7s [%(threadName)s] %(name)s: %(message)s",
    )

    config = AgentConfig.from_env()

    if args.server:
        config.server_url = args.server
    if args.name:
        config.name = args.name
    if args.scope:
        config.network_scope = args.scope
    if args.collect_interval:
        config.collect_interval = args.collect_interval
    if args.heartbeat_interval:
        config.heartbeat_interval = args.heartbeat_interval
    if args.ping_count:
        config.ping_count = args.ping_count

    if not config.name:
        import socket
        config.name = f"agent-{socket.gethostname().lower()}"

    if not config.network_scope:
        print("error: --scope is required (e.g. 192.168.1.0/24)", file=sys.stderr)
        sys.exit(1)

    agent = DinasAgent(config)
    try:
        agent.run()
    except SystemExit as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
