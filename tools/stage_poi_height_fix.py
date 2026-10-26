"""Stage audited POI surface alignment; never edit a live world or save.

Native y_is_groundlevel adds YOffset to the specified position. The native
heightmap compositor then uses originY + localTerrainY - density/128 - 1.
Matching placement Y directly to DTM therefore leaves authored ground low.
"""
import csv,json,hashlib
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'artifacts/maps/Allium-v0.10'
OUT=ROOT/'artifacts/batch-02/poi-height-candidate'
OUT.mkdir(parents=True,exist_ok=True)
audit=list(csv.DictReader((ROOT/'artifacts/batch-02/poi-height-audit.csv').open()))
tree=E.parse(SOURCE/'prefabs.xml');entries=list(tree.getroot())
assert len(entries)==len(audit)
records=json.loads((SOURCE/'locations.json').read_text())
locations={(r['prefab'],tuple(r['position'])):r for r in records}
changes=[];excluded=[]
for entry,row in zip(entries,audit):
    name=entry.get('name');pos=list(map(int,entry.get('position').split(',')))
    assert name==row['prefab'] and pos[1]==int(row['groundY'])
    # Only documented surface POIs: resource sites aren't in the surface catalogue.
    record=locations.get((name,tuple(pos)))
    if record is None:
        excluded.append(name);continue
    delta=float(row['medianSurfaceDelta'])
    lift=round(-delta)
    assert lift in (1,2) and abs(delta+lift)<.02,(name,delta)
    before=pos.copy();pos[1]+=lift
    entry.set('position',','.join(map(str,pos)))
    record['position']=pos
    # height remains the target terrain surface; do not lift DTM along with the POI.
    record['surface_alignment_lift']=lift
    record['surface_alignment_residual']=delta+lift
    if 'underground_bottom' in record:record['underground_bottom']+=lift
    changes.append(dict(prefab=name,before=before,after=pos,lift=lift,residual=delta+lift))
assert len(changes)==len(records)
E.indent(tree);tree.write(OUT/'prefabs.xml',encoding='utf-8',xml_declaration=True)
(OUT/'locations.json').write_text(json.dumps(records,indent=2)+'\n')
report=dict(status='STAGED_NOT_DEPLOYED',surface_pois=len(changes),excluded_resource_prefabs=len(excluded),
    max_residual=max(abs(c['residual']) for c in changes),changes=changes,
    source_dtm_sha256=hashlib.sha256((SOURCE/'dtm.raw').read_bytes()).hexdigest(),
    remaining='Native placed-terrain seam checks and existing-save migration required. No live map/saves modified.')
(OUT/'alignment-report.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:v for k,v in report.items() if k not in ('changes','source_dtm_sha256')})
