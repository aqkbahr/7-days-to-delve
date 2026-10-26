"""Run bounded console checks against the isolated combined progression profile."""
from pathlib import Path
from xml.etree import ElementTree as E
import argparse, socket, time

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('command')
parser.add_argument('--record')
parser.add_argument('--profile',default='AlliumProgression')
parser.add_argument('--evidence',default='allium-progression')
args=parser.parse_args()
assert args.profile.replace('-','').isalnum() and args.evidence.replace('-','').isalnum()
config=E.parse(root/'playtest'/args.profile/'serverconfig.xml')
def prop(name):return config.find(f"./property[@name='{name}']").get('value')
def read(sock,limit=5,wait_result=False):
    output=b'';deadline=time.monotonic()+limit
    while time.monotonic()<deadline:
        try:
            data=sock.recv(65536)
            if not data:break
            output+=data
        except socket.timeout:
            if wait_result and b'PASS' not in output and b'FAIL' not in output and b'Exception' not in output:continue
            break
    return output.decode(errors='replace')
with socket.create_connection(('127.0.0.1',int(prop('TelnetPort'))),5) as sock:
    sock.settimeout(2)
    read(sock);sock.sendall((prop('TelnetPassword')+'\r\n').encode());read(sock)
    sock.sendall((args.command+'\r\n').encode());output=read(sock,30,bool(args.record))
print(output)
if args.record:
    assert args.record.replace('-','').isalnum(), 'Use an evidence filename, not a path'
    destination=root/'artifacts/validation'/args.evidence/f'{args.record}.txt'
    destination.write_text(output)
