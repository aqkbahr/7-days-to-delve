"""Emit immutable reference transforms for native-controller retargeting."""
from pathlib import Path
import json, shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'src/ZDelvePresentation/Resources'
OUT.mkdir(parents=True,exist_ok=True)
entries=[]
for path in sorted((ROOT/'src/Art/ForestEnemies').glob('*/rig-contract.json')):
    entries.append((path,path.parent.name.lower(),ROOT/'artifacts/forest-enemies/Bundle'))
for name in ('delveHellhound','delveGloomcat','delveCrystalStag','delveThornbackBoar'):
    entries.append((ROOT/'src/Art'/name/'rig-contract.json','thornback' if name=='delveThornbackBoar' else name.lower(),ROOT/'artifacts'/('thornback' if name=='delveThornbackBoar' else 'forest-quadrupeds')/'Bundle'))
q=json.dumps
lines=['using System;using System.Collections.Generic;using UnityEngine;namespace DelvePresentation { public static class EnemyRigs {',
'public static readonly Dictionary<string,string> Bundles=new Dictionary<string,string>{']
for path,bundle,folder in entries:
    shutil.copy2(folder/(bundle+'.unity3d'),OUT)
    lines.append('{'+q(path.parent.name)+','+q(bundle)+'},')
lines+=['};','sealed class Bone {public string Parent;public Matrix4x4 Local;}','public static Dictionary<string,Matrix4x4> Build(string id){var input=new Dictionary<string,Bone>();switch(id){']
def vec(values,typename):return 'new '+typename+'('+','.join(format(float(v),'.9g')+'f' for v in values)+')'
for path,bundle,folder in entries:
    lines.append('case '+q(path.parent.name)+':')
    for name,bone in json.loads(path.read_text()).items():
        lines.append('input.Add('+q(name)+',new Bone{Parent='+q(bone['parent'])+',Local=Matrix4x4.TRS('+vec(bone['pos'],'Vector3')+','+vec(bone['rot'],'Quaternion')+','+vec(bone.get('scale',[1,1,1]),'Vector3')+')});')
    lines.append('break;')
lines+=['default:throw new ArgumentException(id);}','var result=new Dictionary<string,Matrix4x4>();foreach(string name in input.Keys)Resolve(name,input,result);return result;}',
'static Matrix4x4 Resolve(string name,Dictionary<string,Bone> input,Dictionary<string,Matrix4x4> result){Matrix4x4 value;if(result.TryGetValue(name,out value))return value;var b=input[name];value=(input.ContainsKey(b.Parent)?Resolve(b.Parent,input,result):Matrix4x4.identity)*b.Local;result.Add(name,value);return value;}','}}']
(ROOT/'src/Art/EnemyRigs.generated.cs').write_text('\n'.join(lines))
print('Generated reference rigs:',len(entries))

