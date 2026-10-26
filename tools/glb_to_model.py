#!/usr/bin/env python3
"""cad/model/NCPK_nasos.glb -> src/ustroystvo/model.json + model.bin (для 3D на странице «Устройство насоса»).
Примитивы каждой детали сливаются в один, координаты квантуются в uint16 по общему габариту, нормали — в int8."""
import json, struct, os, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
f=open(os.path.join(ROOT,'cad','model','NCPK_nasos.glb'),'rb').read()
L=struct.unpack('<I',f[12:16])[0]; j=json.loads(f[20:20+L])
bin0=20+L; BL=struct.unpack('<I',f[bin0:bin0+4])[0]; B=f[bin0+8:bin0+8+BL]
CT={5126:np.float32,5125:np.uint32,5123:np.uint16,5121:np.uint8}
NC={'SCALAR':1,'VEC3':3,'VEC2':2,'VEC4':4}
def acc(i):
    a=j['accessors'][i]; bv=j['bufferViews'][a['bufferView']]
    off=bv.get('byteOffset',0)+a.get('byteOffset',0); n=a['count']*NC[a['type']]
    return np.frombuffer(B,CT[a['componentType']],n,off).reshape(a['count'],NC[a['type']]) if NC[a['type']]>1 else np.frombuffer(B,CT[a['componentType']],n,off)
parts=[];blob=bytearray()
allp=[]
for n in j['nodes'][1:]:
    m=j['meshes'][n['mesh']]; P=[];N=[];I=[];o=0;mat=None
    for p in m['primitives']:
        pos=acc(p['attributes']['POSITION']).astype(np.float64); nor=acc(p['attributes']['NORMAL'])
        idx=acc(p['indices']).astype(np.int64)
        P.append(pos);N.append(nor);I.append(idx+o);o+=len(pos);mat=p.get('material',mat)
    P=np.concatenate(P);N=np.concatenate(N);I=np.concatenate(I)
    t=n.get('translation',[0,0,0]); P=P+np.array(t)
    col=j['materials'][mat]['pbrMetallicRoughness'].get('baseColorFactor',[.7,.7,.7,1])
    allp.append(P); parts.append(dict(name=n['name'],P=P,N=N,I=I,col=col))
ap=np.concatenate(allp); lo=ap.min(0); hi=ap.max(0); sc=(hi-lo)/65535
meta=[]
def put(arr):
    global blob
    while len(blob)%4: blob.append(0)
    o=len(blob); blob+=arr.tobytes(); return o
for p in parts:
    q=np.round((p['P']-lo)/sc).astype(np.uint16)
    nn=p['N']/np.maximum(np.linalg.norm(p['N'],axis=1,keepdims=True),1e-9)
    qn=np.round(nn*127).astype(np.int8)
    idx=p['I'].astype(np.uint16 if len(q)<65536 else np.uint32)
    meta.append(dict(name=p['name'],col=[round(c,3) for c in p['col'][:3]],nv=len(q),ni=len(idx),i32=idx.dtype==np.uint32,
        p=put(q),n=put(qn),i=put(idx)))
out=dict(lo=lo.tolist(),sc=sc.tolist(),parts=meta)
open(os.path.join(ROOT,'src','ustroystvo','model.json'),'w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False))
open(os.path.join(ROOT,'src','ustroystvo','model.bin'),'wb').write(bytes(blob))
print(len(blob),sum(m['nv'] for m in meta),sum(m['ni'] for m in meta)//3, lo,hi)
