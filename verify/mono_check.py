from fractions import Fraction as Fr
from itertools import product
def rates(neg,pos,t): return Fr(sum(s>=t for s in neg),len(neg)), Fr(sum(s<t for s in pos),len(pos))
def ts(neg,pos): u=sorted(set(neg)|set(pos)); return u+[u[-1]+1]
def mm(neg,pos): return min(max(*rates(neg,pos,t)) for t in ts(neg,pos))
def mid(neg,pos):
    g=[(abs(F-R),(F+R)/2) for t in ts(neg,pos) for F,R in [rates(neg,pos,t)]]; m=min(x[0] for x in g)
    return [v for d,v in g if d==m]
vm=vmid=0; ex=None
G=range(4)
for neg in product(G,repeat=3):
  for pa in product(G,repeat=3):
    e=mm(neg,pa); md=mid(neg,pa)
    for i in range(3):                     # raise one positive score by 1
        pb=list(pa); pb[i]+=1; pb=tuple(pb)
        if mm(neg,pb)>e: vm+=1
        if max(mid(neg,pb))>min(md): vmid+=1; ex=ex or (neg,pa,pb,md,mid(neg,pb))
print('minimax monotonicity violations',vm,' midpoint-scorer violations',vmid,' example',ex)
def mid_first(neg,pos,rev):
    L=[(abs(F-R),(F+R)/2) for t in (ts(neg,pos)[::-1] if rev else ts(neg,pos)) for F,R in [rates(neg,pos,t)]]
    m=min(x[0] for x in L); return next(v for d,v in L if d==m)
for rev in (False,True):
    v=0
    for neg in product(G,repeat=3):
      for pa in product(G,repeat=3):
        e=mid_first(neg,pa,rev)
        for i in range(3):
            pb=list(pa); pb[i]+=1
            if mid_first(neg,tuple(pb),rev)>e: v+=1
    print('deterministic tie-break rev=',rev,'violations',v)
