"""Bind checks to the bytes served and publish completed artifacts atomically."""
from contextlib import contextmanager
import hashlib,json,os,tempfile
from pathlib import Path

def verified_response_sha(response,local_path):
    if response is None or response.status!=200:
        raise ValueError('Studio main document did not return HTTP 200')
    served=hashlib.sha256(response.body()).hexdigest()
    local=hashlib.sha256(Path(local_path).read_bytes()).hexdigest()
    if served!=local:
        raise ValueError('--url serves different HTML than --out; verification rejected')
    return served

@contextmanager
def temporary_video(target):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    handle=tempfile.NamedTemporaryFile(prefix='.prometheus-render-',suffix='.mp4',dir=target.parent,delete=False)
    path=Path(handle.name);handle.close()
    try:yield path
    finally:path.unlink(missing_ok=True)

def atomic_json(path,data):
    path=Path(path);handle=tempfile.NamedTemporaryFile(prefix='.verification-',suffix='.json',dir=path.parent,mode='w',encoding='utf-8',delete=False)
    temp=Path(handle.name)
    try:
        with handle:json.dump(data,handle,indent=2);handle.write('\n')
        os.replace(temp,path)
    finally:temp.unlink(missing_ok=True)
