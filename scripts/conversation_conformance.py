"""Opt-in twelve-request conversation conformance via installed public SDKs."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from lab_runner.conversation_conformance import main

if __name__=='__main__':
    raise SystemExit(main())
