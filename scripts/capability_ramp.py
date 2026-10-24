"""Maturity ramp: primary at 20/38/56/76/100 percent over the card, light and dark, for the library's token file and
Entelim's brand token file. Prints OKLab distance of the closest pair under normal vision, protanopia, deuteranopia and
tritanopia (Machado et al. 2009, severity 1.0, applied in linear sRGB), and text contrast on each composed step."""
import math, itertools, sys

def oklch_to_srgb_lin(L,C,h):
    a=C*math.cos(math.radians(h)); b=C*math.sin(math.radians(h))
    l_=L+0.3963377774*a+0.2158037573*b; m_=L-0.1055613458*a-0.0638541728*b; s_=L-0.0894841775*a-1.2914855480*b
    l,m,s=l_**3,m_**3,s_**3
    return [ 4.0767416621*l-3.3077115913*m+0.2309699292*s, -1.2684380046*l+2.6097574011*m-0.3413193965*s, -0.0041960863*l-0.7034186147*m+1.7076147010*s]
def clip(v): return [min(1,max(0,x)) for x in v]
def to_gamma(c): return [12.92*x if x<=0.0031308 else 1.055*x**(1/2.4)-0.055 for x in c]
def to_lin(c): return [x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4 for x in c]
def lin_to_oklab(c):
    r,g,b=c
    l=0.4122214708*r+0.5363325363*g+0.0514459929*b; m=0.2119034982*r+0.6806995451*g+0.1073969566*b; s=0.0883024619*r+0.2817188376*g+0.6299787005*b
    l,m,s=l**(1/3),m**(1/3),s**(1/3)
    return [0.2104542553*l+0.7936177850*m-0.0040720468*s, 1.9779984951*l-2.4285922050*m+0.4505937099*s, 0.0259040371*l+0.7827717662*m-0.8086757660*s]
def dist(a,b): return math.dist(lin_to_oklab(a),lin_to_oklab(b))
def lum(c): return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
def contrast(a,b):
    x,y=lum(a),lum(b); x,y=max(x,y),min(x,y); return (x+0.05)/(y+0.05)
MACHADO={'protanopia':[[0.152286,1.052583,-0.204868],[0.114503,0.786281,0.099216],[-0.003882,-0.048116,1.051998]],
 'deuteranopia':[[0.367322,0.860646,-0.227968],[0.280085,0.672501,0.047413],[-0.011820,0.042940,0.968881]],
 'tritanopia':[[1.255528,-0.076749,-0.178779],[-0.078411,0.930809,0.147602],[0.004733,0.691367,0.303900]]}
def sim(c,name):
    if name=='normal': return c
    M=MACHADO[name]; return clip([sum(M[i][j]*c[j] for j in range(3)) for i in range(3)])
def comp(fg,bg,a):  # composite in gamma sRGB like a browser
    g1,g2=to_gamma(clip(fg)),to_gamma(clip(bg)); return to_lin([a*x+(1-a)*y for x,y in zip(g1,g2)])

SETS={
 'library tokens (shadcn neutral)':{'light':dict(primary=(0.205,0,0),card=(1,0,0),fg=(0.145,0,0),pfg=(0.985,0,0)),'dark':dict(primary=(0.922,0,0),card=(0.205,0,0),fg=(0.985,0,0),pfg=(0.205,0,0))},
 'Entelim brand tokens (brand-decision-v1)':{'light':dict(primary=(0.497,0.163,257),card=(1,0,0),fg=(0.145,0,0),pfg=(0.985,0,0)),'dark':dict(primary=(0.70,0.14,257),card=(0.205,0,0),fg=(0.985,0,0),pfg=(0.205,0,0))},
}
STEPS=[('20',.2),('38',.38),('56',.56),('76',.76),('100',1.0)]
def run(verbose=True):
    out={}
    for sname,themes in SETS.items():
        for theme,t in themes.items():
            P=oklch_to_srgb_lin(*t['primary']); Cd=oklch_to_srgb_lin(*t['card']); FG=oklch_to_srgb_lin(*t['fg']); PFG=oklch_to_srgb_lin(*t['pfg'])
            P,Cd,FG,PFG=map(clip,(P,Cd,FG,PFG))
            cols=[comp(P,Cd,a) for _,a in STEPS]
            res={}
            for s in ['normal','protanopia','deuteranopia','tritanopia']:
                sc=[sim(c,s) for c in cols]
                pairs=sorted((dist(sc[i],sc[j]),STEPS[i][0],STEPS[j][0]) for i,j in itertools.combinations(range(5),2))
                nofill=sim(Cd,s); d0=dist(nofill,sc[0])
                res[s]=(pairs[0],d0,min(dist(sc[i],sc[i+1]) for i in range(4)))
            txt=[]
            for (n,a),c in zip(STEPS,cols):
                cf,cp=contrast(FG,c),contrast(PFG,c); txt.append((n,round(cf,2),round(cp,2)))
            out[(sname,theme)]=(res,txt)
            if verbose:
                print(f'== {sname}, {theme}')
                for s,(p,d0,adj) in res.items(): print(f'  {s:12s} closest pair {p[1]}/{p[2]}: {p[0]:.3f}   adjacent-step min {adj:.3f}   no fill vs 20: {d0:.3f}')
                print('  text contrast on step (step, foreground, primary-foreground):',txt)
    return out
def closest():
    """{(token set, theme): {simulation: (distance, step a, step b)}} for the five ramp steps."""
    return {k: {s: (v[0][0], v[0][1], v[0][2]) for s, v in res.items()} for k, (res, _) in run(verbose=False).items()}


if __name__ == '__main__':
    run()
    worst = min(d for sims in closest().values() for d, _, _ in sims.values())
    print(f'\nclosest pair over every token set, theme and simulation: {worst:.4f} OKLab (threshold 0.08)')
    sys.exit(0 if worst >= 0.08 else 1)
