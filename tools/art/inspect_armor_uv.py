import bpy,os,json,collections
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'src/Art/ForestArmor/Light.blend'))
o=bpy.data.objects['Outfit_LOD0'];out={}
for p in o.data.polygons:
 c=p.center;key='torso' if abs(c.x)<.15 and c.z>1.1 else 'leftleg' if c.x<0 and c.z<.8 else 'rightleg' if c.x>0 and c.z<.8 else 'arm' if abs(c.x)>.24 and c.z>1.1 else 'other'
 counter=out.setdefault(key,collections.Counter())
 for i in p.loop_indices:
  uv=o.data.uv_layers.active.data[i].uv;counter[str((int(uv.x*4),int(uv.y*4)))]+=1
json.dump(out,open(os.path.join(root,'artifacts/forest-armor/uv-diagnostic.json'),'w'),indent=2)
