"""Original Thornback mesh/rig/actions. Run with Blender 5.2 in background."""
import bpy, math, random, json, os, re, sys
from mathutils import Vector, Matrix, Quaternion
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
OUT = os.path.join(ROOT, 'src/Art/delveThornbackBoar')
PREVIEW = os.path.join(ROOT, 'artifacts/thornback/previews')
os.makedirs(OUT, exist_ok=True); os.makedirs(PREVIEW, exist_ok=True)
random.seed(37)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.render.fps=30

# Reconstruct the measured native rest skeleton, never copy native geometry.
nodes={}
for line in open(os.path.join(ROOT,'artifacts/thornback/InspectProfile/native-boar.txt')):
    m=re.match(r'NODE (\S+) parent=(\S+) pos=\(([^)]+)\) rot=\(([^)]+)\)',line)
    if m:
        name,parent,pos,rot=m.groups()
        nodes[name]={'parent':parent,'pos':[float(x) for x in pos.split(',')], 'rot':[float(x) for x in rot.split(',')]}
bone_names=[]
for name,node in nodes.items():
    p=name
    while p in nodes and p!='Origin': p=nodes[p]['parent']
    if p=='Origin': bone_names.append(name)
contract={n:nodes[n] for n in bone_names}
open(os.path.join(OUT,'rig-contract.json'),'w').write(json.dumps(contract,indent=2))
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1))) # Unity XYZ -> Blender X,-Z,Y
world={}
for name in bone_names:
    n=nodes[name]; x,y,z,w=n['rot']
    local=Matrix.Translation(Vector(n['pos'])) @ Quaternion((w,x,y,z)).to_matrix().to_4x4()
    world[name]=(world[n['parent']] @ local) if n['parent'] in world else local
bpy.ops.object.armature_add(enter_editmode=True)
rig=bpy.context.object; rig.name='ThornbackRig'; rig.data.name='ThornbackSkeleton'
rig.data.edit_bones.remove(rig.data.edit_bones[0])
for name in bone_names:
    bone=rig.data.edit_bones.new(name)
    # Bone Y is the native vertical axis. This keeps native rest orientation.
    native=world[name]; basis=C @ native
    bone.head=basis.translation; bone.tail=bone.head+basis.to_3x3()@Vector((0,.065,0))
    bone.align_roll(basis.to_3x3()@Vector((0,0,1)))
    if nodes[name]['parent'] in bone_names: bone.parent=rig.data.edit_bones[nodes[name]['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front=True

# One original 2K atlas: skin, bark, ivory, hoof, eye, moss, ear, scar.
N=2048; cell=512
colors=[(.25,.20,.155),(.22,.185,.12),(.67,.59,.40),(.075,.069,.05),(.62,.34,.075),(.20,.265,.10),(.32,.20,.15),(.39,.31,.22),
        (.18,.145,.11),(.30,.25,.15),(.78,.70,.51),(.11,.105,.08),(.025,.018,.01),(.29,.32,.12),(.17,.12,.09),(.36,.29,.18)]
pixels=np.ones((N,N,4),dtype=np.float32)
rng=np.random.default_rng(37)
yy,xx=np.mgrid[0:cell,0:cell]; u=xx/cell; v=yy/cell
for i,color in enumerate(colors):
    noise=rng.normal(0,.025,(cell,cell))
    waves=.04*np.sin(u*73+np.sin(v*14)*2)+.025*np.sin(v*81+u*7)
    if i in (1,9):
        grain=np.sin(u*180+3*np.sin(v*9)+np.sin(v*39))
        waves=.026*grain+.009*np.sin(v*270); waves-=.025*(grain<-.90)
    if i in (2,10): waves=.035*np.sin(v*135)+.045*v
    if i in (0,8): waves+=.025*np.sin(u*280)*np.sin(v*260)
    tile=np.clip(np.array(color)[None,None,:]+(noise+waves)[:,:,None],.008,.95)
    row,col=divmod(i,4); pixels[row*cell:(row+1)*cell,col*cell:(col+1)*cell,:3]=tile
image=bpy.data.images.new('Thornback_Albedo',width=N,height=N)
image.pixels.foreach_set(pixels.ravel()); image.filepath_raw=os.path.join(OUT,'Thornback_Albedo.png'); image.file_format='PNG'; image.save(); image.pack()
mat=bpy.data.materials.new('Thornback_BarkHide'); mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF'); bsdf.inputs['Roughness'].default_value=.82
tex=mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=image
mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
noise=mat.node_tree.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=65
bump=mat.node_tree.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.24; bump.inputs['Distance'].default_value=.018
mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']); mat.node_tree.links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
parts=[]
def finish(o,tile=0,bone=None):
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    o.data.materials.clear(); o.data.materials.append(mat)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025); bpy.ops.object.mode_set(mode='OBJECT')
    row,col=divmod(tile,4)
    for uv in o.data.uv_layers.active.data: uv.uv=((col+.03+uv.uv.x*.94)/4,(row+.03+uv.uv.y*.94)/4)
    if bone:
        g=o.vertex_groups.new(name=bone); g.add(list(range(len(o.data.vertices))),1,'REPLACE')
    for p in o.data.polygons:p.use_smooth=True
    parts.append(o); o.select_set(False); return o
def ell(name,loc,scale,tile=0,bone=None,seg=20,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; return finish(o,tile,bone)
def tube(name,points,radii,tile,bone,sides=10):
    vs=[]; fs=[]; previous_a=None
    for i,p in enumerate(points):
        p=Vector(p); tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        tangent.normalize(); ref=Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((0,1,0))
        a=tangent.cross(ref).normalized() if previous_a is None else (previous_a-tangent*previous_a.dot(tangent)).normalized()
        previous_a=a; b=tangent.cross(a).normalized()
        for j in range(sides):
            theta=2*math.pi*j/sides; vs.append(p+radii[i]*(a*math.cos(theta)+b*math.sin(theta)))
    for i in range(len(points)-1):
        for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    fs.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))])
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vs,[],fs); mesh.update()
    o=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(o); return finish(o,tile,bone)

# Continuous body surface, fused from anatomical masses; no disconnected ball body.
body_parts=[]
for name,loc,scale in [
 ('Ribcage',(0,.10,.61),(.28,.48,.31)),('Rump',(0,.43,.57),(.245,.25,.27)),
 ('Shoulder',(0,-.16,.65),(.29,.27,.32)),('Neck',(0,-.34,.65),(.245,.23,.24)),
 ('Skull',(0,-.46,.62),(.205,.23,.22)),('Muzzle',(0,-.64,.53),(.145,.22,.125)),
 ('LowerJaw',(0,-.57,.445),(.13,.22,.065))]:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); body_parts.append(o)
for side in (-1,1):
    for y in (-.10,.48):
        for z,sx,sy,sz,dy in ((.48,.115,.14,.19,0),(.28,.065,.075,.17,.015),(.13,.055,.065,.095,0)):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,location=(side*(.17 if y<0 else .145),y+dy,z))
            o=bpy.context.object;o.scale=(sx,sy,sz);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);body_parts.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in body_parts:o.select_set(True)
bpy.context.view_layer.objects.active=body_parts[0];bpy.ops.object.join();body=bpy.context.object;body.name='Thornback_Hide'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
rem=body.modifiers.new('Anatomical fusion','REMESH');rem.mode='VOXEL';rem.voxel_size=.026;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
smooth=body.modifiers.new('Sculpt smoothing','SMOOTH');smooth.factor=1.1;smooth.iterations=4;bpy.ops.object.modifier_apply(modifier=smooth.name)
sub=body.modifiers.new('Surface refinement','SUBSURF');sub.levels=1;bpy.ops.object.modifier_apply(modifier=sub.name)
dec=body.modifiers.new('Retopology budget','DECIMATE');dec.ratio=min(1,10500/(len(body.data.polygons)*2));bpy.ops.object.modifier_apply(modifier=dec.name)
finish(body,0)
def skin_body(o):
    groups={n:o.vertex_groups.new(name=n) for n in bone_names}
    def smooth(a,b,value):
        t=max(0,min(1,(value-a)/(b-a))); return t*t*(3-2*t)
    for v in o.data.vertices:
        x,y,z=v.co; side='Left' if x<0 else 'Right'
        # Continuous anatomical masks: the low muzzle must never be assigned
        # to a front leg merely because it is below shoulder height.
        head=1-smooth(-.48,-.26,y)
        anchors=[('Hips',.45),('LowerBack',.32),('Spine',.18),('Spine1',.04),('Spine2',-.10)]
        trunk=[math.exp(-((y-p)/.15)**2) for n,p in anchors]; total=sum(trunk)
        weights={n:(1-head)*w/total for (n,p),w in zip(anchors,trunk)}
        weights['Head']=head
        front=abs(y+.10)<abs(y-.48); leg_y=-.10 if front else .48
        leg=(1-smooth(.30,.58,z))*(1-smooth(.10,.23,abs(y-leg_y)))*smooth(.045,.12,abs(x))*(1-head)
        for n in weights:weights[n]*=1-leg
        names=[side+'Arm',side+'ForeArm',side+'Hand'] if front else [side+'UpLeg',side+'Leg',side+'Foot']
        heights=[.50,.325,.135] if front else [.57,.35,.14]
        limb=[math.exp(-((z-h)/.13)**2) for h in heights]; total=sum(limb)
        for n,w in zip(names,limb):weights[n]=leg*w/total
        # Unity uses four influences; prune and normalize explicitly.
        best=sorted(weights.items(),key=lambda item:item[1],reverse=True)[:4]; total=sum(w for n,w in best)
        for n,w in best:
            if w>1e-6:groups[n].add([v.index],w/total,'REPLACE')
skin_body(body)

# Heavy brows, recessed eyes, wet nose and split cloven hooves.
for side in (-1,1):
    pref='Left' if side<0 else 'Right'
    ell('Eye socket',(side*.176,-.491,.695),(.04,.055,.04),8,'Head')
    ell('Amber eye',(side*.204,-.505,.704),(.014,.025,.019),4,'Head',16,10)
    ell('Eye pupil',(side*.216,-.513,.704),(.006,.009,.013),12,'Head',12,8)
    brow=ell('Armored brow',(side*.163,-.49,.745),(.07,.12,.045),1,'Head');brow.rotation_euler.y=side*.25
    ell('Nostril',(side*.065,-.855,.54),(.028,.014,.021),12,'Nose',16,10)
    # Curved upward/outward tusks, thick root and worn ivory tips.
    tube('Weathered tusk',[(side*.13,-.65,.46),(side*.20,-.69,.47),(side*.265,-.68,.53),(side*.29,-.65,.62),(side*.27,-.62,.69)], [.055,.048,.034,.019,.002],2,'Mandible',14)
    tube('Upper cutter',[(side*.15,-.61,.56),(side*.205,-.65,.535),(side*.21,-.68,.50)], [.022,.014,.001],10,'Head',10)
    # Broad leaf ears with inset surface.
    ear=ell('Leaf ear',(side*.20,-.32,.885),(.105,.065,.16),0,pref+'Ear',16,12);ear.rotation_euler.y=side*.62
    inner=ell('Ear interior',(side*.205,-.365,.89),(.07,.012,.115),6,pref+'Ear',16,10);inner.rotation_euler.y=side*.62
    for y,bone in ((-.10,pref+'Hand'),(.48,pref+'Foot')):
        for split in (-1,1):
            bpy.ops.mesh.primitive_cube_add(size=1,location=(side*(.17 if y<0 else .145)+split*.029,y-.012,.05))
            hoof=bpy.context.object;hoof.name='Cloven hoof';hoof.scale=(.05,.145,.09)
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
            bevel=hoof.modifiers.new('Worn hoof edge','BEVEL');bevel.width=.012;bevel.segments=2;bpy.ops.object.modifier_apply(modifier=bevel.name)
            finish(hoof,3,bone)
        ell('Dewclaw',(side*(.17 if y<0 else .145),y+.06,.12),(.04,.035,.03),3,bone,12,8)
ell('Nose pad',(0,-.817,.525),(.135,.035,.086),8,'Nose',24,12)

def plate(name,center,width,length,height,bone,tile=1,tilt=0):
    # Irregular layered shell with raised spine and tapered chipped perimeter.
    c=Vector(center); n=8; vs=[]
    for ring in (1,.55):
        for i in range(n):
            t=2*math.pi*i/n; jitter=1+random.uniform(-.12,.12)
            xx=math.cos(t)*width*.5*ring*jitter; yy=math.sin(t)*length*.5*ring*jitter
            zz=(1-ring)*height+abs(yy)*.07
            vs.append(c+Vector((xx,yy,zz+xx*tilt)))
    vs.append(c+Vector((0,0,height)));fs=[]
    for i in range(n):fs.append((i,(i+1)%n,n+(i+1)%n,n+i));fs.append((n+i,n+(i+1)%n,16))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
    solid=o.modifiers.new('Bark thickness','SOLIDIFY');solid.thickness=.025;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=solid.name)
    finish(o,tile,bone)
    for p in o.data.polygons:p.use_smooth=False
    return o
for j,y in enumerate([-.28,-.12,.05,.22,.39,.52]):
    bone='Spine2' if y<-.02 else 'Spine' if y<.28 else 'Hips'
    z=.93 if y<.12 else .89 if y<.4 else .79
    plate('Dorsal bark scute',(0,y,z),.30,.26,.065,bone,1 if j%2 else 9)
    for side in (-1,1):
        plate('Overlapping flank plate',(side*.225,y,z-.12),.20,.30,.055,bone,1,tilt=-side*.75)
        if j<5:plate('Lower rib armor',(side*.27,y+.015,z-.25),.12,.25,.04,bone,9,tilt=-side*1.7)
    # Asymmetric thorns make the ridge legible at game distance.
    h=[.28,.25,.23,.18,.16,.11][j]
    tube('Ridge thorn',[(0,y,z+.025),(.015,y+.025,z+h*.45),(-.015,y+.065,z+h*.8),(.005,y+.11,z+h)], [.055,.038,.022,.001],1,bone,9)
    if j<4:
        for side in (-1,1):tube('Shoulder thorn',[(side*.19,y,z-.08),(side*.28,y+.025,z+.02),(side*.34,y+.08,z+.11)],[.045,.025,.001],9,bone,8)
# Brow plates, cheek scars, moss islands and coarse mane bristles.
plate('Forehead shield',(0,-.41,.82),.22,.24,.045,'Head',9)
for side in (-1,1):
    for j in range(3):tube('Cheek crease',[(side*.192,-.46-j*.045,.62),(side*.207,-.49-j*.045,.60),(side*.193,-.52-j*.045,.585)],[.006,.004,.001],7,'Head',5)
for j in range(45):
    y=random.uniform(-.25,.5); x=random.uniform(-.09,.09); z=.94 if y<.12 else .90 if y<.4 else .82
    bone='Spine2' if y<0 else 'Spine' if y<.28 else 'Hips'
    tube('Coarse mane',[(x,y,z),(x,y+.015,z+.055),(x+.01,y+.04,z+random.uniform(.07,.12))],[.007,.005,.0008],8,bone,5)
for j in range(15):
    y=random.uniform(-.2,.42); x=random.choice((-1,1))*random.uniform(.07,.20);z=.965 if y<.1 else .92
    ell('Moss lichen',(x,y,z),(.035,.055,.012),5,'Spine2' if y<0 else 'Spine',10,6)
tailpoints=[(0,.645,.59),(0,.66,.54),(.02,.68,.49),(.025,.68,.44),(0,.66,.39)]
for i in range(4):tube('Tail segment',tailpoints[i:i+2],[.018-i*.003,.015-i*.003],0,'Tail'+str(i+1),8)
ell('Tail tuft',(0,.66,.38),(.025,.04,.045),8,'Tail5',12,8)

# Merge into one material / skinned render mesh.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();mesh=bpy.context.object;mesh.name='Thornback_LOD0'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
arm=mesh.modifiers.new('Thornback skin','ARMATURE');arm.object=rig;mesh.parent=rig
lods=[mesh]
for level,ratio in ((1,.5),(2,.2)):
    o=mesh.copy();o.data=mesh.data.copy();bpy.context.collection.objects.link(o);o.name='Thornback_LOD'+str(level)
    for m in list(o.modifiers):o.modifiers.remove(m)
    dec=o.modifiers.new('LOD simplification','DECIMATE');dec.ratio=ratio
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=dec.name)
    mod=o.modifiers.new('Thornback skin','ARMATURE');mod.object=rig;o.hide_render=True;o.hide_set(True);lods.append(o)

clips={
 'Idle':(4,True),'Walk':(.933333,True),'Run':(.8,True),'TurnLeft':(1,True),'TurnRight':(1,True),
 'Alert':(1.2,False),'Scrape':(1.8,False),'Brace':(2,True),'Rush':(.8,True),
 'Brake':(.45,False),'Recovery':(2,True),'Attack':(.4,False),'AttackRunning':(.533333,False),
 'Hit':(.566667,False),'Death':(.8,False),'Corpse':(1,True),'Sleep':(2.666667,True),'Wake':(1.333333,False)}
def rotate(name,x=0,y=0,z=0):rig.pose.bones[name].rotation_euler=(math.radians(x),math.radians(y),math.radians(z))
def animate(name,t,duration):
    q=t/duration; wave=math.sin(q*2*math.pi); pulse=math.sin(q*math.pi)
    for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0)
    rig.pose.bones['Spine'].scale=(1,1,1)
    rotate('Head',2*wave);rotate('LeftEar',0,0,5*wave);rotate('RightEar',0,0,-5*wave)
    rotate('Tail1',0,7*wave)
    if name in ('Walk','Run','Rush','AttackRunning'):
        amp=20 if name=='Walk' else 35; phase=q*2*math.pi
        for side,sign in [('Left',1),('Right',-1)]:
            for front,offset in [(True,0),(False,math.pi)]:
                p=phase+(0 if side=='Left' else math.pi)+offset; a=math.sin(p)*amp
                rotate(side+('Arm' if front else 'UpLeg'),sign*a)
                rotate(side+('ForeArm' if front else 'Leg'),sign*max(0,-math.sin(p))*amp*.8)
                rotate(side+('Hand' if front else 'Foot'),-sign*a*.35)
        rig.pose.bones['Hips'].location.y=.012*math.sin(phase*2)
        rotate('Spine2',2*math.sin(phase*2));rotate('Head',(-12 if name=='Rush' else 0)+3*wave)
    if name in ('TurnLeft','TurnRight'):
        s=1 if name=='TurnLeft' else -1;rotate('Head',0,s*17,0);rotate('Spine2',0,s*6,0)
        for side,sign in [('Left',1),('Right',-1)]:rotate(side+'Arm',sign*9*wave);rotate(side+'UpLeg',-sign*8*wave)
    if name=='Idle':rotate('Head',3*wave,5*math.sin(q*4*math.pi),0);rotate('Nose',2*math.sin(q*8*math.pi));rig.pose.bones['Spine'].scale=(1+.012*wave,1+.008*wave,1)
    if name=='Alert':rotate('Head',-13*pulse,10*math.sin(q*2*math.pi),0);rotate('LeftEar',-12*pulse);rotate('RightEar',12*pulse)
    if name=='Scrape':
        rotate('Head',10*pulse);rotate('LeftArm',-30*pulse);rotate('LeftForeArm',45*max(0,math.sin(q*4*math.pi)));rotate('LeftHand',-20*pulse)
    if name=='Brace':
        rotate('Head',18+2*wave);rotate('Spine2',5);rotate('LeftArm',-12);rotate('RightArm',12);rig.pose.bones['Hips'].location.y=-.025
    if name=='Brake':
        rotate('Head',-10*pulse);rotate('LeftArm',-24*pulse);rotate('RightArm',24*pulse);rotate('Hips',-6*pulse)
    if name=='Recovery':rotate('Head',12+4*wave);rig.pose.bones['Spine'].scale=(1+.025*wave,1+.018*wave,1);rotate('Mandible',3+2*wave)
    if name in ('Attack','AttackRunning'):
        # Contact at 45% of the clip; no damage events are emitted by custom art.
        attack=math.sin(min(q/.45,1)*math.pi/2) if q<.45 else math.cos((q-.45)/.55*math.pi/2)
        rotate('Head',-25*attack,0,5*attack);rotate('Mandible',8*attack);rotate('Spine2',-5*attack)
    if name=='Hit':rotate('Head',9*pulse,0,-13*pulse);rotate('Spine2',0,0,-5*pulse)
    if name in ('Death','Corpse'):
        f=min(1,q*1.5) if name=='Death' else 1;f=f*f*(3-2*f)
        rotate('Hips',0,0,83*f);rig.pose.bones['Hips'].location.y=-.32*f
        rotate('Head',15*f);rotate('LeftArm',-25*f);rotate('RightArm',28*f);rotate('LeftUpLeg',20*f);rotate('RightUpLeg',-22*f)
        rotate('LeftEar');rotate('RightEar');rotate('Tail1')
    if name in ('Sleep','Wake'):
        f=1 if name=='Sleep' else 1-q;rig.pose.bones['Hips'].location.y=-.22*f;rotate('Head',15*f)
        for side,sign in [('Left',1),('Right',-1)]:rotate(side+'Arm',sign*35*f);rotate(side+'ForeArm',-sign*65*f);rotate(side+'UpLeg',-sign*30*f);rotate(side+'Leg',sign*60*f)
for name,(duration,loop) in clips.items():
    action=bpy.data.actions.new(name);rig.animation_data_create();rig.animation_data.action=action
    last=max(2,round(duration*30));scene.frame_start=1;scene.frame_end=last+1
    for f in range(1,last+2):
        scene.frame_set(f);animate(name,(f-1)/30,duration)
        for b in rig.pose.bones:
            b.keyframe_insert('rotation_euler',frame=f,group=b.name);b.keyframe_insert('location',frame=f,group=b.name)
        rig.pose.bones['Spine'].keyframe_insert('scale',frame=f,group='Spine')
    action.use_fake_user=True
    action['loop']=loop
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_start=1;scene.frame_end=121;scene.frame_set(1)

# FBX: original model, bones, all named actions and three LOD meshes.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in lods:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'delveThornbackBoar.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,mesh_smooth_type='FACE')
for o in lods[1:]:o.hide_set(True)
counts={}
for o in lods:o.data.calc_loop_triangles();counts[o.name]=len(o.data.loop_triangles)
open(os.path.join(OUT,'asset-manifest.json'),'w').write(json.dumps({'entity':'delveThornbackBoar','authoring':'Original procedural mesh, UV atlas, skinning and animation by Codex for this project','native_geometry_copied':False,'rig_bones':len(bone_names),'triangles':counts,'animations':{n:{'seconds':d,'loop':l} for n,(d,l) in clips.items()},'texture':'Thornback_Albedo.png','texture_size':2048},indent=2))

# Preview staging remains editable in the blend, excluded from FBX.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008));ground=bpy.context.object;ground.name='PreviewGround'
gm=bpy.data.materials.new('Ground');gm.diffuse_color=(.055,.065,.05,1);ground.data.materials.append(gm)
worldmat=bpy.data.worlds.new('StudioWorld');scene.world=worldmat;worldmat.use_nodes=True;worldmat.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.22,1);worldmat.node_tree.nodes['Background'].inputs[1].default_value=.35
for name,loc,power,size,color in [('Key',(-3,-4,5),550,4,(1,.84,.65)),('Fill',(3,-1,3),260,3,(.66,.78,1)),('Rim',(0,3,4),650,3,(.80,1,.74))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color;o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('PreviewCamera');cam=bpy.data.objects.new('PreviewCamera',data);bpy.context.collection.objects.link(cam);scene.camera=cam;data.type='ORTHO';data.ortho_scale=2.0
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
cam.location=(2.3,-3.2,1.65);cam.rotation_euler=(Vector((0,-.02,.56))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'delveThornbackBoar.blend'))
for name,loc in ([] if '--skip-render' in sys.argv else [('hero',(2.3,-3.2,1.65)),('side',(3,0,1)),('front',(0,-3,1)),('back',(0,3,1)),('night',(2.3,-3.2,1.65))]):
    cam.location=loc;cam.rotation_euler=(Vector((0,-.02,.56))-cam.location).to_track_quat('-Z','Y').to_euler()
    if name=='night':
        bpy.data.lights['Key'].energy=35;bpy.data.lights['Fill'].energy=40;bpy.data.lights['Rim'].energy=100;worldmat.node_tree.nodes['Background'].inputs[1].default_value=.07
    scene.render.filepath=os.path.join(PREVIEW,name+'.png');bpy.ops.render.render(write_still=True)
print('THORNBACK_BUILD_PASS',json.dumps(counts))
