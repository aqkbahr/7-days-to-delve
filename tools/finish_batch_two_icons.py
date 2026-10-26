"""Original code-drawn parchment/settlement symbols; model-derived icons stay authoritative."""
from pathlib import Path
import json,math,shutil
from PIL import Image,ImageDraw
from lxml import etree as E
import build_forest_slice as merger
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'src/ZZZZDelveBatch02/UIAtlases/ItemIconAtlas'
def symbol(d,kind,c):
    if kind in ('Mining','Smithing','Carpentry'):
        d.line((130,360,330,140),fill='#81512d',width=30)
        if kind=='Mining':d.arc((150,80,395,270),185,350,fill=c,width=26)
        elif kind=='Smithing':d.rounded_rectangle((210,105,370,205),12,fill=c,outline='#263443',width=8)
        else:d.polygon([(260,130),(370,130),(385,270),(300,250)],fill=c,outline='#263443',width=8)
    elif kind=='Alchemy':
        d.rounded_rectangle((220,100,290,270),8,fill=c);d.ellipse((160,220,355,390),fill=c,outline='#263443',width=9);d.ellipse((175,260,335,375),fill='#7b5997');d.line((235,145,235,230),fill='#eef6ea',width=9)
    elif kind=='Cooking':
        d.ellipse((130,200,370,390),fill=c,outline='#263443',width=9);d.arc((105,240,190,310),60,300,fill='#263443',width=15);d.line((145,215,355,215),fill='#263443',width=15);d.arc((210,90,250,190),80,270,fill='#a7bdb2',width=9)
    else:
        d.line((260,375,260,140),fill='#466d35',width=16)
        for y in (170,235,300):d.ellipse((170,y-30,260,y+20),fill=c);d.ellipse((260,y-60,345,y-10),fill=c)
def draw(name,kind):
    im=Image.new('RGBA',(512,512));d=ImageDraw.Draw(im)
    if kind=='note':
        d.polygon([(80,55),(390,55),(435,105),(435,455),(80,455)],fill='#c7ac77',outline='#614c32',width=10);d.polygon([(390,55),(435,105),(390,105)],fill='#f0dab0')
        skill=name.replace('delveLesson','').replace('Notes','');colors={'Farming':'#7ba44b','Cooking':'#c48b4e','Mining':'#a1b5c3','Smithing':'#bac7ce','Carpentry':'#b99962','Alchemy':'#9cc6bd'};symbol(d,skill,colors[skill])
        for y in (410,427):d.line((125,y,375,y),fill='#826b43',width=5)
    elif kind=='plot':
        d.polygon([(55,240),(260,130),(460,245),(255,385)],fill='#765237',outline='#3b3024',width=12)
        for i in range(5):d.line((110+i*38,235-i*18,295+i*31,337-i*22),fill='#ae8050',width=12)
        if 'Composted' in name:
            d.line((260,265,260,170),fill='#7f9d46',width=12);d.ellipse((200,180,260,220),fill='#87ac43');d.ellipse((260,155,320,195),fill='#a6bf5d')
    elif kind=='ledger':
        d.rounded_rectangle((100,70,410,445),20,fill='#684c35',outline='#c6aa6e',width=12);d.rectangle((135,80,160,435),fill='#a78750');d.rectangle((200,160,355,340),fill='#d8c493')
        for y in (200,240,280):d.line((225,y,330,y),fill='#5e533d',width=8)
    elif kind=='flag':
        d.line((130,450,130,55),fill='#b08b55',width=22);d.polygon([(140,70),(405,90),(350,190),(405,285),(140,260)],fill='#385f75',outline='#c2a46a',width=10);d.polygon([(250,125),(290,160),(270,220),(230,220),(210,160)],fill='#d2b77b')
    else:
        d.polygon([(75,430),(160,380),(350,380),(440,430),(440,465),(75,465)],fill='#747b7a',outline='#363e43',width=8)
        d.rounded_rectangle((185,175,330,390),12,fill='#929c99',outline='#363e43',width=10);d.ellipse((180,80,335,235),fill='#729c9c',outline='#d7d5a9',width=12);d.polygon([(255,105),(280,150),(255,200),(230,150)],fill='#baf4d0')
    im.resize((256,256),Image.Resampling.LANCZOS).save(out/(name+'.png'))
for skill in ('Farming','Cooking','Mining','Smithing','Carpentry','Alchemy'):draw('delveLesson'+skill+'Notes','note')
for n,k in [('delveFarmPlotPlate','plot'),('delveCompostedFarmPlot','plot'),('delveRecruitLedger','ledger'),('delveRallyFlag','flag'),('delveRecoveryShrine','shrine')]:draw(n,k)
for n in ('foodDelveTrailRations','foodDelveTrailRation','foodDelveTravelBread','foodDelveBerryPreserve','foodDelveHoneyberryCakes'):shutil.copy2(out/(n+'.png'),out/(n+'DelvePacked.png'))
excluded={'delveArborProtection','delveWayrestStewardSpawn','meleeHandDelveWorker','meleeHandDelveDefender'}
audit=json.loads((ROOT/'artifacts/batch-02/item-icon-audit.json').read_text());report=[]
for kind in ('items','blocks'):
    path=ROOT/f'src/ZZZZDelveBatch02/Config/{kind}.xml';tree=E.parse(str(path));root=tree.getroot()
    # Repeatable generation: discard only our previous icon property operations.
    for op in list(root):
        if 'CustomIcon' in op.get('xpath','') or (op.tag=='append' and op.find('property[@name="CustomIcon"]') is not None) or (op.tag=='append' and op.find('property[@name="CustomIconTint"]') is not None):root.remove(op)
    merger.MOD_NAMES=['Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest','ZDelveRecruits','ZDelvePresentation','ZZZDelveBatch01']
    base=merger.merge(ROOT/'artifacts/batch-02/candidate/Mods',kind)
    for row in audit:
        n=row['id']
        if row['kind']!=kind or n in excluded or n.endswith('Attack'):continue
        icon=out/(n+'.png');assert icon.exists(),n
        im=Image.open(icon);assert im.getbbox() is not None,n
        target=f'/{kind}/{kind[:-1]}[@name="{n}"]'
        # Set existing local declarations; otherwise override inherited properties.
        for prop,val in [('CustomIcon',n),('CustomIconTint','FFFFFF')]:
            xpath=target+f'/property[@name="{prop}"]'
            if base.xpath(xpath):E.SubElement(root,'set',xpath=xpath+'/@value').text=val
            else:E.SubElement(E.SubElement(root,'append',xpath=target),'property',name=prop,value=val)
        report.append(dict(id=n,icon=str(icon.relative_to(ROOT)),size=im.size))
    path.write_bytes(E.tostring(root,pretty_print=True))
(ROOT/'artifacts/batch-02/icon-coverage.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS',len(report),'player-visible custom icons')
