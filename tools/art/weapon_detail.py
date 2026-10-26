"""Construction detail for Field and Forged weapons, in the existing rig space."""
import math
def detail(ctx):
    g=ctx
    family,tier=g['family'],g['tier'];rod,ring,box=g['rod'],g['ring'],g['box']
    tube,ell=g['tube'],g['ell'];parts=g['parts']
    def stud(p,r=.004,bone='Weapon',tile=15):ell('Peened rivet',p,(r,r*.65,r),tile,bone,10,6)
    def spiral(z0,z1,r,tile=1,bone='Weapon',x=0,turns=8):
        pts=[(x+r*math.cos(j*math.tau*turns/120),r*math.sin(j*math.tau*turns/120),z0+(z1-z0)*j/120) for j in range(121)]
        tube('Continuous stitched leather seam',pts,[.0015]*len(pts),tile,bone,5)
    def seam(z0,z1,r,bone='Weapon',x=0):
        for j in range(12):
            z=z0+(z1-z0)*(j+.5)/12
            rod('Saddle stitch',(x-.006,-r,z-.002),(x+.006,-r,z+.002),.0008,11,bone)
    if family not in ('rune','arrow','bolt','wraps'):
        spiral(-.10,.065,.027 if family in ('staff','wand','hex','heal','ward') else .023,5)
        seam(-.10,.065,.029 if family in ('staff','wand','hex','heal','ward') else .025)
    if family=='dagger':
        for sign in (-1,1):
            # Sharpened bevel follows the leaf silhouette, separate from dark blade face.
            tube('Honed cutting bevel',[(sign*.044 if tier else sign*.034,0,.11),(sign*.033 if tier else sign*.026,0,.38 if tier else .33),(0,0,.48 if tier else .40)],[.0025,.002,.0003],2 if tier else 11,'Weapon',5)
            ell('Guard terminal',(sign*(.071 if tier else .046),0,.09),(.014,.019,.016),15 if tier else 11,'Weapon',12,8)
        for z in (-.075,.025):stud((0,-.025,z),.005)
        if tier:
            box('Ricasso',(0,0,.123),(.065,.024,.045),3)
            for j in range(5):rod('Smith stamp',(-.012+j*.005,-.013,.14),( -.010+j*.005,-.013,.15),.0008,15)
    elif family=='mace':
        if not tier:
            # Irregular split grain and knots interrupt the old ellipsoid silhouette.
            for j in range(7):
                a=j*math.tau/7
                pts=[(.043*math.cos(a),.043*math.sin(a),.30),(.061*math.cos(a+.08),.057*math.sin(a+.08),.43),(.035*math.cos(a-.05),.035*math.sin(a-.05),.55)]
                tube('Raised split oak grain',pts,[.005,.008,.002],4,'Weapon',7)
            for z in (.31,.37):ring('Iron repair hoop',(0,0,z),.057,.005,3)
            for a in (0,1.8,3.9):stud((.063*math.cos(a),.063*math.sin(a),.39),.007)
        else:
            for z in (.365,.535):ring('Head ferrule',(0,0,z),.067,.005,15)
            for j in range(6):
                a=j*math.tau/6
                stud((.080*math.cos(a),.080*math.sin(a),.41),.005)
                tube('Honed flange ridge',[(r*math.cos(a),r*math.sin(a),z) for r,z in [(.060,.35),(.092,.40),(.097,.47),(.075,.55)]],[.0018]*4,2,'Weapon',5)
        seam(-.12,.06,.034)
    elif family=='spear':
        spiral(.885,.97,.029,5,turns=8)
        for z in (.88,.95):stud((0,-.03,z),.004)
        for sign in (-1,1):tube('Spear honed edge',[(sign*.054,0,.99),(sign*.040,0,1.20),(0,0,1.27)],[.002,.0015,.0002],2 if tier else 11,'Weapon',5)
        for z in (-.60,.78):ring('Shaft binding',(0,0,z),.021,.003,15 if tier else 1)
    elif family=='wraps':
        for x,bone in [(0,'Weapon'),(-.20,'LeftWrap')]:
            seam(-.055,.06,.057,bone,x)
            for j in range(4):
                stud((x+(j-1.5)*.022,-.055,.055),.0035,bone)
                box('Knuckle leather welt',(x+(j-1.5)*.022,-.048,.036),(.020,.014,.008),5,bone)
            box('Wrist strap',(x,-.047,-.05),(.083,.014,.024),5,bone)
            box('Buckle tongue',(x,-.059,-.05),(.023,.004,.003),15,bone)
            for sx in (-.015,.015):rod('Buckle side',(x+sx,-.058,-.062),(x+sx,-.058,-.038),.002,15,bone)
    elif family=='bow':
        length=.65 if tier else .52
        for sign,bone in [(1,'BowUpper'),(-1,'BowLower')]:
            for j in range(5):
                z=sign*(length*.86+j*.012);y=-.09+(.115*(abs(z)/length-.82)/.18)
                ring('Horn nock binding',(0,y,z),.012,.002,11 if tier else 5,bone)
            tube('Contrasting limb lamination',[(-.012,0,sign*.08),(-.012,-.10,sign*length*.5),(-.009,-.09,sign*length*.82)],[.003,.003,.002],11 if tier else 4,bone,6)
        box('Arrow rest',( .024,0,-.015),(.025,.035,.010),11)
        for z in (-.085,.085):ring('Grip ferrule',(0,0,z),.024,.003,15 if tier else 5)
    elif family=='crossbow':
        for side in (-1,1):
            box('Stock reinforcement plate',(side*.035,-.18,-.005),(.008,.29,.035),3)
            for y in (-.29,-.18,-.06):stud((side*.041,y,.012),.005)
            rod('Bolt guide rail',(side*.012,-.44,.042),(side*.012,.06,.042),.003,2)
            tube('Trigger guard',[(side*.02,.09,-.065),(side*.02,.08,-.12),(side*.02,-.03,-.12),(side*.02,-.05,-.065)],[.003]*4,3,'Weapon',8)
        rod('Trigger lever',(0,.025,-.065),(0,.005,-.10),.004,15)
        box('Rolling sear',(0,.01,.045),(.044,.023,.024),2)
        for y in (.15,.20,.25):rod('Stock binding',(-.043,y,-.04),(.043,y,-.04),.003,5)
    elif family in ('wand','staff','hex','heal','ward'):
        color={'wand':6,'staff':7,'hex':8,'heal':9,'ward':10}[family]
        if family in ('wand','staff'):
            end=1.0 if family=='staff' else .32
            # Carved twisted ribs, a socket and a cage rather than a floating colored sphere.
            for j in range(3):
                pts=[]
                for k in range(18):
                    z=.10+(end-.13)*k/17;a=j*math.tau/3+k*.12
                    pts.append((.029*math.cos(a),.029*math.sin(a),z))
                tube('Carved spiral fillet',pts,[.0025]*18,15 if tier else 4,'Weapon',5)
            ring('Focus seat',(0,0,end+.025),.034,.006,15 if tier else 11)
            for j in range(4):
                a=j*math.tau/4
                tube('Crystal setting claw',[(.033*math.cos(a),.033*math.sin(a),end+.015),(.045*math.cos(a),.045*math.sin(a),end+.06),(.026*math.cos(a),.026*math.sin(a),end+.13)],[.005,.004,.001],15 if tier else 11,'Weapon',7)
            for z in (.12,.19):ring('Inlaid focus band',(0,0,z),.027,.002,color)
        else:
            for sign in (-1,1):
                tube('Carved border',[(sign*.055,-.033,.055),(sign*.065,-.034,.14),(sign*.05,-.034,.21)],[.005,.007,.004],15 if tier else 11,'Weapon',7)
                for z in (.075,.19):stud((sign*.05,-.041,z),.004)
            if family=='hex':
                for sign in (-1,1):
                    tube('Carved brow',[(0,-.045,.19),(sign*.027,-.048,.20),(sign*.052,-.04,.18)],[.004,.006,.002],11,'Weapon',7)
                for j in range(5):box('Carved teeth',((j-2)*.012,-.035,.078),(.006,.009,.024),11)
            if family=='heal':
                for sign in (-1,1):rod('Leaf midrib',(sign*.015,-.02,.19),(sign*.06,-.02,.30),.002,15 if tier else 11,'Focus')
            if family=='ward':
                for sign in (-1,1):rod('Shield emboss',(0,-.014,.10),(sign*.065,-.014,.22),.003,15)
    elif family=='rune':
        ring('Worn rune rim',(0,0,.01),.060,.0025,15 if tier else 11)
        for j in range(12):
            a=j*math.tau/12
            rod('Rim chisel mark',(.048*math.cos(a),.048*math.sin(a),.011),(.055*math.cos(a),.055*math.sin(a),.011),.0008,3)
    elif family in ('arrow','bolt'):
        length=.72 if family=='arrow' else .43
        spiral(length/2-.025,length/2,.006,5,turns=5)
        for z in (-length/2+.015,-length/2+.10):ring('Fletching tie',(0,0,z),.006,.001,4)
