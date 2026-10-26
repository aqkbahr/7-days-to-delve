"""Read-only UnityFS header / first serialized-file diagnostics, no third-party dependency."""
import struct,sys,io
from pathlib import Path
def lz4(data,size):
    result=bytearray();i=0
    while i<len(data):
        token=data[i];i+=1;length=token>>4
        if length==15:
            while True:
                n=data[i];i+=1;length+=n
                if n!=255:break
        result.extend(data[i:i+length]);i+=length
        if i>=len(data):break
        offset=int.from_bytes(data[i:i+2],'little');i+=2;length=(token&15)+4
        if (token&15)==15:
            while True:
                n=data[i];i+=1;length+=n
                if n!=255:break
        assert offset>0
        for _ in range(length):result.append(result[-offset])
    assert len(result)==size,(len(result),size)
    return bytes(result)
def string(stream):
    result=bytearray()
    while True:
        c=stream.read(1)
        if c==b'\0':return result.decode(errors='replace')
        if not c:raise EOFError()
        result.extend(c)
def inspect(path):
    data=Path(path).read_bytes();s=io.BytesIO(data);signature=string(s);version=struct.unpack('>I',s.read(4))[0];unity=string(s);revision=string(s);size,compressed,uncompressed,flags=struct.unpack('>QIII',s.read(20))
    if version>=7:s.seek((s.tell()+15)//16*16)
    start=s.tell();info=s.read(compressed) if not flags&128 else data[-compressed:]
    info=lz4(info,uncompressed) if flags&63 in (2,3) else info
    b=io.BytesIO(info);b.read(16);count=struct.unpack('>I',b.read(4))[0];blocks=[struct.unpack('>IIH',b.read(10)) for _ in range(count)];files=struct.unpack('>I',b.read(4))[0];nodes=[]
    for _ in range(files):offset,length,f=struct.unpack('>QQI',b.read(20));nodes.append((offset,length,f,string(b)))
    body=start if flags&128 else start+compressed
    if flags&512:body=(body+15)//16*16
    first=blocks[0];chunk=data[body:body+first[1]];chunk=lz4(chunk,first[0]) if first[2]&63 in (2,3) else chunk
    print(path);print(dict(signature=signature,version=version,unity=unity,revision=revision,declared=size,actual=len(data),first_block=first,nodes=nodes[:4]));print('Serialized first header:',chunk[:120]);print('Serialized BE fields:',struct.unpack('>IIII',chunk[:16]))
if __name__=='__main__':
    for path in sys.argv[1:]:inspect(path)
