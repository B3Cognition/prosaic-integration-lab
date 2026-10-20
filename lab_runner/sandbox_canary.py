"""Owned synthetic CLI canary. Never supply real secrets or shared paths."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time


def main():
    if sys.argv[1:]==['--version']:
        print('sandbox-canary-v1');return
    if len(sys.argv)==3 and sys.argv[1]=='--linger':
        time.sleep(4);return
    parser=argparse.ArgumentParser()
    for name in ('nonce','mode','input','slot','secret','forbidden','alias','write','tcp','udp','unix'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    if args.mode in ('timeout','output'):
        subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--linger',args.nonce])
        # Give the independent host inventory time to observe both owned PIDs.
        time.sleep(0.35)
        if args.mode=='output':
            print('X'*32768,flush=True)
        time.sleep(4);return
    def readable(path):
        try:Path(path).read_bytes();return True
        except OSError:return False
    def writable(path):
        try:Path(path).write_text('OWNED-SYNTHETIC-WRITE');return True
        except OSError:return False
    def connect(family,address):
        try:
            with socket.socket(family,socket.SOCK_STREAM) as client:
                client.settimeout(0.2);client.connect(address)
                client.sendall(('probe:'+args.nonce).encode())
            return True
        except OSError:return False
    scratch=Path(os.environ['TMPDIR'])
    checks=dict(grantedRead=Path(args.input).read_text()=='GRANTED-CANARY',
        outsideReadDenied=not readable(args.secret),aliasReadDenied=not readable(args.alias),
        forbiddenReadDenied=not readable(args.forbidden),outsideWriteDenied=not writable(args.write),
        evidenceWriteDenied=not writable(Path(args.input).parent/('write-'+args.slot)),
        credentialAbsent=os.getenv('PROSAIC_SANDBOX_CANARY_KEY') is None,
        privateHome=not any(Path(os.environ['HOME']).iterdir()),
        scratchWritable=writable(scratch/('scratch-'+args.slot)),
        tcpDenied=not connect(socket.AF_INET,('127.0.0.1',int(args.tcp))),
        unixDenied=not connect(socket.AF_UNIX,args.unix))
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as client:
            client.sendto(('probe:'+args.nonce).encode(),('127.0.0.1',int(args.udp)))
    except OSError:pass
    print(json.dumps(dict(nonce=args.nonce,slot=args.slot,checks=checks,
                          scratch=str(scratch),home=os.environ['HOME'])))


if __name__=='__main__':main()
