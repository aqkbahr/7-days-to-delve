from pathlib import Path
from lxml import etree as E
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'src/ZZZZDelveBatch02/Config/blocks.xml';tree=E.parse(str(path));root=tree.getroot()
native=E.parse('D:/Steam/steamapps/common/7 Days To Die/Data/Config/blocks.xml')
for name in ('tractorGreen','tractorRed'):
    target=f'/blocks/block[@name="{name}"]'
    for prop,value in [('Model','#@modfolder(ZZZDelveBatch01):Resources/batchone.unity3d?delveWagon1'),('CustomIcon','delveWagon1'),('TintColor','FFFFFF')]:
        xp=target+f'/property[@name="{prop}"]'
        for op in list(root):
            if op.get('xpath') in (xp,xp+'/@value') or (op.get('xpath')==target and op.find(f'property[@name="{prop}"]') is not None):root.remove(op)
        if native.xpath(xp):E.SubElement(root,'set',xpath=xp+'/@value').text=value
        else:E.SubElement(E.SubElement(root,'append',xpath=target),'property',name=prop,value=value)
target='/blocks/block[@name="delveFarmPlotPlate"]'
for op in list(root):
    if op.get('xpath')==target and op.find('property[@name="ModelOffset"]') is not None:root.remove(op)
E.SubElement(E.SubElement(root,'append',xpath=target),'property',name='ModelOffset',value='1,-1,1')
path.write_bytes(E.tostring(root,pretty_print=True))
print('Staged lootable tractor wagons and terrain-seated farm plate mesh')


