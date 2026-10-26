"""Deterministic original material surfaces for the staged quality pass."""
import math,os
import numpy as np
KINDS={
 'props':['wood','wood','metal','stone','ceramic','cloth','leaf','fruit','bone','brass','crystal','ceramic','soil','water','food','paper'],
 'armor':['cloth','leather','metal','metal','cloth','cloth','cloth','brass','cloth','cloth','metal','leather','cloth','leather','cloth','metal'],
 'weapons':['wood','leather','metal','metal','wood','leather','crystal','crystal','crystal','crystal','crystal','bone','soil','stone','cloth','brass'],
 'enemies':['skin','bark','bone','leather','eye','moss','skin','metal','metal','brass','cloth','leather','soil','wound','metal','leather'],
 'quadrupeds':['fur','fur','bone','hoof','eye','fur','skin','bark','fur','leather','crystal','hoof','soil','fur','crystal','bone'],
 'thornback':['fur','bark','bone','hoof','eye','moss','skin','wound','fur','bark','bone','hoof','soil','moss','skin','leather']}
def field(rng,cell,resolution):
    grid=rng.uniform(-1,1,(resolution+1,resolution+1));a=np.arange(cell)*resolution/cell;i=a.astype(int);f=a-i;f=f*f*f*(f*(f*6-15)+10)
    return (grid[i[:,None],i[None,:]]*(1-f[None,:])+grid[i[:,None],i[None,:]+1]*f[None,:])*(1-f[:,None])+(grid[i[:,None]+1,i[None,:]]*(1-f[None,:])+grid[i[:,None]+1,i[None,:]+1]*f[None,:])*f[:,None]
def build_surfaces(bpy,source,group,identity,dest):
    os.makedirs(dest,exist_ok=True)
    category=group if group in KINDS else 'props';kinds=KINDS[category]
    # Read linear colors from the authored atlas, preserving existing UV/material roles.
    old=bpy.data.images.load(source,check_existing=False);w,h=old.size;data=np.empty(w*h*4,np.float32);old.pixels.foreach_get(data);data=data.reshape(h,w,4)
    bases=[np.median(data[r*h//4:(r+1)*h//4,c*w//4:(c+1)*w//4,:3],axis=(0,1)) for r in range(4) for c in range(4)]
    bpy.data.images.remove(old)
    size=2048;cell=512;y,x=np.mgrid[0:cell,0:cell];u=x/cell;v=y/cell
    rng=np.random.default_rng(19271)
    maps={n:np.ones((size,size,4),np.float32) for n in ('Albedo','Normal','Metallic','Occlusion','Emission')}
    for i,(kind,base) in enumerate(zip(kinds,bases)):
        n=rng.normal(0,1,(cell,cell));coarse=field(rng,cell,5);mid=field(rng,cell,19);fine=field(rng,cell,87)
        height=n*.02;variation=coarse*.06+mid*.025;metal=0.;rough=.78;emission=0.;tint=np.ones((cell,cell,3),np.float32)
        if kind in ('wood','bark'):
            phase=u*145+3*np.sin(v*9)+np.sin(v*29)*.8
            grain=np.sin(phase)+.35*np.sin(phase*3.11);groove=np.maximum(0,-np.sin(phase*1.37)-.68)
            height=grain*.06-groove*(.32 if kind=='bark' else .08)+n*.012
            variation=grain*.033-groove*.14+coarse*.045+mid*.018;rough=.82 if kind=='bark' else .61
            tint[:,:,0]*=1.08;tint[:,:,2]*=.88
        elif kind=='fur':
            phase=u*530+np.sin(v*33)*1.7+np.sin(v*113)*.4
            strands=np.sin(phase);tips=np.maximum(0,np.sin(v*160+u*87))
            height=strands*.09*(.4+.6*tips)+n*.01;variation=strands*.035+coarse*.045+mid*.025;rough=.92
            if 'Gloomcat' in identity and i in (0,1):
                spots=np.zeros((cell,cell))
                for j in range(28):
                    a,b=rng.random(2);rx,ry=rng.uniform(.025,.065,2);d=((u-a)/rx)**2+((v-b)/ry)**2
                    spots=np.maximum(spots,np.exp(-((d-1)/.40)**2))
                variation-=spots*.065;tint[:,:,2]*=1.12
            if 'Hellhound' in identity:variation+=np.maximum(0,mid-.25)*.08
        elif kind in ('skin','wound'):
            crease=np.maximum(0,-np.sin(u*71+np.sin(v*59)*3)-.83)
            pores=np.maximum(0,n-1.2);height=mid*.025-crease*.13-pores*.055+n*.014
            variation=coarse*.035+mid*.018-pores*.014-crease*.045
            tint[:,:,0]+=np.maximum(0,coarse)*.16;tint[:,:,1]-=np.maximum(0,-mid)*.10;tint[:,:,2]+=np.maximum(0,-coarse)*.08
            rough=.65 if kind=='skin' else .38
        elif kind=='cloth':
            warp=np.sin(u*math.tau*110);weft=np.sin(v*math.tau*110);weave=warp*weft
            height=weave*.09+n*.008;variation=weave*.025+coarse*.045+mid*.017;rough=.94
        elif kind=='leather':
            cracks=np.maximum(0,np.sin(u*63+np.sin(v*49)*2)*np.sin(v*71+u*11)-.58)
            height=n*.032-cracks*.2;variation=coarse*.04+mid*.016-cracks*.07+n*.006;rough=.73
        elif kind in ('metal','brass'):
            pits=np.maximum(0,n-1.65);scratch=np.maximum(0,np.sin(u*630+v*24)-.97)*(np.sin(v*29)>.2)
            height=-pits*.035-scratch*.08+n*.006;variation=coarse*.025+mid*.015-pits*.012+scratch*.12;metal=.92;rough=.38 if kind=='metal' else .31
            tarnish=np.maximum(0,coarse*mid-.25);tint[:,:,0]+=tarnish*.25;tint[:,:,2]-=tarnish*.35
        elif kind in ('stone','soil','moss'):
            height=coarse*.09+mid*.12+fine*.035+n*.025;variation=coarse*.055+mid*.065+n*.01;rough=.95
            if kind=='moss':tint[:,:,1]+=np.maximum(0,mid)*.2
        elif kind=='leaf':
            rib=np.exp(-((u-.5)/.014)**2);vein=np.exp(-np.abs(np.sin(v*60+np.abs(u-.5)*70))*30)
            height=rib*.09+vein*.025+n*.003;variation=coarse*.025+rib*.05+vein*.02;rough=.55
        elif kind in ('bone','hoof'):
            height=np.sin(u*260+np.sin(v*31))*.025+n*.006;variation=coarse*.04+mid*.015+height*.3;rough=.47 if kind=='bone' else .35
        elif kind=='ceramic':
            height=n*.008+np.sin(v*350)*.008;variation=coarse*.04+mid*.015;rough=.33
        elif kind=='paper':
            height=n*.008+fine*.007;variation=coarse*.025+n*.006;rough=.91
            # Faded botanical maker's seal and ink lines, without invented readable text.
            radius=np.sqrt((u-.5)**2+(v-.60)**2);seal=np.exp(-((radius-.19)/.006)**2)
            stem=np.exp(-((u-.5)/.004)**2)*((v>.44)&(v<.75))
            leaves=np.exp(-(((np.abs(u-.5)-.055)/.025)**2+((v-.58-(u-.5)*.8)/.02)**2))
            ink=seal+stem+leaves
            for z in (.20,.26,.32):ink+=np.exp(-((v-z-.004*np.sin(u*27))/.004)**2)*((u>.24)&(u<.76))
            variation-=np.clip(ink,0,1)*.18
        elif kind=='food':
            pores=np.maximum(0,n-.9);height=mid*.035-pores*.03;variation=coarse*.06+mid*.025-pores*.014;rough=.79
        elif kind=='fruit':
            height=n*.007;variation=coarse*.04+mid*.02;rough=.30
        elif kind in ('crystal','eye','water'):
            veins=np.exp(-np.abs(np.sin(u*21+v*13+np.sin(v*19)))*40)
            height=veins*.012;variation=coarse*.025+veins*.07;rough=.18 if kind!='water' else .11;emission=.10 if kind=='eye' else .035 if kind=='crystal' else 0
        r,c=divmod(i,4);sl=np.s_[r*cell:(r+1)*cell,c*cell:(c+1)*cell]
        maps['Albedo'][sl][:,:,:3]=np.clip(base[None,None,:]*tint+variation[:,:,None],.004,.92)
        gy,gx=np.gradient(height);normal=np.stack((-gx*2,-gy*2,np.ones_like(gx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1)[:,:,None]
        maps['Normal'][sl][:,:,:3]=normal*.5+.5;maps['Metallic'][sl][:,:,:3]=metal;maps['Metallic'][sl][:,:,3]=np.clip(1-rough-variation*.2,.04,.92)
        maps['Occlusion'][sl][:,:,:3]=np.clip(1+height[:,:,None]*.30,.65,1);maps['Emission'][sl][:,:,:3]=base*emission
    images={}
    for name,px in maps.items():
        image=bpy.data.images.new('Quality_'+identity+'_'+name,width=size,height=size,alpha=True)
        if name not in ('Albedo','Emission'):image.colorspace_settings.name='Non-Color'
        image.pixels.foreach_set(px.ravel())
        if name in ('Metallic','Occlusion'):image.scale(1024,1024)
        if name=='Emission':image.scale(512,512)
        image.filepath_raw=os.path.join(dest,name+'.png');image.file_format='PNG';image.save();image.pack();images[name]=image
    return images
