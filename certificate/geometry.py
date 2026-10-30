"""Kamp conventions: circumradius-1 inner polygons; clockwise angles from +y.
This is a floating-point DISCOVERY/DIAGNOSTIC kernel, not a proof checker.
"""
from pathlib import Path
import numpy as np

def load(path):
    lines=Path(path).read_text().splitlines()
    l,m,n=map(int,lines[0].split()); R=float(lines[1]); q=np.loadtxt(lines[2:]).reshape(n,3)
    return l,m,n,R,q

def local_vertices(m,theta):
    offsets=(np.arange(m)+((m-1)%2)/2)*2*np.pi/m
    a=np.asarray(theta)[...,None]+offsets
    return np.stack([np.sin(a),np.cos(a)],axis=-1)

def vertices(q,m):
    return q[:,:2,None].transpose(0,2,1)+local_vertices(m,q[:,2])

def normals(l):
    a=np.arange(l)*2*np.pi/l
    return np.stack([np.sin(a),np.cos(a)],axis=-1) # inward

def boundary_vertices(l,R,delta=None):
    # Recover polygon from adjacent inward halfplane boundaries.
    N=normals(l); b=R*np.cos(np.pi/l)+np.zeros(l)
    if delta is not None: b=b+delta
    return np.array([np.linalg.solve(np.stack([N[k],N[(k+1)%l]]),-b[[k,(k+1)%l]]) for k in range(l)])

def separating_gaps(v):
    n=len(v); i,j=np.triu_indices(n,1)
    edge=np.roll(v,-1,axis=1)-v
    N=np.stack([-edge[...,1],edge[...,0]],axis=-1)
    N=N/np.linalg.norm(N,axis=-1)[...,None]
    axes=np.concatenate([N[i],N[j]],axis=1)
    pi=np.einsum('ped,pvd->pev',axes,v[i]); pj=np.einsum('ped,pvd->pev',axes,v[j])
    forward=pj.min(axis=2)-pi.max(axis=2)
    back=pi.min(axis=2)-pj.max(axis=2)
    allg=np.concatenate([forward,back],axis=1)
    ix=allg.argmax(axis=1); k=ix%axes.shape[1]
    witness=axes[np.arange(len(i)),k]*np.where(ix<axes.shape[1],1.,-1.)[:,None]
    return allg.max(axis=1),witness,i,j

def constraints(z,l,m,n,delta=None):
    q=z[:-1].reshape(n,3);R=z[-1];v=vertices(q,m)
    wall=np.einsum('kd,ivd->ikv',normals(l),v)+R*np.cos(np.pi/l)
    if delta is not None: wall=wall+delta[None,:,None]
    g,_,_,_=separating_gaps(v)
    return np.r_[wall.ravel(),g]

def diagnose(l,m,n,R,q):
    from shapely.geometry import Polygon
    v=vertices(q,m); walls=np.einsum('kd,ivd->ikv',normals(l),v)+R*np.cos(np.pi/l)
    g,a,i,j=separating_gaps(v)
    polys=[Polygon(vv) for vv in v];out=Polygon(boundary_vertices(l,R))
    overlap=max(polys[ii].intersection(polys[jj]).area for ii,jj in zip(i,j))
    outside=max(p.difference(out).area for p in polys)
    unit_side=R*np.sin(np.pi/l)/np.sin(np.pi/m)
    density=n*m*np.sin(2*np.pi/m)/(l*R*R*np.sin(2*np.pi/l))
    return dict(R=R,outer_side_for_unit_side_pieces=unit_side,area_fraction=density,
      min_wall_gap=float(walls.min()),min_pair_separating_gap=float(g.min()),
      max_pair_intersection_area=float(overlap),max_outside_area=float(outside),
      near_contact_pairs=[(int(ii),int(jj)) for ii,jj,gg in zip(i,j,g) if gg<1e-6],
      near_wall_contacts=[(int(ii),int(k)) for ii,k in zip(*np.where(walls.min(axis=2)<1e-6))])

if __name__=='__main__':
    import json
    root=Path(__file__).parent; out={}
    for f in sorted((root/'baselines').glob('*.txt')):
        l,m,n,R,q=load(f);d=diagnose(l,m,n,R,q);out[f.stem]=d
        print(f.stem,json.dumps({k:v for k,v in d.items() if not k.startswith('near_')}))
    (root/'baseline_diagnostics.json').write_text(json.dumps(out,indent=2)+'\n')
