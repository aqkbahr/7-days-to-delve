"""Final Allium placement correction; run on a fresh world, never a live save.

The native prefab ground layer is -YOffset-1. Allium terraces were authored at
the declared placement Y, which put the prefab surface a metre below the apron.
Keep the heightmap and buried ore sites unchanged; lift gameplay POIs by their
surveyed ground-layer offset (one cell, or two for the church templates below).
The receipt makes repeated packaging idempotent and detects later edits.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

# Native edge-layer survey: these three templates have their perimeter terrain
# at -YOffset-2, unlike the other 500 placements at -YOffset-1.
TWO_BLOCK_LIFT = {'church_01', 'remnant_church_01', 'delve_arbor_remnant_church_01'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def footprints(world, nodes):
    mods = world.parents[1] / 'Mods'
    native = Path('D:/Steam/steamapps/common/7 Days To Die/Data/Prefabs/POIs')
    files = {p.stem: p for p in mods.glob('*/Prefabs/POIs/*.xml')}
    result = []
    for node in nodes:
        name = node.get('name')
        xml = files.get(name, native / (name + '.xml'))
        props = {p.get('name'): p.get('value') for p in ET.parse(xml).getroot().findall('property')}
        sx, _, sz = map(int, props['PrefabSize'].split(','))
        if int(node.get('rotation', '0')) % 2:
            sx, sz = sz, sx
        x, y, z = map(int, node.get('position').split(','))
        result.append((name, x, y, z, sx, sz))
    return result

def grade_aprons(world, sites):
    original = np.fromfile(world/'dtm.raw', dtype='<u2').reshape(8192, 8192)
    heights = original.copy()
    best = np.zeros(original.shape, dtype=np.uint8)
    protected = np.asarray(Image.open(world/'splat4.png'))[:, :, 2][::-1] > 0
    for name, x, y, z, sx, sz in sites:
        if name.startswith('delve_ore_'):
            protected[z+4096:z+4096+sz, x+4096:x+4096+sx] = True
    for name, x, y, z, sx, sz in sites:
        if name.startswith('delve_ore_'):
            continue
        left, right = max(0,x+4096-12), min(8192,x+4096+sx+12)
        low, high = max(0,z+4096-12), min(8192,z+4096+sz+12)
        zz, xx = np.mgrid[low:high, left:right]
        distance = np.maximum(np.maximum(x+4096-xx, xx-(x+4096+sx-1)),
                              np.maximum(z+4096-zz, zz-(z+4096+sz-1)))
        blend = np.clip((12-distance)/8, 0, 1)
        blend = blend*blend*(3-2*blend)
        weight = np.rint(blend*255).astype(np.uint8)
        previous = best[low:high,left:right]
        use = (weight > previous) & ~protected[low:high,left:right]
        view = heights[low:high,left:right]
        values = np.rint(original[low:high,left:right]*(1-blend)+y*257*blend).astype('<u2')
        view[use] = values[use]
        previous[use] = weight[use]
    changed = int(np.count_nonzero(heights != original))
    heights.tofile(world/'dtm.raw')
    return changed

def update_metadata(folder, changes):
    lookup = {(c['name'], tuple(c['before'])): c for c in changes}
    for filename in ('locations.json', 'dungeons.json'):
        meta = Path(folder) / filename
        if not meta.exists():
            continue
        records = json.loads(meta.read_text(encoding='utf-8-sig'))
        for record in records:
            change = lookup.get((record['prefab'], tuple(record['position'])))
            if change:
                record['position'] = change['after']
                record['terrain_height'] = change['before'][1]
                for key in ('height', 'underground_bottom'):
                    if key in record:
                        record[key] += change['after'][1] - change['before'][1]
        meta.write_text(json.dumps(records, indent=2), encoding='utf-8')

def correct(world):
    world = Path(world)
    path = world / 'prefabs.xml'
    receipt = world / 'poi-elevation.json'
    if receipt.exists():
        report = json.loads(receipt.read_text())
        assert report['correction'] == 'native-ground-layer-v3', 'Obsolete correction: rebuild from original placements'
        assert digest(path) == report['after_sha256'], 'Placements changed after elevation correction'
        assert digest(world/'dtm.raw') == report['terrain_after_sha256'], 'Terrain changed after apron correction'
        return report
    before = digest(path)
    tree = ET.parse(path)
    sites = footprints(world, tree.getroot())
    terrain_before = digest(world/'dtm.raw')
    changes = []
    excluded = 0
    for node in tree.getroot():
        if node.get('name', '').startswith('delve_ore_'):
            excluded += 1
            continue
        assert node.get('y_is_groundlevel') == 'true', node.attrib
        old = list(map(int, node.get('position').split(',')))
        lift = 2 if node.get('name') in TWO_BLOCK_LIFT else 1
        new = [old[0], old[1] + lift, old[2]]
        node.set('position', ','.join(map(str, new)))
        changes.append(dict(name=node.get('name'), before=old, after=new))
    update_metadata(world, changes)
    terrain_changed = grade_aprons(world, sites)
    ET.indent(tree)
    tree.write(path, encoding='utf-8', xml_declaration=True)
    report = dict(correction='native-ground-layer-v3', before_sha256=before,
                  after_sha256=digest(path), raised=len(changes), ore_unchanged=excluded,
                  terrain_before_sha256=terrain_before, terrain_after_sha256=digest(world/'dtm.raw'),
                  terrain_cells_changed=terrain_changed,
                  changes=changes)
    receipt.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('world')
    parser.add_argument('--metadata-root')
    args = parser.parse_args()
    report = correct(args.world)
    if args.metadata_root:
        update_metadata(args.metadata_root, report['changes'])
    print(f"Raised {report['raised']} POIs; retained {report['ore_unchanged']} ore placements")
