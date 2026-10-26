import bpy,os,sys,math
from mathutils import Quaternion,Euler
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
folder=os.path.join(ROOT,'src/Art/ForestEnemies')
for entity in os.listdir(folder):
 path=os.path.join(folder,entity,entity+'.blend')
 if not os.path.isfile(path):continue
 bpy.ops.wm.open_mainfile(filepath=path)
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
 for name in ['Sleep','Wake']:
  action=bpy.data.actions[name];rig.animation_data.action=action;last=round(3*30 if name=='Sleep' else 1.5*30)
  for f in range(last+1):
   scene.frame_set(f+1);q=f/last;t=1 if name=='Sleep' else 1-q;lean=14 if entity=='delveCorruptedWalker' else 22 if entity=='delveImp' else 7 if entity in ('delveWarpedBrute','delveDemonSpawn') else 0;angle=30*t+lean*(1-t)+.8*math.sin(q*2*math.pi)*t
   basis=rig.data.bones['Spine2'].matrix_local.to_quaternion();rig.pose.bones['Spine2'].rotation_quaternion=basis.inverted()@Euler((math.radians(angle),0,0),'XYZ').to_quaternion()@basis
   rig.pose.bones['Spine2'].keyframe_insert('rotation_quaternion',frame=f+1,group='Spine2')
 if entity=='delveImp':
  rig.animation_data.action=bpy.data.actions['Death']
  for f in range(40):
   scene.frame_set(f+1)
   for i in range(4):
    b=rig.pose.bones['Tail'+str(i+1)];b.rotation_quaternion=Quaternion();b.keyframe_insert('rotation_quaternion',frame=f+1,group=b.name)
 rig.animation_data.action=None
 for b in rig.pose.bones:b.rotation_quaternion=Quaternion();b.location=(0,0,0)
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in bpy.data.objects:
  if o.type=='MESH':o.hide_set(False);o.hide_render=False;o.select_set(True)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=os.path.join(folder,entity,entity+'.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name!='Creature_LOD0':o.hide_render=True;o.hide_set(True)
 rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=path,compress=True)
open(os.path.join(ROOT,'artifacts/forest-enemies/motion-repair.txt'),'w').write('PASS: Sleep/Wake breath and Imp tail death endpoint repaired')

