import re, sys, hashlib, time, json, os, requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
S3="https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
BASE="https://data.binance.vision/"
RAW="/home/ubuntu/mafe-data/raw"
NS="{http://s3.amazonaws.com/doc/2006-03-01/}"
sess=requests.Session()
def list_keys(prefix):
    keys=[];marker=""
    while True:
        r=sess.get(S3,params={"delimiter":"/","prefix":prefix,"marker":marker},timeout=60);r.raise_for_status()
        root=ET.fromstring(r.content)
        ks=[c.find(NS+"Key").text for c in root.findall(NS+"Contents")]
        keys+=ks
        if root.find(NS+"IsTruncated").text=="true":
            marker=root.find(NS+"NextMarker").text if root.find(NS+"NextMarker") is not None else ks[-1]
        else: break
    return [k for k in keys if k.endswith(".zip")]
def want(k):
    m=re.search(r"-(\d{4}-\d{2})(-\d{2})?\.zip$",k); ym=m.group(1); d=m.group(2)
    if "/monthly/" in k:
        if "fundingRate" in k: return True
        return "2020-01"<=ym<="2026-09"
    day=ym+(d or "")
    if "/daily/klines/" in k or "/daily/premiumIndexKlines/" in k: return day>="2026-10-01"
    return True
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()
def fetch(url,dst):
    with sess.get(url,stream=True,timeout=120) as r:
        if r.status_code!=200: raise RuntimeError(f"HTTP {r.status_code}")
        with open(dst+".part","wb") as f:
            for c in r.iter_content(1<<20): f.write(c)
    os.replace(dst+".part",dst)
def job(k):
    p=k.split("/"); ds=p[4]+("_1m" if "/1m/" in k else ""); sym=p[5]
    d=f"{RAW}/{ds}/{sym}"; os.makedirs(d,exist_ok=True)
    z=f"{d}/{os.path.basename(k)}"
    for attempt in range(5):
        try:
            if not os.path.exists(z): fetch(BASE+k,z)
            fetch(BASE+k+".CHECKSUM",z+".CHECKSUM")
            exp=open(z+".CHECKSUM").read().split()[0]
            if sha(z)==exp: return (k,"ok")
            os.remove(z); err="checksum mismatch"
        except Exception as e: err=str(e)
        time.sleep(2*(attempt+1))
    return (k,"FAIL "+err)
if __name__=="__main__":
    pre=[]
    for s in ("BTCUSDT","ETHUSDT"):
        pre+=[f"data/futures/um/monthly/klines/{s}/1m/",f"data/futures/um/daily/klines/{s}/1m/",
              f"data/futures/um/monthly/fundingRate/{s}/",f"data/futures/um/monthly/premiumIndexKlines/{s}/1m/",
              f"data/futures/um/daily/premiumIndexKlines/{s}/1m/",
              f"data/futures/um/daily/metrics/{s}/",f"data/futures/um/daily/bookDepth/{s}/"]
    keys=[]
    for p in pre:
        ks=[k for k in list_keys(p) if want(k)]; print(p,len(ks),flush=True); keys+=ks
    json.dump(keys,open("/home/ubuntu/mafe-data/keys.json","w"))
    fails=[]
    with ThreadPoolExecutor(4) as ex:
        for i,(k,st) in enumerate(ex.map(job,keys)):
            if st!="ok": fails.append((k,st)); print("REJECT",k,st,flush=True)
            if i%200==0: print(i,len(keys),flush=True)
    json.dump(fails,open("/home/ubuntu/mafe-data/rejects.json","w"))
    print("DONE fails",len(fails),flush=True)
