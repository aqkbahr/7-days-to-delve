"""Compare corrected world against its unmodified package, including ore exclusions."""
import csv
import hashlib
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from fix_allium_poi_elevation import correct, TWO_BLOCK_LIFT, footprints
import numpy as np

base, fixed = map(Path, sys.argv[1:3])
old = list(ET.parse(base / 'prefabs.xml').getroot())
new = list(ET.parse(fixed / 'prefabs.xml').getroot())
assert len(old) == len(new)
raised = ores = 0
for a, b in zip(old, new):
    aa, bb = dict(a.attrib), dict(b.attrib)
    pa = list(map(int, aa.pop('position').split(',')))
    pb = list(map(int, bb.pop('position').split(',')))
    assert aa == bb
    delta = 0 if aa['name'].startswith('delve_ore_') else (2 if aa['name'] in TWO_BLOCK_LIFT else 1)
    assert pb == [pa[0], pa[1] + delta, pa[2]]
    raised += int(delta > 0)
    ores += int(delta == 0)
changed = {'prefabs.xml', 'locations.json', 'dungeons.json', 'dtm.raw'}
for path in base.iterdir():
    if path.is_file() and path.name not in changed:
        assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256((fixed/path.name).read_bytes()).digest(), path.name
before = (fixed/'prefabs.xml').read_bytes()
old_h=np.fromfile(base/'dtm.raw',dtype='<u2').reshape(8192,8192)
new_h=np.fromfile(fixed/'dtm.raw',dtype='<u2').reshape(8192,8192)
allowed=np.zeros(old_h.shape,dtype=bool)
for name,x,y,z,sx,sz in footprints(base,old):
    if name.startswith('delve_ore_'):
        assert np.array_equal(old_h[z+4096:z+4096+sz,x+4096:x+4096+sx],new_h[z+4096:z+4096+sz,x+4096:x+4096+sx]), name
    else:
        allowed[max(0,z+4096-12):min(8192,z+4096+sz+12),max(0,x+4096-12):min(8192,x+4096+sx+12)]=True
        for margin in (1,4):
            left,right=x+4096-margin,x+4096+sx-1+margin
            low,high=z+4096-margin,z+4096+sz-1+margin
            perimeter=np.concatenate((new_h[low,left:right+1],new_h[high,left:right+1],new_h[low:high+1,left],new_h[low:high+1,right]))
            assert np.all(perimeter==y*257), f'Apron not level: {name} at {x},{z}, margin {margin}'
assert not np.any((old_h!=new_h)&~allowed), 'Terrain changed outside POI aprons'
correct(fixed)
assert (fixed/'prefabs.xml').read_bytes() == before, 'Repeated correction changed placements'
for name in ('locations.json', 'dungeons.json'):
    if not (fixed/name).exists():
        continue
    placements = {(n.get('name'), n.get('position')) for n in new}
    for record in json.loads((fixed/name).read_text()):
        assert (record['prefab'], ','.join(map(str,record['position']))) in placements
print(f'PASS: {raised} surveyed ground-layer lifts; {ores} unchanged ore sites and terrain; height edits confined to POI aprons; other world inputs unchanged; metadata consistent; correction idempotent.')
