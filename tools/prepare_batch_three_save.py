from pathlib import Path
import xml.etree.ElementTree as E
root=Path.cwd();rows={r.get('name'):r for r in E.parse(root/'artifacts/batch-03/cart-prefabs.xml').getroot()};out=E.Element('repairs')
mods=root/'artifacts/batch-03/candidate/Mods';meta={p.stem:p for p in mods.rglob('*.xml') if p.parent.name=='POIs'}
for r in E.parse(root/'artifacts/maps/Allium-v0.10/prefabs.xml').getroot():
 n=r.get('name');p=rows.get(n)
 if p is None:continue
 x,y,z=map(int,r.get('position').split(','));assert int(r.get('rotation','0'))==0
 m=E.parse(meta[n]);offset=m.find(".//property[@name='YOffset']");y+=int(offset.get('value')) if offset is not None else 0
 for c in p.findall('cell'):
  E.SubElement(out,'cell',prefab=n,lx=c.get('x'),ly=c.get('y'),lz=c.get('z'),x=str(x+int(c.get('x'))),y=str(y+int(c.get('y'))),z=str(z+int(c.get('z'))),before=c.get('before'),after=c.get('after'))
E.indent(out);E.ElementTree(out).write(root/'playtest/BatchThreeSave/Mods/BatchTwoSaveTools/cells.xml',encoding='utf-8');print('planned',len(out),'container cells')
