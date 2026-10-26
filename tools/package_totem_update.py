from pathlib import Path
from datetime import datetime
import json,hashlib,os,shutil,csv
R=Path(__file__).resolve().parents[1]
B=Path(json.loads((R/'dist/active-playtest-release.json').read_text())['release'])
N=R/'dist'/('Delve-TotemHex-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
m=json.loads((B/'manifest.json').read_text())
for e in m['files']:
 assert sha(B/e['path'])==e['sha256'],e['path']
N.mkdir()
for p in B.rglob('*'):
 if p.is_file():
  dest=N/p.relative_to(B);dest.parent.mkdir(parents=True,exist_ok=True)
  if p.name in ['manifest.json','START-HERE.txt','VALIDATION.txt'] or p.relative_to(B).as_posix()=='Mods/Delve/Delve.dll':shutil.copy2(p,dest)
  else:os.link(p,dest)
shutil.copy2(R/'src/Delve/Delve.dll',N/'Mods/Delve/Delve.dll')
mod=R/'src/ZZZZZZZZZZZZZZZZDelveTotemHex'
(mod/'Config').mkdir(parents=True,exist_ok=True)
(mod/'ModInfo.xml').write_text('<xml><Name value="DelveTotemHex"/><DisplayName value="Delve - Totem Curse Splash"/><Version value="0.16.1"/><Author value="Delve"/></xml>')
with (mod/'Config/Localization.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english'])
 for key,text in [
 ('delveStarterTotemDesc','Field Crafting Mat starter focus; 300 durability. Uses Totem Runes. Impact damage increased 15%; decay deals 12 base damage over 5 seconds. A hit splashes nearby enemies within 1.5m for 4 damage and spreads the 20% slow and 15% weakening curse. Walls block splash; curses refresh rather than stack.'),
 ('delveForgedTotemDesc','Carpentry 20. Forged hex focus. Impact damage increased 15%; decay deals 12 base damage over 5 seconds. A hit splashes nearby enemies within 1.5m for 6 damage and spreads the 20% slow and 15% weakening curse for 6 seconds. Walls block splash; curses refresh rather than stack. Repair with Focus Repair Supplies.')]:w.writerow([key,'Delve','','','',text])
shutil.copytree(mod,N/'Mods'/mod.name)
notes='TOTEM CURSE UPDATE 0.16.1\n15% increased offensive totem impact damage; 12 base decay damage over 5 seconds. Successful hits spread a curse in a 1.5m radius: 4 starter / 6 Forged splash damage, slow and weaken. Enemy-only secondary targets, line-of-sight required, no recursive splash. Existing rune costs and refresh behavior preserved.\nBuilt on the complete Batch10 release. Close the game and use Play-First-Forest.cmd to install and play.\n'
(N/'START-HERE.txt').write_text(notes+'\n'+(B/'START-HERE.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
e=N/'Evidence/TotemHex';e.mkdir(parents=True)
for f in ['totem-hex-results.txt','first-tier-results.txt']:shutil.copy2(R/'artifacts/tests'/f,e/f)
shutil.copy2(R/'artifacts/validation/forged-rules.txt',e/'forged-rules.txt')
(N/'VALIDATION.txt').write_text(notes+'\nCompiled against installed game assemblies. PASS 197 rule checks. Human combat feel, controller aiming and remote-client splash remain playtest checks.\n'+(B/'VALIDATION.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
m.update(version='0.16.1-totemhex')
m['files']=[dict(path=p.relative_to(N).as_posix(),sha256=sha(p)) for p in sorted(N.rglob('*')) if p.is_file() and p.name!='manifest.json']
(N/'manifest.json').write_text(json.dumps(m,indent=2))
(R/'artifacts/totem-release.txt').write_text(str(N))
print(N)
