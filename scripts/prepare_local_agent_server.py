"""Create a private server base; never print or edit shared credentials/settings."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lab_runner.native_eval.local_server import prepare_agent_server_profile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-base',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--model',required=True)
    args=parser.parse_args()
    print(json.dumps(prepare_agent_server_profile(args.source_base,args.destination,args.model),sort_keys=True))


if __name__=='__main__':main()
