import numpy as np, math, random
from PIL import Image, ImageDraw
N=1024

def gauss_wrap(a, sigma):
    # periodic gaussian blur via FFT -> stays seamless
    if sigma<=0: return a
    fy=np.fft.fftfreq(a.shape[0])[:,None]; fx=np.fft.fftfreq(a.shape[1])[None,:]
    k=np.exp(-2*(math.pi**2)*(sigma**2)*(fx**2+fy**2))
    return np.real(np.fft.ifft2(np.fft.fft2(a)*k))

def fold(big):
    # sum the 3x3 tiles of a 3N canvas into one N tile => seamless wrap
    return sum(big[i*N:(i+1)*N, j*N:(j+1)*N] for i in range(3) for j in range(3))

def wipe(draw, rng, cx, cy, length, width, angle, bend, strength):
    # an eraser wipe: many thin parallel streaks along a gentle arc, uneven pressure
    steps=60
    lines=int(width/2)
    phase=rng.uniform(0,6.28)
    for l in range(lines):
        off=(l/lines-0.5)*width
        u=l/max(lines-1,1)
        edge=max(0.0,1-(2*u-1)**2)**0.8          # soft edges across the wipe
        streak=edge*(0.7+0.3*math.sin(l*0.9+phase)*rng.uniform(0.5,1.0))  # gentle cloth streaks
        pts=[]
        for s in range(steps+1):
            t=s/steps
            a=angle+bend*(t-0.5)
            x=cx+math.cos(angle)*(t-0.5)*length - math.sin(a)*off
            y=cy+math.sin(angle)*(t-0.5)*length + math.cos(a)*off + bend*80*(t-0.5)**2*length/400
            pts.append((x+N,y+N))
        for s in range(steps):
            t=s/steps
            press=math.sin(math.pi*t)**0.6*streak   # fades in and out at both ends
            v=int(255*strength*press)
            if v>0: draw.line([pts[s],pts[s+1]], fill=v, width=2)

def ghost(draw, rng, strength):
    # faint leftover chalk marks: short scribbles/lines
    x,y=rng.uniform(0,N),rng.uniform(0,N)
    pts=[(x+N,y+N)]
    ang=rng.uniform(0,6.28)
    for k in range(rng.randint(3,7)):
        ang+=rng.uniform(-1.2,1.2)
        x+=math.cos(ang)*rng.uniform(15,45); y+=math.sin(ang)*rng.uniform(15,45)
        pts.append((x+N,y+N))
    draw.line(pts, fill=int(255*strength), width=rng.randint(2,4), joint="curve")

def make(seed, wipes, wipe_strength, clouds, ghosts, dust, max_alpha):
    rng=random.Random(seed); nrng=np.random.default_rng(seed)
    # 1) cloudy chalk haze (low frequency)
    haze=gauss_wrap(nrng.random((N,N)),60); haze=(haze-haze.min())/(haze.max()-haze.min())
    haze=np.clip((haze-0.45)/0.55,0,1)**1.5*clouds
    # 2) eraser wipes
    img=Image.new("L",(3*N,3*N),0); d=ImageDraw.Draw(img)
    for i in range(wipes):
        wipe(d,rng,rng.uniform(0,N),rng.uniform(0,N),rng.uniform(260,620),rng.uniform(40,90),
             rng.uniform(-0.5,0.5)+(math.pi if rng.random()<0.5 else 0),rng.uniform(-0.8,0.8),wipe_strength*rng.uniform(0.5,1.0))
    w=fold(np.asarray(img,dtype=float)/255.0)
    w=gauss_wrap(w,2.2)
    # 3) ghost strokes
    img2=Image.new("L",(3*N,3*N),0); d2=ImageDraw.Draw(img2)
    for i in range(ghosts): ghost(d2,rng,rng.uniform(0.25,0.6))
    g=gauss_wrap(fold(np.asarray(img2,dtype=float)/255.0),1.0)
    # 4) fine dust, clustered where there is haze/wipe
    speck=(nrng.random((N,N))>0.9965).astype(float)*nrng.uniform(0.3,1.0,(N,N))
    speck=gauss_wrap(speck,0.6)*dust*(0.4+haze+w)
    a=np.clip(haze*0.55+w*0.9+g*0.5+speck,0,None)
    a=a/ a.max()
    alpha=(a*max_alpha).clip(0,255).astype(np.uint8)
    rgba=np.zeros((N,N,4),np.uint8); rgba[...,:3]=255; rgba[...,3]=alpha
    return Image.fromarray(rgba,"RGBA")

variants={"subtle":dict(seed=7,wipes=14,wipe_strength=0.55,clouds=0.8,ghosts=6,dust=3.0,max_alpha=48),
          "medium":dict(seed=11,wipes=18,wipe_strength=0.75,clouds=1.0,ghosts=9,dust=3.5,max_alpha=70),
          "bold":dict(seed=23,wipes=22,wipe_strength=0.95,clouds=1.1,ghosts=12,dust=4.0,max_alpha=96)}
for name,cfg in variants.items():
    im=make(**cfg); im.save(f"/home/claude/tex/chalk_{name}_1024.png")
    # preview: tiled 2x1 over panel colour at 93%, with seam check line not drawn
    base=Image.new("RGBA",(2*N,N),(32,55,42,255))
    over=Image.new("RGBA",(2*N,N)); over.paste(im,(0,0)); over.paste(im,(N,0))
    Image.alpha_composite(base,over).convert("RGB").resize((1024,512)).save(f"/home/claude/tex/prev_{name}.png")
    a=np.asarray(im)[...,3].astype(float)
    print(name,"seam h %.2f/%.2f v %.2f/%.2f coverage>10: %.0f%%"%(np.abs(a[:,0]-a[:,-1]).mean(),np.abs(a[:,1:]-a[:,:-1]).mean(),np.abs(a[0]-a[-1]).mean(),np.abs(a[1:]-a[:-1]).mean(),(a>10).mean()*100))
