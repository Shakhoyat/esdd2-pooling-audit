import numpy as np
rng=np.random.default_rng(0)
def curves(neg,pos,ts):
    neg=np.sort(neg); pos=np.sort(pos)
    F=1-np.searchsorted(neg,ts,side='left')/len(neg)   # s>=t
    R=np.searchsorted(pos,ts,side='left')/len(pos)     # s<t
    return F,R
def mm(neg,pos):
    ts=np.unique(np.r_[neg,pos,np.max(np.r_[neg,pos])+1]); F,R=curves(neg,pos,ts); v=np.maximum(F,R); i=np.argmin(v); return v[i],ts[i]
def mid(neg,pos):
    ts=np.unique(np.r_[neg,pos,np.max(np.r_[neg,pos])+1]); F,R=curves(neg,pos,ts); i=np.argmin(abs(F-R)); return (F[i]+R[i])/2,ts[i],abs(F[i]-R[i])
res=dict(naive_mm=0,bound_mm=0,naive_mid=0,bound_mid=0,mono_inv=0,dom=0); gaps=[]
T=3000
for k in range(T):
    nN,nA,n0=rng.integers(50,800,3); sep=rng.uniform(0,3)
    neg=rng.normal(0,1,nN); pa=rng.normal(sep,1,nA)
    if rng.random()<0.5: p0=np.full(n0,rng.normal(0,2))      # atom at c
    else: p0=rng.normal(rng.normal(0,2),rng.uniform(.1,2),n0)
    if rng.random()<0.3: neg=np.round(neg,1); pa=np.round(pa,1)   # ties
    P=np.r_[pa,p0]; w0=n0/(n0+nA)
    ea,_=mm(neg,pa); ep,t=mm(neg,P)
    F,Rp=curves(neg,P,np.array([t])); _,Ra=curves(neg,pa,np.array([t])); d0=Rp[0]-Ra[0]
    res['naive_mm']+=abs(ep-ea)>abs(d0)+1e-12; res['bound_mm']+=abs(ep-ea)>abs(d0)+abs(F[0]-Rp[0])+1e-12
    vp,tp,gp=mid(neg,P); va,ta,ga=mid(neg,pa); _,Rp2=curves(neg,P,np.array([tp])); _,Ra2=curves(neg,pa,np.array([tp])); d02=Rp2[0]-Ra2[0]
    res['naive_mid']+=abs(vp-va)>abs(d02)+1e-12; res['bound_mid']+=abs(vp-va)>abs(d02)+(gp+ga)/2+1e-12
    gaps.append(abs(F[0]-Rp[0]))
    # invariance to strictly increasing transform, and to any change of P0 scores
    f=lambda x: np.exp(0.7*x)+x**3
    res['mono_inv']+= abs(mm(f(neg),f(pa))[0]-ea)>1e-12
    # dominance: shift applicable positives up -> AC-EER must not increase
    res['dom']+= mm(neg,pa+rng.uniform(0,1))[0]>ea+1e-12
print(res, 'median pooled gap',np.median(gaps),'max',np.max(gaps))
