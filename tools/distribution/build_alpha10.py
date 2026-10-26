"""Freeze the selected release; never rebuild or rename compatibility-sensitive content."""
from pathlib import Path
import argparse, hashlib, json, shutil, zipfile

ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()

def build(base, output):
    old = json.loads((base/'manifest.json').read_text(encoding='utf-8-sig'))
    runtime = {e['path']: e for e in old['files'] if e['path'].startswith(('Mods/', 'Worlds/'))}
    disk = {p.relative_to(base).as_posix() for folder in ['Mods','Worlds'] for p in (base/folder).rglob('*') if p.is_file()}
    assert disk == set(runtime), 'Runtime files differ from baseline manifest'
    assert not output.exists(), 'Use a new output directory; never overwrite a published package'
    for path, entry in runtime.items():
        assert sha(base/path) == entry['sha256'], f'Baseline hash mismatch: {path}'
    output.mkdir(parents=True)
    for path in sorted(runtime):
        target=output/path; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(base/path,target)
        assert sha(target) == runtime[path]['sha256']
    for name in ['Play-Delve.cmd','Play-Delve.ps1','Verify-Package.ps1','Hash-File.ps1']:
        shutil.copy2(ROOT/'tools/distribution'/name,output/name)
    shutil.copy2(ROOT/'docs/alpha-10-install.txt',output/'START-HERE.txt')
    # Small gameplay references remain available; private testing evidence stays local.
    guides=['CRAFTING-GUIDE.txt','CRAFTING-STATIONS.txt','STATION-UPGRADES.txt',
            'RECRUITMENT.txt','RESURRECTION.txt','SUMMONING.txt','SUMMONING20.txt',
            'RECIPE-LEARNING.txt','SKILL-COVERAGE.txt','ACCESS-GUIDE.txt','TOMES.txt']
    for name in guides:
        if (base/name).exists():
            target=output/'Guides'/name;target.parent.mkdir(exist_ok=True)
            text=(base/name).read_text(encoding='utf-8-sig')
            # Historical guide commands refer to the local development launcher.
            text=text.replace('Play-First-Forest.cmd','Play-Delve.cmd')
            target.write_text('Alpha .10 reference. Earlier version labels below describe feature history.\n'
                              'Use START-HERE.txt for installation and supported game version.\n\n'+text,encoding='utf-8')
    manifest={k:v for k,v in old.items() if k not in ['files','name','version','acceptance']}
    manifest.update(name='7 Days to Delve',version='alpha.10',displayVersion='Alpha .10',
                    worldName=(base/'world-name.txt').read_text(encoding='utf-8-sig').strip(),
                    baselineVersion=old['version'],baselineManifestSha256=sha(base/'manifest.json'),
                    compatibility='Runtime Mods and Worlds are byte-identical to the selected 0.18.1 baseline; internal IDs and load order preserved.',
                    validation='Distribution hash parity and installer tests; inherited runtime evidence retained locally. No new human multiplayer acceptance claimed.')
    manifest['files']=[dict(path=p.relative_to(output).as_posix(),sha256=sha(p),size=p.stat().st_size)
                       for p in sorted(output.rglob('*')) if p.is_file()]
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    archive=output.with_suffix('.zip')
    assert not archive.exists()
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
        for p in sorted(output.rglob('*')):
            if p.is_file():z.write(p,output.name+'/'+p.relative_to(output).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for entry in manifest['files']:
            assert hashlib.sha256(z.read(output.name+'/'+entry['path'])).hexdigest().upper()==entry['sha256']
    checksum=sha(archive)
    Path(str(archive)+'.sha256').write_text(checksum+'  '+archive.name+'\n',encoding='ascii')
    report=dict(version='alpha.10',baseline=str(base),runtimeFiles=len(runtime),modCount=len(list((output/'Mods').iterdir())),
                runtimeBytes=sum((base/p).stat().st_size for p in runtime),
                baselineBytes=sum(p.stat().st_size for p in base.rglob('*') if p.is_file()),
                packageBytes=sum(p.stat().st_size for p in output.rglob('*') if p.is_file()),
                downloadBytes=archive.stat().st_size,sha256=checksum,archive=str(archive),allRuntimeHashesPreserved=True)
    evidence=ROOT/'artifacts/alpha10';evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'distribution-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    base=args.base or Path((ROOT/'dist/latest-first-forest-release.txt').read_text(encoding='utf-8-sig').strip())
    build(base,args.output or ROOT/'dist/Delve-Alpha-10')
