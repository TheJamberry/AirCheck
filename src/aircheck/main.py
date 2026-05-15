import argparse
import signal
import sys
import threading
from pathlib import Path

import sounddevice as sd

from .audio_capture import AudioCapture
from .comparator import compare, rms
from .config import load_config
from .status import Status, determine_status, print_status

DEFAULT_CONFIG = Path("./config.yaml")


def list_devices() -> None:
    print(sd.query_devices())


def _check_loop(config, capture: AudioCapture, shutdown: threading.Event) -> None:
    """Inner loop: sample the buffer, compare, and print status every check_interval."""
    while not shutdown.is_set():
        off_air, program = capture.get_channels()

        if off_air is None:
            print_status(Status.UNCERTAIN, "buffering")
            shutdown.wait(config.check_interval)
            continue

        off_rms = rms(off_air)
        prog_rms = rms(program)

        similarity = None
        delay_ms = None
        if off_rms >= config.min_rms and prog_rms >= config.min_rms:
            try:
                similarity, delay_ms = compare(off_air, program, config.sample_rate)
            except Exception as exc:
                print(f"[ERROR] Comparison failed: {exc}", flush=True)

        status, detail = determine_status(
            off_rms,
            prog_rms,
            similarity,
            delay_ms,
            config.min_rms,
            config.match_threshold,
            config.max_delay_ms,
        )
        print_status(status, detail)
        shutdown.wait(config.check_interval)


def run(config_path: Path) -> None:
    config = load_config(config_path)

    shutdown = threading.Event()

    def _handle_signal(signum, frame):
        print("\n[INFO] Shutting down...", flush=True)
        shutdown.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    print(
        f"[INFO] Starting AirCheck — device={config.device!r} "
        f"rate={config.sample_rate}Hz  "
        f"off_air=ch{config.off_air_channel}  program=ch{config.program_channel}",
        flush=True,
    )

    retry_delay = 5
    while not shutdown.is_set():
        capture = AudioCapture(config)
        try:
            capture.start()
            print("[INFO] Audio capture started.", flush=True)
            _check_loop(config, capture, shutdown)
        except Exception as exc:
            print(
                f"[ERROR] Audio device error: {exc}. Retrying in {retry_delay}s...",
                flush=True,
            )
            shutdown.wait(retry_delay)
        finally:
            capture.stop()

    print("[INFO] AirCheck stopped.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aircheck",
        description="AirCheck — broadcast confidence monitor",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        metavar="PATH",
        help="Path to config.yaml (default: ./config.yaml)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit",
    )
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        sys.exit(0)

    if not args.config.exists():
        print(f"[ERROR] Config file not found: {args.config}", file=sys.stderr)
        print(
            "[ERROR] Copy config.example.yaml to config.yaml and edit it.",
            file=sys.stderr,
        )
        sys.exit(1)

    run(args.config)


if __name__ == "__main__":
    main()
