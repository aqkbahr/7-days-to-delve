"""Generate a separate presentation candidate; never alter the stable release."""
import json
import shutil
from pathlib import Path
from xml.etree import ElementTree as E
from build_forest_slice import merge

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'src/ZDelvePresentation'
GAME = Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')

def main():
    (OUT/'Config').mkdir(parents=True, exist_ok=True)
    (OUT/'Resources').mkdir(exist_ok=True)
    (OUT/'ModInfo.xml').write_text('<xml><Name value="ZDelvePresentation"/><DisplayName value="Delve presentation integration candidate"/><Version value="0.1.0-dev"/><Author value="Delve"/></xml>', encoding='utf-8')
    known = {}
    for family, element in [('items','item'), ('blocks','block')]:
        names = {e.get('name') for e in E.parse(GAME/(family+'.xml')).iter(element)}
        for mod in ROOT.joinpath('src').iterdir():
            path = mod/'Config'/(family+'.xml')
            if mod != OUT and path.exists():
                names.update(e.get('name') for e in E.parse(path).iter(element))
        known[family] = names
    docs = {family:E.Element('configs') for family in known}
    merged = {family:merge(ROOT/'src',family) for family in known}
    report = {'bindings':[], 'unbound_review_assets':[], 'runtime_acceptance':'PENDING'}
    weapon_catalog=json.loads((ROOT/'src/Art/ForestWeapons/catalogue.json').read_text())
    held={a['id']:(a['id'],a['family']) for a in weapon_catalog['weapons'] if a['family'] not in ('rune','arrow','bolt')}
    for alias,target in weapon_catalog.get('aliases',{}).items():
        if target in held: held[alias]=held[target]
    lines=['using System.Collections.Generic; namespace DelvePresentation { public static class HeldCatalog { public static readonly Dictionary<string,string[]> Items=new Dictionary<string,string[]> {']
    lines += ['{"'+name+'",new[]{"'+asset+'","'+family+'"}},' for name,(asset,family) in held.items()]
    lines += ['};}}']
    (ROOT/'src/Art/HeldCatalog.generated.cs').write_text('\n'.join(lines))
    def set_properties(family, name, values, asset):
        if name not in known[family]:
            report['unbound_review_assets'].append(name)
            return
        element = 'item' if family=='items' else 'block'
        target = '/%s/%s[@name="%s"]' % (family, element, name)
        for key,value in values.items():
            prop_path=target+'/property[@name="'+key+'"]'
            if merged[family].xpath(prop_path):
                E.SubElement(docs[family], 'set', xpath=prop_path+'/@value').text=str(value)
            else:
                add=E.SubElement(docs[family], 'append', xpath=target)
                E.SubElement(add, 'property', name=key, value=str(value))
        report['bindings'].append({'definition':name,'family':family,'asset':asset,'properties':values})
    def address(bundle, asset):
        return '#@modfolder:Resources/'+bundle+'.unity3d?'+asset
    for group,bundle in [('forest-props','forestprops'),('forest-weapons','forestweapons'),('forest-armor','forestarmor')]:
        shutil.copy2(ROOT/'artifacts'/group/'Bundle'/(bundle+'.unity3d'), OUT/'Resources')
    props=json.loads((ROOT/'src/Art/ForestProps/catalogue.json').read_text())
    for a in props['assets']:
        name=a['id']
        if a['kind'] in ('station','plant'):
            set_properties('blocks',name,{'Shape':'ModelEntity','Model':address('forestprops',name),'ModelOffset':'0,0,0'},name)
        else:
            set_properties('items',name,{'DropMeshfile':address('forestprops',name+'_Drop')},name+'_Drop')
    for name,target in props['aliases'].items():
        set_properties('blocks',name,{'Shape':'ModelEntity','Model':address('forestprops',target),'ModelOffset':'0,0,0'},target)
    for file,key,bundle in [('ForestWeapons','weapons','forestweapons'),('ForestArmor','armor','forestarmor')]:
        catalog=json.loads((ROOT/'src/Art'/file/'catalogue.json').read_text())
        for a in catalog[key]:
            set_properties('items',a['id'],{'DropMeshfile':address(bundle,a['id']+'_Drop')},a['id']+'_Drop')
            if key=='armor':
                target='/items/item[@name="'+a['id']+'"]/property[@class="SDCS"]/property[@name="Prefab"]/@value'
                E.SubElement(docs['items'],'set',xpath=target).text=address(bundle,a['id']+'_Worn')
                if a['id'].endswith('Helmet'):
                    # These are open-faced shells, not replacement player heads.
                    base='/items/item[@name="'+a['id']+'"]/property[@class="SDCS"]/property'
                    E.SubElement(docs['items'],'remove',xpath=base+'[@name="Excludes"]')
                    E.SubElement(docs['items'],'set',xpath=base+'[@name="HairMaskType"]/@value').text='Full'
                report['bindings'].append({'definition':a['id'],'family':'nativeSDCS','asset':a['id']+'_Worn','body_exclusions':'preserve face; hide hair' if a['id'].endswith('Helmet') else 'retain native slot exclusions'})
        for name,target in catalog.get('aliases',{}).items():
            set_properties('items',name,{'DropMeshfile':address(bundle,target+'_Drop')},target+'_Drop')
    for name in ('foodDelveTrailRations','foodDelveTrailRation','foodDelveTravelBread','foodDelveBerryPreserve','foodDelveHoneyberryCakes'):
        if any(a['id']==name for a in props['assets']):
            set_properties('items',name+'DelvePacked',{'DropMeshfile':address('forestprops',name+'_Drop')},name+'_Drop')
    # Shared bottle geometry for the newly implemented protection draught.
    set_properties('items','delveArborProtection',{'DropMeshfile':address('forestprops','drinkJarBoiledWater_Drop')},'drinkJarBoiledWater_Drop')
    for family,doc in docs.items():
        E.indent(doc)
        E.ElementTree(doc).write(OUT/'Config'/(family+'.xml'),encoding='utf-8',xml_declaration=True)
    (ROOT/'artifacts/integration/art-bindings.json').write_text(json.dumps(report,indent=2))
    print('Candidate presentation bindings:',len(report['bindings']),'; unbound review-only assets:',len(report['unbound_review_assets']))
if __name__=='__main__': main()

