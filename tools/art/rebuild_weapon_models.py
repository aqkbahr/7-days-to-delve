"""Reconstruct all weapon forms around their integrated rigs and sockets, Blender 5.2."""
from pathlib import Path
import bpy,math,random,json,sys,traceback
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
STAGE=Path('D:/Projects/Codex/7DaysToDelve/WeaponRebuild20261026')
specs=json.loads((STAGE/'weapons.json').read_text())['weapons'];TAU=math.tau
def uv(tile,u,v):return ((tile%4+.025+.95*u)/4,(3-tile//4+.025+.95*v)/4)
def textures():
    image=bpy.data.images.load(str(STAGE/'Artwork/WeaponMaterials-original.png'));image.scale(2048,2048);data=np.empty(2048*2048*4,np.float32);image.pixels.foreach_get(data);atlas=data.reshape(2048,2048,4)
    maps={'Atlas':atlas,'Normal':np.ones_like(atlas),'Metallic':np.ones_like(atlas),'Occlusion':np.ones_like(atlas),'Emission':np.ones_like(atlas)};maps['Emission'][:,:,:3]=0
    rng=np.random.default_rng(301)
    for tile in range(16):
        row=3-tile//4;col=tile%4;sl=np.s_[row*512:(row+1)*512,col*512:(col+1)*512];lum=atlas[sl][:,:,:3]@np.array((.2126,.7152,.0722));dy,dx=np.gradient(lum)
        strength=.8 if tile in (0,1,4,7,8,9) else .34;normal=np.stack((-dx*strength,-dy*strength,np.ones_like(dx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1)[...,None];maps['Normal'][sl][:,:,:3]=normal*.5+.5
        metal=1 if tile in (2,3) else .9 if tile==5 else 0;rough=.43 if tile==2 else .27 if tile==3 else .45 if tile==5 else .24 if tile>=12 else .86 if tile in (7,9) else .73 if tile==1 else .62
        maps['Metallic'][sl][:,:,:3]=metal;maps['Metallic'][sl][:,:,3]=np.clip(1-rough+(lum-lum.mean())*.14,.08,.82);maps['Occlusion'][sl][:,:,:3]=np.clip(.97+(lum-lum.mean())*.10,.82,1)[...,None]
        if tile>=12:maps['Emission'][sl][:,:,:3]=atlas[sl][:,:,:3]*.25
    folder=STAGE/'UnityProject/Assets/RebuiltWeaponTextures';folder.mkdir(exist_ok=True)
    for name,values in maps.items():
        im=bpy.data.images.new('RebuiltWeapon'+name,width=2048,height=2048,alpha=True)
        if name not in ('Atlas','Emission'):im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(values.ravel());im.filepath_raw=str(folder/(name+'.png'));im.file_format='PNG';im.save()

class MeshBuilder:
    def __init__(self,seed):self.rng=random.Random(seed);self.v=[];self.f=[];self.uv=[];self.tiles=[];self.weights=[];self.colors=[];self.smooth=[];self.labels={};self.face_uv=[]
    def part(self,vs,fs,tile,bone='Weapon',uvs=None,smooth=False,tint=(1,1,1),label='component',weights=None,face_uvs=None):
        if isinstance(tile,int) and tile in (0,4,8):tint=(tint[0],tint[1]*.93,tint[2]*.84)
        uvs=uvs or [(.5,.5)]*len(vs)
        if face_uvs is None:
            face_uvs=[]
            for face in fs:
                points=[uvs[i] for i in face];area=abs(sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points))))
                if area<1e-8:
                    vertices=[Vector(vs[i]) for i in face];normal=(vertices[1]-vertices[0]).cross(vertices[2]-vertices[0]);axis=max(range(3),key=lambda i:abs(normal[i]));coords=tuple(i for i in range(3) if i!=axis);minimum=[min(p[i] for p in vertices) for i in coords];maximum=[max(p[i] for p in vertices) for i in coords]
                    face_uvs.append([tuple(.06+.88*(p[i]-lo)/max(.00001,hi-lo) for i,lo,hi in zip(coords,minimum,maximum)) for p in vertices])
                else:face_uvs.append(None)
        start=len(self.v);self.v.extend([tuple(p) for p in vs]);self.f.extend([tuple(i+start for i in f) for f in fs]);self.uv.extend(uvs or [(.5,.5)]*len(vs));self.tiles.extend(tile if isinstance(tile,list) else [tile]*len(fs));self.face_uv.extend(face_uvs or [None]*len(fs));self.smooth.extend([smooth]*len(fs));self.weights.extend(weights or [{bone:1} for _ in vs]);shade=self.rng.uniform(.88,1);self.colors.extend([tuple(t*shade for t in tint)]*len(vs));self.labels[label]=self.labels.get(label,0)+1
    def tube(self,points,radii,tile=0,bone='Weapon',sides=12,label='shaped shaft',weights=None,aspect=(1,1),tint=(1,1,1)):
        pts=[Vector(p) for p in points];radii=[radii]*len(pts) if isinstance(radii,(float,int)) else radii;vs=[];fs=[];uvs=[];ws=[]
        for i,p in enumerate(pts):
            tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();side=tangent.cross(Vector((0,1,0)))
            if side.length<.01:side=tangent.cross(Vector((1,0,0)))
            side.normalize();other=tangent.cross(side)
            for j in range(sides+1):
                a=j*TAU/sides;vs.append(p+radii[i]*(side*math.cos(a)*aspect[0]+other*math.sin(a)*aspect[1]));uvs.append((j/sides,i/(len(pts)-1)));ws.append(weights(i/(len(pts)-1)) if weights else {bone:1})
        for i in range(len(pts)-1):
            for j in range(sides):q=i*(sides+1)+j;fs.append((q,q+1,q+sides+2,q+sides+1))
        fs.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*(sides+1)+j for j in range(sides))]);self.part(vs,fs,tile,bone,uvs,True,tint,label,ws)
        self.smooth[-2:]=[False,False]
    def lathe(self,profile,tile=2,bone='Weapon',center=(0,0,0),sides=20,label='turned fitting',tint=(1,1,1),irregular=0):
        p=Vector(center);vs=[];fs=[];uvs=[];z0=profile[0][1];length=profile[-1][1]-z0
        for i,(r,z) in enumerate(profile):
            for j in range(sides+1):
                a=j*TAU/sides;rr=r*(1+irregular*math.sin(a*5+i*.45)+irregular*.4*math.cos(a*3));vs.append(p+Vector((rr*math.cos(a),rr*math.sin(a),z)));uvs.append((j/sides,(z-z0)/max(.001,length)))
        for i in range(len(profile)-1):
            for j in range(sides):q=i*(sides+1)+j;fs.append((q,q+1,q+sides+2,q+sides+1))
        fs.extend([tuple(reversed(range(sides))),tuple((len(profile)-1)*(sides+1)+j for j in range(sides))]);self.part(vs,fs,tile,bone,uvs,True,tint,label)
        self.smooth[-2:]=[False,False]
    def band(self,z,r,width=.012,tile=2,bone='Weapon',center=(0,0,0),sides=24):
        self.lathe([(r*.93,z-width*.5),(r,z-width*.32),(r,z+width*.32),(r*.93,z+width*.5)],tile,bone,center,sides,label='beveled collar')
    def ribbon(self,z0,z1,rx,ry,tile=1,bone='Weapon',turns=7,width=.021,x=0):
        vs=[];fs=[];uvs=[];steps=turns*18
        for i in range(steps+1):
            t=i/steps;a=t*TAU*turns;contour=1+.055*math.sin(math.pi*t)
            for dr,dz in ((0,-width/2),(0,width/2),(.0011,-width/2),(.0011,width/2)):
                vs.append((x+(rx*contour+dr)*math.cos(a),(ry*contour+dr)*math.sin(a),z0+(z1-z0)*t+dz));uvs.append((i%18/18,.2 if dz<0 else .8))
        for i in range(steps):q=i*4;p=q+4;fs.extend([(q,p,p+1,q+1),(q+2,q+3,p+3,p+2),(q,q+2,p+2,p),(q+1,p+1,p+3,q+3)])
        self.part(vs,fs,tile,bone,uvs,True,label='overlapping flat leather binding')
    def seam(self,z0,z1,r,bone='Weapon',x=0):
        for i in range(12):
            z=z0+(z1-z0)*(i+.5)/12;self.tube([(x-.004,-r,z-.0017),(x+.004,-r-.0006,z+.0017)],.00065,9,bone,5,label='individual saddle stitch')
    def grip(self,z0=-.12,z1=.08,r=.022,bone='Weapon',x=0,tile=1):
        self.tube([(x,0,z0),(x,0,(z0+z1)/2),(x,0,z1)],[r*.91,r,r*.92],tile,bone,16,label='contoured grip core');self.ribbon(z0+.008,z1-.008,r+.001,r*.92+.001,tile,bone,7,x=x);self.seam(z0+.015,z1-.015,r+.004,bone,x)
    def rivet(self,p,r=.003,tile=5,bone='Weapon',axis='y'):
        self.gem(p,(r,r*.5,r),tile,bone,sides=8,label='peened rivet')
    def extrude(self,outline,depth,tile=2,bone='Weapon',y=0,bevel=.04,label='chamfered fitting',tint=(1,1,1)):
        area=sum(outline[i][0]*outline[(i+1)%len(outline)][1]-outline[(i+1)%len(outline)][0]*outline[i][1] for i in range(len(outline)))
        if area<0:outline=list(reversed(outline))
        cx=sum(p[0] for p in outline)/len(outline);cz=sum(p[1] for p in outline)/len(outline);vs=[];uvs=[];n=len(outline);fs=[];tiles=[];xmin=min(x for x,z in outline);xmax=max(x for x,z in outline);zmin=min(z for x,z in outline);zmax=max(z for x,z in outline)
        for yy,scale in ((y-depth/2,1-bevel),(y-depth*.32,1),(y+depth*.32,1),(y+depth/2,1-bevel)):
            for x,z in outline:vs.append((cx+(x-cx)*scale,yy,cz+(z-cz)*scale));uvs.append(((x-xmin)/max(.001,xmax-xmin),(z-zmin)/max(.001,zmax-zmin)))
        fs.extend([tuple(range(n)),tuple(reversed(range(3*n,4*n)))]);tiles.extend([tile,tile])
        for k in range(3):
            for j in range(n):fs.append((k*n+j,(k+1)*n+j,(k+1)*n+(j+1)%n,k*n+(j+1)%n));tiles.append(3 if tile==2 and k!=1 else tile)
        edges={}
        for face in fs:
            for a,b in zip(face,face[1:]+face[:1]):
                key=(min(a,b),max(a,b));count,orientation=edges.get(key,(0,0));edges[key]=(count+1,orientation+(1 if a<b else -1))
        assert all(count==2 and orientation==0 for count,orientation in edges.values()),'Non-manifold or inconsistent fitting normals: '+label
        self.part(vs,fs,tiles,bone,uvs,False,tint,label)
    def blade(self,z0,z1,width,stone=False,bone=False):
        vs=[];uvs=[];fs=[];tiles=[];rings=[(0,.72),(.08,1),(.38,.95),(.65,.79),(.84,.49),(.95,.20),(1,.003)];xs=(-1,-.72,-.21,0,.21,.72,1);depth=.010 if not stone else .014
        for side in (-1,1):
            for i,(t,w) in enumerate(rings):
                for j,x in enumerate(xs):
                    relief=(0,.67,1,.73,1,.67,0)[j] if not stone and not bone else (0,.6,.9,1,.9,.6,0)[j];irregular=(1+.10*math.sin(i*3+j*1.7)) if stone else 1;vs.append((x*width*w*irregular,side*depth*relief*(1-t*.78),z0+(z1-z0)*t));uvs.append(((x+1)/2,t))
        half=len(rings)*len(xs)
        for side in range(2):
            for i in range(len(rings)-1):
                for j in range(len(xs)-1):q=side*half+i*7+j;face=(q,q+1,q+8,q+7);fs.append(face if not side else tuple(reversed(face)));tiles.append(10 if stone else 6 if bone else 2 if j in (2,3) else 3)
        for edge in (0,6):
            for i in range(len(rings)-1):a=i*7+edge;b=(i+1)*7+edge;fs.append((a,b,b+half,a+half));tiles.append(10 if stone else 6 if bone else 3)
        self.part(vs,fs,tiles,'Weapon',uvs,False,label='knapped stone point' if stone else 'carved bone blade' if bone else 'ground steel blade with recessed fuller')
    def gem(self,p,size,tile,bone='Focus',sides=10,label='cut mineral focus'):
        p=Vector(p);vs=[];uvs=[];fs=[]
        for i,(r,z) in enumerate(((.12,-1),(.72,-.70),(1,-.30),(.94,.45),(.5,.85),(.05,1))):
            for j in range(sides):a=j*TAU/sides;vs.append(p+Vector((size[0]*r*math.cos(a),size[1]*r*math.sin(a),size[2]*z)));uvs.append((j/sides,i/5))
        for i in range(5):
            for j in range(sides):q=i*sides+j;fs.append((q,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,q+sides))
        self.part(vs,fs,tile,bone,uvs,False,label=label)

def make_dagger(g,tier):
    g.grip();g.lathe([(.015,-.165),(.028,-.158),(.030,-.140),(.024,-.115)],2 if tier else 6,label='fitted tang pommel');g.band(.076,.026,.014,5 if tier else 6)
    outline=[(-.078 if tier else -.049,.081),(-.074 if tier else -.046,.104),(-.033,.111),(.033,.111),(.074 if tier else .046,.104),(.078 if tier else .049,.081),(.047,.087),(-.047,.087)];g.extrude(outline,.032,2 if tier else 6,label='swept finger guard')
    g.blade(.11,.48 if tier else .40,.044 if tier else .034,bone=not tier)
    for z in (-.07,.018):g.rivet((0,-.025,z),.0045,tile=5 if tier else 6)
    if tier:
        for i in range(4):g.tube([(-.009+i*.005,-.010,.145),(-.007+i*.005,-.010,.153)],.0005,5,sides=4,label='maker chisel mark')
    else:g.ribbon(.065,.125,.029,.021,9,turns=4,width=.010)

def make_mace(g,tier):
    g.tube([(0,0,-.16),(.002,0,.14),(-.004,.002,.34),(0,0,.46)],[.027,.025,.030,.03 if tier else .047],0,sides=18);g.grip(-.15,.07,.029)
    if tier:
        g.lathe([(.033,.32),(.049,.35),(.050,.49),(.035,.565)],2,sides=24,label='forged mace head core')
        for k in range(6):
            a=k*TAU/6;outline=[(.032,.34),(.064,.355),(.091,.405),(.095,.46),(.072,.53),(.034,.56)];start=len(g.v);g.extrude(outline,.014,2,label='forged beveled flange')
            for i in range(start,len(g.v)):r,t,z=g.v[i];g.v[i]=(r*math.cos(a)-t*math.sin(a),r*math.sin(a)+t*math.cos(a),z)
        for z in (.345,.545):g.band(z,.051,.018,5)
    else:
        g.lathe([(.033,.25),(.046,.29),(.059,.36),(.064,.45),(.052,.52),(.026,.575)],0,sides=20,label='asymmetric knotted oak striking head',irregular=.12)
        for j in range(3):a=j*2.39;g.tube([(.048*math.cos(a),.048*math.sin(a),.34),(.062*math.cos(a+.06),.062*math.sin(a+.06),.43),(.045*math.cos(a+.1),.045*math.sin(a+.1),.52)],[.001,.0025,.0004],8,sides=5,label='split-grain scar')
        g.ribbon(.29,.34,.051,.050,1,turns=3,width=.016)
    g.band(-.15,.031,.014,2 if tier else 6)

def make_spear(g,tier):
    g.tube([(0,0,-.65),(.003,0,-.2),(-.002,.001,.4),(0,0,.94)],[.020,.019,.018,.021],4,sides=16);g.grip(-.10,.16,.022);g.band(-.64,.022,.035,2 if tier else 1)
    g.lathe([(.025,.875),(.028,.89),(.026,.96),(.019,1.005)],2 if tier else 1,label='fitted spear socket');g.blade(.98,1.27,.054,stone=not tier)
    g.ribbon(.89,.974,.029,.029,1 if tier else 9,turns=7,width=.011)
    for z in (.894,.956):g.rivet((0,-.029,z),.0035,2 if tier else 6)
    for z in (-.58,.77):g.band(z,.021,.014,5 if tier else 1)

def make_wraps(g,tier):
    for x,bone in ((0,'Weapon'),(-.20,'LeftWrap')):
        g.ribbon(-.055,.04,.046,.039,1 if tier else 7,bone,6,width=.021,x=x);g.ribbon(-.059,-.035,.048,.041,1,bone,2,width=.015,x=x)
        for j in range(4):
            xx=x+(j-1.5)*.022;g.extrude([(xx-.011,.037),(xx-.009,.059),(xx-.006,.066),(xx+.006,.066),(xx+.010,.060),(xx+.011,.037),(xx+.006,.032),(xx-.006,.032)],.016,2 if tier else 1,bone,y=-.041,bevel=.16,label='contoured knuckle guard');g.rivet((xx,-.051,.051),.0025,5 if tier else 6,bone)
        g.seam(-.052,.035,.043,bone,x)
        for sign in (-1,1):g.tube([(x+sign*.018,-.046,-.057),(x+sign*.018,-.050,-.034)],.0018,5 if tier else 6,bone,6,label='wrist buckle side')
        g.tube([(x-.018,-.05,-.035),(x+.018,-.05,-.035)],.0018,5 if tier else 6,bone,6,label='wrist buckle bridge')
        for z in (-.058,.041):g.tube([(x,0,z-.004),(x,0,z+.004)],.049,1 if tier else 7,bone,sides=24,aspect=(1,.85),label='tucked binding end welt')

def bow_limb(g,points,widths,bone,tier):
    pts=[Vector(p) for p in points];vs=[];uvs=[];fs=[];tiles=[]
    for i,p in enumerate(pts):
        w=widths[i];d=.008*(1-.65*i/(len(pts)-1));vs.extend([p+Vector((-w,-d,0)),p+Vector((w,-d,0)),p+Vector((w,d,0)),p+Vector((-w,d,0))]);uvs.extend([(0,i/(len(pts)-1)),(1,i/(len(pts)-1)),(1,i/(len(pts)-1)),(0,i/(len(pts)-1))])
    for i in range(len(pts)-1):
        for k in range(4):q=i*4+k;fs.append((q,i*4+(k+1)%4,(i+1)*4+(k+1)%4,q+4));tiles.append(4 if k in (0,2) else 0)
    if pts[-1].z<pts[0].z:fs=[tuple(reversed(face)) for face in fs]
    g.part(vs,fs,tiles,bone,uvs,True,label='tapered laminated bow limb' if tier else 'shaped sapwood bow limb')

def make_bow(g,tier):
    length=.65 if tier else .52;g.grip(-.09,.09,.022)
    for sign,bone in ((1,'BowUpper'),(-1,'BowLower')):
        pts=[];widths=[]
        for i in range(13):
            t=i/12;z=sign*(.08+(length-.08)*t);y=-.105*math.sin(math.pi*t*.92)+.044*t**7;pts.append((0,y,z));widths.append(.024*(1-t*.72))
        bow_limb(g,pts,widths,bone,tier)
        g.tube([pts[-1],(0,.025,0)],.0018,9,'String',sides=7,label='blended tension bowstring',weights=lambda t,b=bone:{b:1-t,'String':t})
        for i in range(4):p=Vector(pts[-1])+Vector((0,0,-sign*i*.005));g.band(p.z,.009,.0035,9,bone,center=(0,p.y,0),sides=14)
        g.band(sign*.087,.025,.010,5 if tier else 6)
    g.extrude([(.015,-.024),(.039,-.024),(.041,-.012),(.020,-.009)],.026,6,label='bone arrow rest')
    projectile(g,'arrow',tier,bone='Ammo',loaded='bow')

def make_crossbow(g):
    # Shaped tiller follows the -Y aim axis; steel rails and furniture have real bevels.
    vs=[];fs=[];uvs=[]
    for i,(y,w,top,bottom) in enumerate(((-.47,.024,.032,-.025),(-.32,.032,.039,-.032),(-.05,.031,.039,-.037),(.10,.025,.028,-.048),(.20,.039,.029,-.074),(.30,.043,.014,-.087))):
        for x,z in ((-w,top),(w,top),(w,bottom),(-w,bottom)):vs.append((x,y,z));uvs.append((.08 if x<0 else .92,i/5))
    for i in range(5):
        for k in range(4):q=i*4+k;fs.append((q,i*4+(k+1)%4,(i+1)*4+(k+1)%4,q+4))
    fs.extend([(3,2,1,0),(20,21,22,23)]);face_uv=[]
    # Side grain uses stock height across U and longitudinal length across V.
    # The old per-vertex projection collapsed each stock side to a texture line.
    for face in fs:
        p=[Vector(vs[i]) for i in face];normal=(p[1]-p[0]).cross(p[2]-p[0]);axis=max(range(3),key=lambda a:abs(normal[a]));coords=(2,1) if axis==0 else (0,2) if axis==1 else (0,1);minimum=[min(v[c] for v in p) for c in coords];maximum=[max(v[c] for v in p) for c in coords]
        face_uv.append([tuple(.04+.92*(v[c]-lo)/max(.001,hi-lo) for c,lo,hi in zip(coords,minimum,maximum)) for v in p])
    g.part(vs,fs,0,uvs=uvs,smooth=True,label='contoured wooden tiller',face_uvs=face_uv)
    g.grip(-.12,-.015,.022)
    for sign,bone in ((1,'BowUpper'),(-1,'BowLower')):
        pts=[(sign*.36*t,-.36-.06*math.sin(t*math.pi)+.06*t*t,0) for t in [i/10 for i in range(11)]]
        g.tube(pts,[.024-i*.0014 for i in range(11)],2,bone,sides=12,aspect=(1,.32),label='flattened steel crossbow prod');g.tube([pts[-1],(0,.02,0)],.0023,9,'String',sides=7,weights=lambda t,b=bone:{b:1-t,'String':t},label='blended crossbow string')
        g.tube([(sign*.012,-.45,.043),(sign*.012,.04,.043)],.0027,3,sides=8,label='polished bolt guide rail')
        for y in (-.28,-.12,.18):g.rivet((sign*.035,y,.012),.004,5)
        g.tube([(sign*.022,.07,-.063),(sign*.023,.06,-.112),(sign*.023,-.025,-.112),(sign*.022,-.045,-.06)],.003,2,sides=8,label='curved trigger guard')
    g.tube([(0,.025,-.055),(0,.005,-.094)],.0035,5,sides=8,label='trigger lever')
    # Stirrup lies in the stock plane, instead of an unrelated upright ring.
    g.tube([(-.038,-.45,-.012),(-.046,-.52,-.015),(0,-.55,-.015),(.046,-.52,-.015),(.038,-.45,-.012)],.006,2,sides=10,label='loading stirrup')
    projectile(g,'bolt',True,bone='Ammo',loaded='crossbow')

def glyph(g,kind,p,scale=.03,tile=12,bone='Weapon',plane='xz'):
    shapes={'wand':[(-1,0),(0,1),(1,0),(0,-1),(-1,0)],'staff':[(-1,-.8),(0,1),(1,-.8)],'hex':[(-1,.7),(1,-.7),(-1,-.7),(1,.7)],'heal':[(-1,0),(1,0),(0,0),(0,-1),(0,1)],'ward':[(-1,1),(1,1),(.8,-.5),(0,-1),(-.8,-.5),(-1,1)]}
    p=Vector(p)
    for a,b in zip(shapes[kind],shapes[kind][1:]):
        def point(q):return p+Vector((q[0]*scale,q[1]*scale,0) if plane=='xy' else (q[0]*scale,0,q[1]*scale))
        g.tube([point(a),point(b)],.0015,tile,bone,sides=5,label='inlaid physical rune stroke')

def make_magic(g,family,tier):
    tile={'wand':12,'staff':13,'hex':14,'heal':15,'ward':12}[family]
    if family in ('wand','staff'):
        end=1.0 if family=='staff' else .32;start=-.52 if family=='staff' else -.12;r=.025 if family=='staff' else .021
        pts=[(.003*math.sin(i*.7),.002*math.sin(i),start+(end-start)*i/10) for i in range(11)];g.tube(pts,[r*(.84+.22*math.sin(i/10*math.pi)) for i in range(11)],8 if tier else 4,sides=18,label='carved contoured focus shaft');g.grip(-.10,.075,.026)
        for z in (start+.015,end-.025):g.band(z,r+.004,.024,5 if tier else 6)
        for j in range(3):
            pts=[]
            for i in range(17):z=.10+(end-.16)*i/16;a=j*TAU/3+i*.12;pts.append((r*math.cos(a),r*math.sin(a),z))
            g.tube(pts,.0018,5 if tier else 8,sides=5,label='carved fluted shaft rib')
        for j in range(4):
            a=j*TAU/4;g.tube([(.027*math.cos(a),.027*math.sin(a),end-.025),(.046*math.cos(a),.046*math.sin(a),end+.06),(.024*math.cos(a),.024*math.sin(a),end+.17)],[.007,.005,.0015],5 if tier else 6,sides=9,label='fitted crystal setting claw')
        g.band(end+.012,.032,.022,5 if tier else 6);g.gem((0,0,end+.08),(.036,.032,.073),tile);glyph(g,family,(0,-r-.001,.69 if family=='staff' else .18),.011,tile)
    else:
        g.grip(-.14,.025,.026);outline=[(-.035,.03),(-.063,.07),(-.058,.18),(-.04,.225),(0,.238),(.04,.225),(.058,.18),(.063,.07),(.035,.03)];g.extrude(outline,.056,8 if tier else 0,bevel=.10,label='chamfered carved totem body')
        for sign in (-1,1):
            g.tube([(sign*.041,-.029,.055),(sign*.054,-.033,.13),(sign*.041,-.030,.205)],[.004,.005,.003],5 if tier else 6,sides=8,label='inset totem border')
            for z in (.065,.194):g.rivet((sign*.043,-.035,z),.0035,5 if tier else 6)
        if family=='hex':
            for sign in (-1,1):g.tube([(sign*.038,0,.20),(sign*.076,.002,.28),(sign*.059,.005,.345)],[.016,.011,.001],6,sides=12,label='curved bone horn')
            g.gem((0,-.033,.15),(.028,.018,.042),tile);glyph(g,'hex',(0,-.031,.085),.017,tile)
        elif family=='heal':
            for sign in (-1,1):g.tube([(sign*.015,0,.20),(sign*.055,0,.265),(sign*.027,0,.32)],[.012,.009,.0015],5 if tier else 6,sides=10,label='leaf-shaped mending crown')
            g.gem((0,-.008,.25),(.029,.023,.056),tile);glyph(g,'heal',(0,-.031,.135),.021,tile)
        else:
            g.extrude([(-.075,.285),(.075,.285),(.066,.15),(0,.085),(-.066,.15)],.018,2,y=-.025,bevel=.08,label='curved shield focus plate');g.gem((0,-.043,.205),(.030,.015,.048),tile);glyph(g,'ward',(0,-.039,.16),.029,5)
        g.band(.025,.030,.018,5 if tier else 6)

def projectile(g,family,tier,bone='Weapon',loaded=None):
    length=.72 if family=='arrow' else .43
    # Author standalone along Z; remap loaded projectile to the native -Y rail.
    start=len(g.v);g.tube([(0,0,-length/2),(0,0,length/2)],.0048,4,bone,sides=10,label='straight grained projectile shaft')
    head=[(-.014,length/2),(-.010,length/2+.032),(0,length/2+.055),(.010,length/2+.032),(.014,length/2),(0,length/2+.008)];g.extrude(head,.005,3 if tier else 10,bone,bevel=.05,label='forged bodkin point' if tier else 'knapped stone arrowhead')
    for j in range(3):
        a=j*TAU/3;z0=-length/2+.015;outline=[(.004,z0),(.020,z0+.01),(.023,z0+.06),(.010,z0+.088),(.004,z0+.09)];vs=[(r*math.cos(a),r*math.sin(a),z) for r,z in outline];fs=[tuple(range(5)),tuple(reversed(range(5)))];g.part(vs,fs,7,bone,[(r/.025,(z-z0)/.09) for r,z in outline],False,label='cut feather vane')
        g.tube([(r*math.cos(a),r*math.sin(a),z0+t*.085) for t,r in ((0,.004),(.5,.009),(1,.004))],.0005,9,bone,sides=4,label='feather quill')
    g.ribbon(length/2-.025,length/2+.004,.006,.006,9,bone,turns=4,width=.005)
    for z in (-length/2+.012,-length/2+.103):g.band(z,.006,.005,9,bone,sides=12)
    if loaded:
        shift=-.305 if loaded=='bow' else -.275
        for i in range(start,len(g.v)):
            x,y,z=g.v[i];g.v[i]=(x,-z+shift,y+(.045 if loaded=='crossbow' else 0))

def make_rune(g,spec):
    ident=spec['id'];etched='Etched' in ident;moon='Mooncap' in ident;kind='wand' if 'Wand' in ident else 'staff' if 'Staff' in ident else 'heal' if 'Healing' in ident else 'ward' if 'Ward' in ident else 'hex';tile={'wand':12,'staff':13,'hex':14,'heal':15,'ward':12}[kind]
    g.lathe([(.055,-.009),(.063,-.005),(.064,.005),(.058,.012)],2 if etched else 6 if moon else 10,sides=12 if etched else 11,label='beveled rune blank',irregular=.025 if not etched else 0)
    glyph(g,kind,(0,0,.013),.029,tile,plane='xy');g.band(.009,.055,.003,5 if etched else 6,sides=32)
    for j in range(12):
        a=j*TAU/12;g.tube([(.047*math.cos(a),.047*math.sin(a),.012),(.053*math.cos(a),.053*math.sin(a),.012)],.00065,5 if etched else 8,sides=4,label='radial rim chisel mark')
    if moon:g.band(.011,.045,.0025,6,sides=32)

def build(spec):
    ident=spec['id'];bpy.ops.wm.open_mainfile(filepath=spec['source']);rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');before={a.name:tuple(a.frame_range) for a in bpy.data.actions};bones={b.name:tuple(tuple(row) for row in b.matrix_local) for b in rig.data.bones}
    for o in list(bpy.data.objects):
        if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
    for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0);b.scale=(1,1,1)
    g=MeshBuilder(ident);family=spec['family'];tier=spec['tier']=='Forged'
    if family=='dagger':make_dagger(g,tier)
    elif family=='mace':make_mace(g,tier)
    elif family=='spear':make_spear(g,tier)
    elif family=='wraps':make_wraps(g,tier)
    elif family=='bow':make_bow(g,tier)
    elif family=='crossbow':make_crossbow(g)
    elif family in ('wand','staff','hex','heal','ward'):make_magic(g,family,tier)
    elif family=='rune':make_rune(g,spec)
    else:projectile(g,family,tier)
    mesh=bpy.data.meshes.new(ident+'_RebuiltMesh');mesh.from_pydata(g.v,[],g.f);mesh.update();obj=bpy.data.objects.new('Weapon_LOD0',mesh);bpy.context.collection.objects.link(obj)
    mesh.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in mesh.vertices],[t.vertices for t in mesh.loop_triangles],all_triangles=True);ao=[]
    for v in mesh.vertices:
        normal=v.normal.normalized();hit=0
        if normal.length>.5:
            side=normal.cross(Vector((.3,.7,.2))).normalized()
            for ray in (normal,(normal+side*.5).normalized(),(normal-side*.5).normalized()):hit+=tree.ray_cast(v.co+normal*.0012,ray,.035)[0] is not None
        ao.append(1-.10*hit)
    layer=mesh.uv_layers.new(name='UVMap');colors=mesh.color_attributes.new(name='WeaponVariation',type='FLOAT_COLOR',domain='CORNER');tiles=mesh.attributes.new(name='surface_tile',type='INT',domain='FACE')
    for poly in mesh.polygons:
        poly.use_smooth=g.smooth[poly.index]
        tiles.data[poly.index].value=g.tiles[poly.index]
        for local_index,li in enumerate(poly.loop_indices):
            vi=mesh.loops[li].vertex_index;local_uv=g.face_uv[poly.index][local_index] if g.face_uv[poly.index] is not None else g.uv[vi];layer.data[li].uv=uv(g.tiles[poly.index],*local_uv);colors.data[li].color=(*g.colors[vi],ao[vi])
    groups={name:obj.vertex_groups.new(name=name) for name in bones}
    for i,weights in enumerate(g.weights):
        total=sum(weights.values());assert abs(total-1)<.001
        for name,weight in weights.items():
            if weight>0:groups[name].add([i],weight,'REPLACE')
    mat=bpy.data.materials.new('RebuiltWeaponSurface');mat.use_nodes=True;nodes=mat.node_tree.nodes;bsdf=nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.55
    for channel in ('Atlas','Normal','Metallic','Occlusion','Emission'):
        tx=nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(STAGE/'UnityProject/Assets/RebuiltWeaponTextures'/(channel+'.png')))
        if channel not in ('Atlas','Emission'):tx.image.colorspace_settings.name='Non-Color'
        if channel=='Atlas':mat.node_tree.links.new(tx.outputs['Color'],bsdf.inputs['Base Color'])
        elif channel=='Normal':n=nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.35;mat.node_tree.links.new(tx.outputs['Color'],n.inputs['Color']);mat.node_tree.links.new(n.outputs['Normal'],bsdf.inputs['Normal'])
        elif channel=='Metallic':mat.node_tree.links.new(tx.outputs['Color'],bsdf.inputs['Metallic']);inv=nodes.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;mat.node_tree.links.new(tx.outputs['Alpha'],inv.inputs[1]);mat.node_tree.links.new(inv.outputs[0],bsdf.inputs['Roughness'])
    mesh.materials.append(mat);obj.parent=rig;mod=obj.modifiers.new('Skin','ARMATURE');mod.object=rig;lods=[obj]
    for level,ratio in ((1,.42),(2,.13)):
        o=obj.copy();o.data=mesh.copy();bpy.context.collection.objects.link(o);o.name='Weapon_LOD'+str(level)
        for mod in list(o.modifiers):o.modifiers.remove(mod)
        bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Rebuilt LOD','DECIMATE');mod.ratio=ratio;bpy.ops.object.modifier_apply(modifier=mod.name)
        # Collapse can extrapolate UVs on long thin fittings. Keep every reduced
        # face inside its original material cell rather than sampling adjacent metal.
        for poly in o.data.polygons:
            tile=o.data.attributes['surface_tile'].data[poly.index].value;col=tile%4;row=3-tile//4
            for li in poly.loop_indices:
                point=o.data.uv_layers.active.data[li].uv;point.x=max((col+.025)/4,min((col+.975)/4,point.x));point.y=max((row+.025)/4,min((row+.975)/4,point.y))
        mod=o.modifiers.new('Skin','ARMATURE');mod.object=rig;lods.append(o)
    assert before=={a.name:tuple(a.frame_range) for a in bpy.data.actions};assert bones=={b.name:tuple(tuple(row) for row in b.matrix_local) for b in rig.data.bones}
    for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0);b.scale=(1,1,1)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    for o in lods:o.select_set(True);o.hide_set(False);o.hide_render=False
    bpy.context.view_layer.objects.active=rig;bpy.ops.export_scene.fbx(filepath=str(STAGE/'UnityProject/Assets/Models'/(ident+'.fbx')),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
    folder=STAGE/'Sources'/ident;folder.mkdir(exist_ok=True)
    for o in lods[1:]:o.hide_render=True;o.hide_set(True)
    rig.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(ident+'.blend')),compress=True)
    counts=[]
    for o in lods:o.data.calc_loop_triangles();counts.append(len(o.data.loop_triangles))
    (folder/'model.json').write_text(json.dumps({'id':ident,'family':family,'tier':spec['tier'],'triangles':counts,'clips':len(before),'bones':len(bones),'parts':g.labels,'contract':'original bone rest matrices and action frame ranges preserved'},indent=2));print('WEAPON_REBUILD_PASS',ident,counts,flush=True)
try:
    (STAGE/'Reports/blender-error.txt').unlink(missing_ok=True)
    textures();requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];count=0
    for spec in specs:
        if requested and spec['id'] not in requested:continue
        (STAGE/'Reports/blender-progress.txt').write_text('BUILDING '+spec['id']);build(spec);count+=1
    (STAGE/'Reports/blender-progress.txt').write_text('PASS rebuilt '+str(count)+' selected weapon models')
except Exception:
    (STAGE/'Reports/blender-error.txt').write_text(traceback.format_exc());raise
