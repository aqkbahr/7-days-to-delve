"""Installer safety tests using tiny synthetic packages, never the live game/save."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]

class InstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=ROOT/'artifacts/alpha10';root.mkdir(parents=True,exist_ok=True)
        cls.root=Path(tempfile.mkdtemp(prefix='installer-tests-',dir=root))

    def setUp(self):
        self.case=self.root/self._testMethodName;self.case.mkdir()
        self.package=self.case/'package';self.package.mkdir()
        self.game=self.case/'game';self.profile=self.case/'profile'
        for name,data in [('7DaysToDie.exe',b''),('7DaysToDie_Data/Managed/Assembly-CSharp.dll',b'test-api'),('Mods/0_TFP_Harmony/ModInfo.xml',b'<xml/>')]:
            p=self.game/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        for name in ['Play-Delve.ps1','Verify-Package.ps1','Hash-File.ps1']:
            shutil.copy2(ROOT/'tools/distribution'/name,self.package/name)
        for name,data in [('Mods/Delve/ModInfo.xml',b'<xml/>'),('Mods/Delve/test.dat',b'new-runtime'),('Worlds/Allium-v0.10/dtm.raw',b'test-terrain')]:
            p=self.package/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        self.write_manifest()

    def write_manifest(self):
        m=dict(version='alpha.10',displayVersion='Alpha .10',gameVersion='synthetic test',worldName='Allium-v0.10',
               gameAssemblySha256=hashlib.sha256(b'test-api').hexdigest(),files=[])
        for p in self.package.rglob('*'):
            if p.is_file() and p.name not in ['manifest.json','launcher-settings.local.json']:
                m['files'].append(dict(path=p.relative_to(self.package).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        (self.package/'manifest.json').write_text(json.dumps(m))

    def run_install(self,ok=True):
        env=os.environ.copy()
        # A Python child of PowerShell 7 can inherit its incompatible module path.
        # Simulate the normal CMD launcher by letting Windows PowerShell choose it.
        env.pop('PSModulePath',None)
        result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(self.package/'Play-Delve.ps1'),
                               '-GamePath',str(self.game),'-DataPath',str(self.profile),'-InstallOnly'],capture_output=True,text=True,env=env)
        self.assertEqual(result.returncode==0,ok,result.stdout+result.stderr)
        return result

    def test_fresh_and_repeat_install(self):
        self.run_install();self.run_install()
        self.assertEqual((self.profile/'Mods/Delve/test.dat').read_bytes(),b'new-runtime')
        self.assertFalse((self.profile/'Backups').exists(),'Repeated play must not create duplicate backups')
        self.assertIn(str(self.profile),(self.profile/'Steam-launch-options.txt').read_text(encoding='utf-8-sig'))

    def test_update_preserves_saves_and_removes_stale_mod_files(self):
        self.run_install()
        saved=self.profile/'Saves/Allium-v0.10/MyWorld/player.dat';saved.parent.mkdir(parents=True);saved.write_bytes(b'precious-save')
        old=self.profile/'Mods/Delve/test.dat';old.write_bytes(b'previous-runtime')
        (old.parent/'obsolete.txt').write_bytes(b'obsolete')
        self.run_install()
        self.assertEqual(saved.read_bytes(),b'precious-save')
        self.assertFalse((old.parent/'obsolete.txt').exists())
        self.assertEqual(next((self.profile/'Backups').glob('*/Delve/test.dat')).read_bytes(),b'previous-runtime')

    def test_corrupt_download_refused_before_install(self):
        (self.package/'Mods/Delve/test.dat').write_bytes(b'corrupt')
        self.run_install(False);self.assertFalse(self.profile.exists())

    def test_wrong_game_refused(self):
        (self.game/'7DaysToDie_Data/Managed/Assembly-CSharp.dll').write_bytes(b'wrong-api')
        self.run_install(False);self.assertFalse(self.profile.exists())

    def test_different_world_preserved(self):
        self.run_install();p=self.profile/'GeneratedWorlds/Allium-v0.10/dtm.raw';p.write_bytes(b'other-map')
        self.run_install(False);self.assertEqual(p.read_bytes(),b'other-map')

    def test_unknown_mod_preserved(self):
        p=self.profile/'Mods/OtherMod/ModInfo.xml';p.parent.mkdir(parents=True);p.write_bytes(b'other-mod')
        self.run_install(False);self.assertEqual(p.read_bytes(),b'other-mod')

    def test_manifest_traversal_refused(self):
        p=self.package/'manifest.json';m=json.loads(p.read_text());m['files'][0]['path']='../outside.txt';p.write_text(json.dumps(m))
        self.run_install(False);self.assertFalse(self.profile.exists())

if __name__=='__main__':unittest.main(verbosity=2)
