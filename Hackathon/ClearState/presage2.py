import argparse
import getpass
import json
import os
import signal
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROCESSING_STATES = {
    "kUninitialized": "uninitialized",
    "kIdle": "idle",
    "kStarting": "starting",
    "kRunning": "running",
    "kStopping": "stopping",
    "kError": "error",
}


def find_node():
    node = shutil.which("node")
    if node:
        return node

    if os.name == "nt":
        candidates = [
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "nodejs" / "node.exe",
            Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "nodejs" / "node.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "nodejs" / "node.exe",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)

    return None


def describe_measurement(item, unit):
    if not item or item.get("value") is None:
        return "not available yet"
    text = f"{item['value']:g} {unit}"
    if item.get("confidence") is not None:
        text += f", confidence {item['confidence']:.0f}%"
    if item.get("stable") is not None:
        text += ", stable" if item["stable"] else ", not stable"
    return text


def describe_metrics(event):
    print(f"Pulse: {describe_measurement(event.get('pulse_rate'), 'bpm')}")
    print(f"Breathing: {describe_measurement(event.get('breathing_rate'), 'breaths/min')}")
    face = event.get("face") or {}
    blinking = face.get("blinking")
    talking = face.get("talking")
    expression = face.get("expression") or {}
    scores = expression.get("scores") or []
    top_expression = max(scores, key=lambda score: score.get("confidence", 0), default=None)
    landmarks = face.get("landmarks") or {}
    points = landmarks.get("points") or []
    print(
        "Face: "
        f"blinking={blinking.get('detected') if blinking else 'n/a'}, "
        f"talking={talking.get('detected') if talking else 'n/a'}, "
        f"expression={top_expression.get('type') if top_expression else 'n/a'}, "
        f"landmarks={len(points)} points"
    )


def display_event(event):
    event_type = event.get("type")
    if event_type == "started":
        print(f"SmartSpectra {event.get('version')} started. Press Ctrl+C to stop.")
    elif event_type == "status":
        status = PROCESSING_STATES.get(event.get("status"), event.get("status"))
        print(f"Processing: {status}")
    elif event_type == "validation":
        print(f"Input guidance: {event.get('hint')}")
    elif event_type == "metrics":
        describe_metrics(event)
    elif event_type == "decode_error":
        print(f"Could not decode metrics: {event.get('message')}")
    elif event_type == "error":
        print(f"SmartSpectra error: {event.get('message')} (code={event.get('code')})")


def run_live(node, output_jsonl):
    output_file = output_jsonl.open("a", encoding="utf-8") if output_jsonl else None
    process = subprocess.Popen(
        [node, str(ROOT / "presage_bridge.mjs"), "--live"],
        cwd=ROOT,
        env=os.environ.copy(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    try:
        for line in process.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                print(line, end="")
                continue
            if output_file and event.get("type") == "metrics":
                output_file.write(json.dumps(event, separators=(",", ":")) + "\n")
                output_file.flush()
            display_event(event)
        return process.wait()
    except KeyboardInterrupt:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait()
        return 130
    finally:
        if process.stdout:
            process.stdout.close()
        if output_file:
            output_file.close()


def main():
    parser = argparse.ArgumentParser(description="Test Presage SmartSpectra from Python.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live",
        action="store_true",
        help="authenticate and start a live camera measurement",
    )
    mode.add_argument(
        "--gui",
        action="store_true",
        help="open the Pygame dashboard",
    )
    parser.add_argument(
        "--jsonl",
        type=Path,
        help="append decoded metrics, including facial landmarks, to this JSONL file",
    )
    args = parser.parse_args()

    if args.jsonl and not (args.live or args.gui):
        parser.error("--jsonl can only be used together with --live or --gui.")

    node = find_node()
    if node is None:
        parser.error("Node.js 20 or newer is required for Presage's supported SDK binding.")

    if args.gui:
        from presage_gui import run_gui

        return run_gui(node, args.jsonl)

    if args.live:
        api_key = os.environ.get("SMARTSPECTRA_API_KEY")
        if not api_key:
            if not os.isatty(0):
                parser.error("Set SMARTSPECTRA_API_KEY before running in a non-interactive shell.")
            api_key = getpass.getpass("Presage API key: ")
        if not api_key:
            parser.error("An API key is required for a live measurement.")
        os.environ["SMARTSPECTRA_API_KEY"] = api_key
        return run_live(node, args.jsonl)

    try:
        return subprocess.run(
            [node, str(ROOT / "presage_bridge.mjs"), "--check"],
            cwd=ROOT,
            env=os.environ.copy(),
            check=False,
        ).returncode
    except KeyboardInterrupt:
        return 130
    except FileNotFoundError:
        parser.error("Node.js was not found. Install Node.js 20 or newer and retry.")


if __name__ == "__main__":
    raise SystemExit(main())