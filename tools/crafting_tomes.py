"""Idempotent optional lesson tome migration; preserve item IDs for existing saves."""
from pathlib import Path
import xml.etree.ElementTree as E
import shutil
SKILLS=('Farming','Cooking','Mining','Smithing','Carpentry','Alchemy')
def apply(mods):
    config=Path(mods)/'Delve/Config'
    for filename in ('items.xml','recipes.xml'):
        path=config/filename;tree=E.parse(path)
        for skill in SKILLS:
            name='delveLesson'+skill+'Notes'
            if filename=='items.xml':
                item=tree.find('.//item[@name="'+name+'"]')
                if item is None:raise ValueError('Missing tome '+name)
                for key,value in {'CustomIcon':'bookEnforcerDamage','EconomicValue':'500','EconomicBundleSize':'1','Stacknumber':'1','SellableToTrader':'false'}.items():
                    prop=item.find('property[@name="'+key+'"]')
                    if prop is None:prop=E.SubElement(item,'property',name=key)
                    prop.set('value',value)
            else:
                for parent in tree.iter():
                    for child in list(parent):
                        if child.tag=='recipe' and child.get('name')==name:parent.remove(child)
        E.indent(tree);tree.write(path,encoding='utf-8',xml_declaration=True)
    path=config/'traders.xml'
    tree=E.parse(path) if path.exists() else E.ElementTree(E.Element('configs'))
    root=tree.getroot()
    for op in list(root):
        if 'delveCraftingTomes' in E.tostring(op,encoding='unicode'):root.remove(op)
    group=E.SubElement(E.SubElement(root,'append',xpath='/traders/trader_item_groups'),'trader_item_group',name='delveCraftingTomes')
    for skill in SKILLS:E.SubElement(group,'item',name='delveLesson'+skill+'Notes',count='1')
    # Only staffed vendors, not vending machines or player-owned/rented shops.
    stock=E.SubElement(E.SubElement(root,'append',xpath="/traders/trader_info[not(@is_vending='true') and not(@player_owned='true') and not(@rentable='true')]"),'trader_items',count='all')
    E.SubElement(stock,'item',group='delveCraftingTomes',unique_only='true',count='3')
    E.indent(tree);tree.write(path,encoding='utf-8',xml_declaration=True)
    # Batch02 already maps these IDs to per-item icons. Reuse a native book
    # asset under those names so its later icon override still shows a tome.
    icons=Path(mods)/'ZZZZDelveBatch02/UIAtlases/ItemIconAtlas'
    if icons.exists():
        book=Path('D:/Steam/steamapps/common/7 Days To Die/Data/ItemIcons/bookEnforcerDamage.png')
        for skill in SKILLS:shutil.copy2(book,icons/('delveLesson'+skill+'Notes.png'))

