"""Original Forest quadruped art; Blender background script. No native meshes/clips."""
import bpy, math, random, json, os, re, sys, ast
import numpy as np
from mathutils import Vector, Matrix, Quaternion
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
IDS=['delveHellhound','delveGloomcat','delveCrystalStag']
# Reuse only our original primitive/UV helpers, without running Thornback's build.
tree=ast.parse(open(os.path.join(ROOT,'tools/art/build_thornback.py')).read())
helpers=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('finish','ell','tube')],type_ignores=[])
exec(compile(helpers,'original_geometry_helpers','exec'))
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))

def build(entity):
 global mat,parts
 random.seed(81+IDS.index(entity));dog=entity==IDS[0];cat=entity==IDS[1];stag=entity==IDS[2]
 out=os.path.join(ROOT,'src/Art',entity);os.makedirs(out,exist_ok=True)
 # Remove hidden LOD objects too; operator selection skips hidden objects.
 for old in list(bpy.data.objects):bpy.data.objects.remove(old,do_unlink=True)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.render.fps=30
 nodes={}
 for line in open(os.path.join(ROOT,'artifacts/forest-quadrupeds/InspectProfile',entity+'-rig.txt')):
  m=re.match(r'NODE (\S+) parent=(\S+) pos=\(([^)]+)\) rot=\(([^)]+)\)',line)
  if m:
   n,p,xyz,q=m.groups();nodes[n]={'parent':p,'pos':[float(v) for v in xyz.split(',')],'rot':[float(v) for v in q.split(',')]}
 names=[]
 for n in nodes:
  p=n
  while p in nodes and p!='Origin':p=nodes[p]['parent']
  if p=='Origin':names.append(n)
 native={};points={}
 for n in names:
  d=nodes[n];x,y,z,w=d['rot'];local=Matrix.Translation(Vector(d['pos']))@Quaternion((w,x,y,z)).to_matrix().to_4x4()
  native[n]=native[d['parent']]@local if d['parent'] in native else local;points[n]=(C@native[n]).translation
 bpy.ops.object.armature_add(enter_editmode=True);rig=bpy.context.object;rig.name=entity+'_Rig';rig.data.edit_bones.remove(rig.data.edit_bones[0])
 for n in names:
  b=rig.data.edit_bones.new(n);basis=C@native[n];b.head=basis.translation;b.tail=b.head+basis.to_3x3()@Vector((0,.06,0));b.align_roll(basis.to_3x3()@Vector((0,0,1)))
  if nodes[n]['parent'] in names:b.parent=rig.data.edit_bones[nodes[n]['parent']]
 bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
 base=(.105,.085,.075) if dog else (.14,.12,.19) if cat else (.34,.28,.19)
 colors=[base,(.055,.045,.045) if dog else (.20,.16,.27) if cat else (.43,.38,.27),(.68,.61,.46),(.035,.027,.024),(.85,.24,.045) if dog else (.50,.53,.25) if cat else (.12,.36,.41),(.23,.08,.035) if dog else (.10,.075,.14) if cat else (.23,.46,.50),(.28,.15,.12),(.075,.04,.025),(.09,.08,.075),(.24,.14,.09),(.64,.77,.73),(.025,.02,.02),(.01,.008,.008),(.34,.24,.41),(.14,.24,.25),(.53,.45,.31)]
 N=2048;cell=512;pixels=np.ones((N,N,4),np.float32);rng=np.random.default_rng(82);yy,xx=np.mgrid[0:cell,0:cell];u=xx/cell;v=yy/cell
 for i,color in enumerate(colors):
  grain=rng.normal(0,.012,(cell,cell))+.012*np.sin(u*250+np.sin(v*30))
  if cat and i in (0,1):grain-=.045*(np.sin(u*41+np.cos(v*21))*np.sin(v*39)>.52)
  if dog and i==0:grain+=.012*np.cos(u*75+v*15)
  tile=np.clip(np.array(color)[None,None,:]+grain[:,:,None],.004,.95);row,col=divmod(i,4);pixels[row*cell:(row+1)*cell,col*cell:(col+1)*cell,:3]=tile
 teximage=bpy.data.images.new(entity+'_Albedo',width=N,height=N);teximage.pixels.foreach_set(pixels.ravel());teximage.filepath_raw=os.path.join(out,'Albedo.png');teximage.file_format='PNG';teximage.save();teximage.pack()
 mat=bpy.data.materials.new(entity+'_Surface');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.8
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=teximage;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);parts=[]
 masses=[]
 def mass(name,p,scale):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=p);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);masses.append(o);return o
 def capsule(name,a,b,r1,r2):
  steps=max(3,int((b-a).length/(.018 if stag else .04)))
  for i in range(steps+1):
   t=i/steps;r=r1*(1-t)+r2*t;mass(name,a.lerp(b,t),(r,r,r))
 hip=points['Hips'];head=points['Head'];spine=points['Spine'];front=points['Spine1' if dog else 'Spine2']
 mass('Ribcage',spine+Vector((0,0,-.055)),(.16 if dog else .175 if cat else .17,.31,.22 if dog else .19 if cat else .23))
 mass('Tucked waist',hip.lerp(spine,.42),(.115 if dog else .145,.22,.13 if dog else .16))
 mass('Haunches',hip,(.15 if dog else .18,.19,.19))
 mass('Shoulders',front,(.16 if dog else .18 if cat else .15,.19,.21 if dog else .17 if cat else .22))
 capsule('Neck',front,head,.125 if dog else .14 if cat else .12,.10 if dog else .13 if cat else .09)
 mass('Skull',head+Vector((0,-.035,0)),(.11 if dog else .145 if cat else .09,.13,.125 if dog else .12))
 nose=points.get('Nose',head+Vector((0,-.2,-.04)))
 if dog:nose=head+Vector((0,-.22,-.09))
 if cat:nose=head+Vector((0,-.16,-.025))
 capsule('Muzzle',head+Vector((0,-.09,-.045)),nose,.072 if dog else .09 if cat else .065,.05 if dog else .065 if cat else .05)
 jawbone='Jaw' if dog else 'Mandible'
 mass('Lower jaw',(head+nose)/2+Vector((0,0,-.075)),(.065,.13 if dog or stag else .08,.035))
 segments=[];legchains=[]
 for side in ('Left','Right'):
  fore=[side+n for n in (['UpForeleg','ForeLeg','ForeWrist','ForePaw'] if dog else ['Arm','ForeArm','Hand','HandFingers'])]
  hind=[side+n for n in (['UpLeg','Leg','Ankle','HindPaw'] if dog else ['UpLeg','Leg','Foot','ToeBase'])]
  for chain in (fore,hind):
   legchains.append(chain)
   for i in range(len(chain)-1):
    a,b=points[chain[i]],points[chain[i+1]];r=(.09 if i==0 else .043) if not stag else (.072 if i==0 else .041)
    capsule('Limb',a,b,r,r*(.88 if stag else .68));segments.append((chain[i],a,b))
   end=points[chain[-1]];mass('Foot join',end+Vector((0,-.015,0)),(.05 if stag else .068,.07 if stag else .095,.055))
   segments.append((chain[-1],end,end+Vector((0,-.08,0))))
 # Fuse the anatomical masses into a single continuous hide.
 bpy.ops.object.select_all(action='DESELECT')
 for o in masses:o.select_set(True)
 bpy.context.view_layer.objects.active=masses[0];bpy.ops.object.join();body=bpy.context.object;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 mod=body.modifiers.new('Continuous anatomy','REMESH');mod.mode='VOXEL';mod.voxel_size=.012 if stag else .022;bpy.ops.object.modifier_apply(modifier=mod.name)
 mod=body.modifiers.new('Sculpt smoothing','SMOOTH');mod.factor=1;mod.iterations=3 if stag else 4;bpy.ops.object.modifier_apply(modifier=mod.name)
 mod=body.modifiers.new('Retopology','DECIMATE');mod.ratio=min(1,6800/max(1,len(body.data.polygons)));bpy.ops.object.modifier_apply(modifier=mod.name)
 finish(body,0)
 torso=[n for n in ['Hips','LowerBack','Spine','Spine1','Spine2','Neck','Neck1','Neck2','Neck3','Head'] if n in points]
 for i,n in enumerate(torso):segments.append((n,points[n],points[torso[i+1]] if i+1<len(torso) else nose))
 groups={n:body.vertex_groups.new(name=n) for n in names}
 for vertex in body.data.vertices:
  scored=[]
  for n,a,b in segments:
   ab=b-a;t=max(0,min(1,(vertex.co-a).dot(ab)/max(ab.length_squared,1e-8)));dist=(vertex.co-a-t*ab).length
   scored.append((n,1/(dist+.035)**5))
  merged={}
  for n,w in scored:merged[n]=merged.get(n,0)+w
  best=sorted(merged.items(),key=lambda p:p[1],reverse=True)[:4];total=sum(w for n,w in best)
  for n,w in best:groups[n].add([vertex.index],w/total,'REPLACE')
 # Feet, facial features and original silhouette attachments.
 for chain in legchains:
  p=points[chain[-1]]
  if stag:
   for sign in (-1,1):ell('Cloven hoof',p+Vector((sign*.023,-.025,-.015)),(.021,.065,.045),3,chain[-1],12,8)
  else:
   ell('Paw',p+Vector((0,-.035,-.01)),(.075 if cat else .065,.10,.047),1,chain[-1])
   for j in range(3):
    q=p+Vector(((j-1)*.033,-.09,-.01));ell('Toe',q,(.024,.04,.027),0,chain[-1],12,8)
    if dog:tube('Claw',[q,q+Vector((0,-.04,-.01))],[.012,.001],2,chain[-1],6)
 ell('Nose',nose+Vector((0,-.025,0)),(.049 if dog or stag else .05,.032,.03),3,'Head')
 for sign,side in [(-1,'Left'),(1,'Right')]:
  eye=head+Vector((sign*(.10 if dog else .126 if cat else .082),-.06,.035));ell('Socket',eye,(.026,.04,.023),3,'Head',16,10);ell('Iris',eye+Vector((sign*.014,-.008,0)),(.012,.025,.014),4,'Head',16,10);ell('Pupil',eye+Vector((sign*.023,-.012,0)),(.005,.009,.012),12,'Head',12,8)
  earbone=side+('Ear1' if cat else 'Ear');ear=head+Vector((sign*.085,0,.10))
  tip=ear+Vector((sign*(.15 if stag else .045),.02,.10 if stag else .14 if dog else .07))
  tube('Ear',[ear,(ear+tip)/2,tip],[.055,.04,.001],0,earbone,8)
  tube('Inner ear',[ear+Vector((0,-.012,.015)),(ear+tip)/2+Vector((0,-.023,0)),tip-Vector((0,0,.015))],[.032,.025,.001],6,earbone,7)
  if not stag:
   for j in range(3):
    q=head+Vector((sign*.065,-.12-j*.032,-.055));tube('Fang',[q,q+Vector((0,0,-.045 if j==0 else -.023))],[.012,.001],2,'Head',7)
  if cat:
   for j in range(4):
    q=head+Vector((sign*.115,.035,-.025-j*.018));tube('Ragged cheek tuft',[q,q+Vector((sign*.10,.07,-.065))],[.035,.001],1,'Head',6)
 if dog:
  for j in range(11):
   t=j/10;p=hip.lerp(front,t)+Vector((0,0,.13));bone=min(torso[:4],key=lambda n:(points[n]-p).length)
   h=random.uniform(.13,.25);p.x=random.uniform(-.035,.035)
   tube('Broken obsidian mane',[p,p+Vector((.015,.03,h*.5)),p+Vector((random.uniform(-.05,.05),.10,h))],[.045,.025,.001],1,bone,7)
  for sign in (-1,1):
   for j in range(5):
    p=spine+Vector((sign*.145,-.12+j*.075,.07));tube('Scorched rib ridge',[p,p+Vector((sign*.024,.01,-.08)),p+Vector((sign*.008,.035,-.14))],[.014,.016,.004],8,'Spine',7)
    tube('Dull heat seam',[p+Vector((sign*.009,-.012,0)),p+Vector((sign*.021,.005,-.08))],[.004,.002],5,'Spine',5)
  tail=points.get('Tail',hip);tube('Tapered tail',[tail,tail+Vector((0,.18,-.08)),tail+Vector((0,.33,-.20))],[.05,.032,.003],0,'Tail',10)
 if cat:
  tails=[n for n in names if re.match(r'^Tail\d+$',n)]
  if not tails:tails=[n for n in names if n.startswith('Tail')]
  for i,n in enumerate(tails[:-1]):tube('Long feline tail',[points[n],points[tails[i+1]]],[max(.012,.035-i*.003),max(.008,.032-i*.003)],0,n,10)
  if tails:
   p=points[tails[-1]]
   for sign in (-1,1):tube('Split tail tip',[p,p+Vector((sign*.045,.10,-.015))],[.018,.001],1,tails[-1],8)
 if stag:
  for sign in (-1,1):
   basep=head+Vector((sign*.065,.015,.10));antler=[basep,basep+Vector((sign*.10,.06,.21)),basep+Vector((sign*.18,.15,.40)),basep+Vector((sign*.24,.23,.57))]
   tube('Mineral antler beam',antler,[.038,.033,.023,.001],5,'Head',6)
   for j in range(1,3):
    p=antler[j];tube('Branching crystal tine',[p,p+Vector((sign*.09,-.10,.12)),p+Vector((sign*.12,-.14,.24))],[.025,.018,.001],10,'Head',5)
   for j in range(4):
    p=front+Vector((sign*(.11+j*.014),j*.03,.14));tube('Shoulder crystal',[p,p+Vector((sign*.04,.04,.12+j*.014))],[.028,.001],5,'Spine2',5)
  tail=points['Tail1'];tube('Short deer tail',[tail,tail+Vector((0,.08,-.14))],[.05,.004],15,'Tail1',9)
 # One material, three skinned LOD meshes.
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join();mesh=bpy.context.object;mesh.name='Creature_LOD0';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 modifier=mesh.modifiers.new('Skin','ARMATURE');modifier.object=rig;mesh.parent=rig;lods=[mesh]
 for level,ratio in [(1,.5),(2,.2)]:
  o=mesh.copy();o.data=mesh.data.copy();bpy.context.collection.objects.link(o);o.name='Creature_LOD'+str(level)
  for m in list(o.modifiers):o.modifiers.remove(m)
  bpy.context.view_layer.objects.active=o;m=o.modifiers.new('LOD','DECIMATE');m.ratio=ratio;bpy.ops.object.modifier_apply(modifier=m.name);m=o.modifiers.new('Skin','ARMATURE');m.object=rig;lods.append(o)
 clips={'Idle':(4,True),'Walk':(1,True),'Run':(.8,True),'TurnLeft':(1,True),'TurnRight':(1,True),'Alert':(1.1,False),'Hit':(.6,False),'Death':(.9,False),'Corpse':(1,True),'Sleep':(3,True),'Wake':(1.3,False)}
 clips.update({'Graze':(3,True),'Startle':(.6,False),'Flee':(.7,True)} if stag else {'Attack':(.5,False),'AttackRunning':(.6,False),'Recovery':(1,False)})
 if cat:clips.update({'Stalk':(1.5,True),'PounceTakeoff':(.4,False),'PounceAir':(.6,True),'PounceLand':(.4,False)})
 def rotate(n,x=0,y=0,z=0):
  if n in rig.pose.bones:rig.pose.bones[n].rotation_euler=(math.radians(x),math.radians(y),math.radians(z))
 for name,(duration,loop) in clips.items():
  action=bpy.data.actions.new(name);action.use_fake_user=True;action['loop']=loop;rig.animation_data_create();rig.animation_data.action=action;last=round(duration*30)
  for f in range(last+1):
   scene.frame_set(f+1);q=f/last;wave=math.sin(q*2*math.pi);pulse=math.sin(q*math.pi)
   for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
   if name!='Corpse':rotate('Head',2*wave);rotate('Tail' if dog else 'Tail1',0,6*wave);rotate('LeftEar1' if cat else 'LeftEar',0,0,4*wave)
   if name in ('Walk','Run','Flee','Stalk','AttackRunning'):
    fast=name in ('Run','Flee','AttackRunning');amp=30 if fast else 14
    for i,chain in enumerate(legchains):
     phase=q*2*math.pi+(0 if i in (0,3) else math.pi);sign=1 if chain[0].startswith('Left') else -1
     rotate(chain[0],sign*amp*math.sin(phase));rotate(chain[1],-sign*amp*.9*max(0,-math.sin(phase)));rotate(chain[2],sign*amp*.4*math.sin(phase))
    rotate('Spine',3*math.sin(q*4*math.pi));rig.pose.bones['Hips'].location.y=.012*math.sin(q*4*math.pi)
   if name in ('TurnLeft','TurnRight'):rotate('Head',0,18*(1 if name=='TurnLeft' else -1),0);rotate('Spine',0,5*wave)
   if name in ('Alert','Startle'):rotate('Head',-15*pulse);rotate('Neck1',-8*pulse)
   if name in ('Attack','AttackRunning'):rotate('Head',-24*pulse);rotate(jawbone,18*pulse);rotate('Spine1',-7*pulse)
   if name=='Recovery':rotate('Head',10*pulse);rotate(jawbone,6*pulse)
   if name=='Hit':rotate('Head',8*pulse,0,-16*pulse)
   if name=='Graze':rotate('Neck1',35+4*wave);rotate('Neck2',20);rotate('Head',20+2*wave)
   if name in ('PounceTakeoff','PounceAir','PounceLand','Stalk'):
    crouch=(1-q) if name=='PounceTakeoff' else q if name=='PounceLand' else .3
    rig.pose.bones['Hips'].location.y=-.10*crouch;rotate('Head',-8)
    for i,chain in enumerate(legchains):rotate(chain[0],(1 if i<2 else -1)*(25*crouch+4*wave));rotate(chain[1],(1 if i<2 else -1)*-35*crouch)
   if name in ('Death','Corpse'):
    t=1 if name=='Corpse' else min(1,q*1.4);rotate('Hips',0,0,85*t);rig.pose.bones['Hips'].location.y=-hip.z*.65*t;rotate('Head',18*t)
    for i,chain in enumerate(legchains):rotate(chain[0],(1 if i<2 else -1)*20*t)
   if name in ('Sleep','Wake'):
    t=1 if name=='Sleep' else 1-q;rig.pose.bones['Hips'].location.y=-hip.z*.45*t;rotate('Head',16*t+wave)
    for i,chain in enumerate(legchains):rotate(chain[0],(1 if i<2 else -1)*35*t);rotate(chain[1],(1 if i<2 else -1)*-65*t)
   for b in rig.pose.bones:
    b.keyframe_insert('rotation_euler',frame=f+1,group=b.name);b.keyframe_insert('location',frame=f+1,group=b.name)
 rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_start=1;scene.frame_end=121;scene.frame_set(1)
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in lods:o.select_set(True)
 bpy.context.view_layer.objects.active=rig;bpy.ops.export_scene.fbx(filepath=os.path.join(out,entity+'.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
 counts={}
 for o in lods:o.data.calc_loop_triangles();counts[o.name]=len(o.data.loop_triangles)
 for o in lods[1:]:o.hide_render=True;o.hide_set(True)
 world=bpy.data.worlds.new(entity+'_Studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.23,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
 for label,loc,power in [('Key',(2,-3,4),700),('Rim',(-2,2,3),600)]:
  d=bpy.data.lights.new(label,'AREA');d.energy=power;d.shape='DISK';d.size=4;o=bpy.data.objects.new(label,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,-.25,.65))-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',d);bpy.context.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=2.7 if stag else 2.3;cam.location=(2.5,-3.5,1.9);cam.rotation_euler=(Vector((0,-.25,.8 if stag else .55))-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,entity+'.blend'))
 json.dump({'entity':entity,'status':'authored first pass; gameplay acceptance deferred','native_geometry_copied':False,'rig_bones':len(names),'triangles':counts,'animations':{n:{'seconds':d,'loop':l} for n,(d,l) in clips.items()},'texture':'Albedo.png','texture_size':2048},open(os.path.join(out,'asset-manifest.json'),'w'),indent=2)
 json.dump({n:nodes[n] for n in names},open(os.path.join(out,'rig-contract.json'),'w'),indent=2)
 open(os.path.join(out,'PROVENANCE.txt'),'w').write('Original project-authored geometry, texture atlas, weights and animation curves. Native skeleton transform metadata used only for fitting. No native mesh, texture or animation copied. Generator: tools/art/build_forest_quadrupeds.py; original geometry helpers from build_thornback.py. Gameplay and live-ragdoll integration pending.\n')
 print('FOREST_BUILD_PASS',entity,counts,flush=True)
requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else IDS
for entity in requested:
 if entity not in IDS:raise ValueError('Unknown creature '+entity)
 build(entity)
