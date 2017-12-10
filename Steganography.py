import sys
import re
import numpy as np
import base64
import zlib
from scipy.misc import *
import imageio as io
from PIL import Image


class Payload:

    def __init__(self, rawData=None, compressionLevel=-1, json=None):
        if (rawData is None and json is None):
            raise ValueError('Both rawData and json are empty!')
        if compressionLevel < -1 or compressionLevel > 9:
            raise ValueError('Wrong compressionLevel value!')
        if json is None:
            if  type(rawData) is not np.ndarray:
                raise TypeError('Wrong type for rawData')
        if rawData is None:
            if type(json) is not str:
                raise TypeError('Wrong type for json')
        if isinstance(rawData, np.ndarray):
            self.rawData = rawData
            self.json = self.gen_json(compressionLevel)
        if isinstance(json,str):
            self.json = json
            self.rawData = self.gen_rawData()



    def gen_rawData(self):
        expr1 = r"{\"type\":\"(?P<type>color|gray|text)\","""
        m1 = re.match(expr1,self.json)
        if m1 is not None:
            if m1.group('type') == 'text':
                expr2 = r"\"size\":\"(?P<size0>null),\"isCompressed\":(?P<iscomp>true|false),\"content\":\"(?P<content>.+)\"}" #json
            else:
                expr2 = r"\"size\":\"(?P<size0>\d+),(?P<size1>\d+)\",\"isCompressed\":(?P<iscomp>true|false),\"content\":\"(?P<content>.+)\"}" #json
        m2 = re.match(expr2,self.json)
        if m2 is not None:
            content = m2.group('content')
            decon = base64.b64decode(content)
        #print (len(decon))
        if m2 is not None:
            if m2.group('iscomp') == 'false':
                connew = decon
            else:
                connew = zlib.decompress(decon)
        if m1 is not None:
            if m1.group('type') == 'text':
                temp = np.array(list(connew), dtype=unit8)
            elif m1.group('type') == 'gray':
                ians = np.array(list(connew),dtype=np.unit8)
                temp = np.resize(ians,(int(m2.group('size0')),int(m2.group('size1'))))
            else:
                ians = np.array(list(connew), dtype=np.uint8)
                temp = np.resize(ians,(int(m2.group('size0')),int(m2.group('size1')),3))
            self.rawData = temp
            return self.rawData

    def gen_json(self,compressionLevel):
        #type
        if self.rawData.ndim == 3:
            tdata = 'color'
        elif self.rawData.ndim == 2:
            tdata = 'gray'
        else:
            tdata = 'text'
        #content and compress boolean
        flat = self.rawData.flatten()

        if compressionLevel == -1:
            com = 'false'
            fdata = flat

        else:
            com = "true"
            fdata = zlib.compress(flat,compressionLevel)

        # base64 conversion for size and content
        content = str(base64.b64encode(fdata))
        content = content[2:]
        content = content[:-1]

        if self.rawData.ndim != 1:
            self.json = '{'
            self.json += '"type"' + ':'
            self.json += '"{}"'.format(tdata)
            self.json += ',' + '"size"' + ':'
            self.json += '"{}'.format(self.rawData.shape[0])
            self.json += ","
            self.json += '{}"'.format(self.rawData.shape[1])
            self.json += ',' + '"isCompressed"' + ':'
            self.json += '{}'.format(com)
            self.json += ','
            self.json += '"content'
            self.json += '"' + ':'
            self.json += '"{}"'.format(content)
            self.json += '}'

        else:
            self.json = '{'
            self.json += '"type"' + ':'
            self.json += '"{}"'.format(tdata)
            self.json += ',' + '"size"' + ':'
            self.json += 'null'
            self.json += ',' + '"isCompressed"' + ':'
            self.json += '{}'.format(com)
            self.json += ','
            self.json += '"content'
            self.json += '"' + ':'
            self.json += '"{}"'.format(content)
            self.json += '}'
        return self.json
        #with open('test.json','w') as myFile:
        #    myFile.write(self.json)


class Carrier:

    def __init__(self, img):
        if type(img) is not np.ndarray:
            raise TypeError('Wrong type for img!')
        if img.shape[2] != 4 or img.ndim != 3:
            raise ValueError('Wrong dimensions or channels!')
        self.img = img


    def payloadExists(self):
        result = []
        ch = ''
        test = '{"type":'
        for i in range(8):
            l = []
            data = self.img[0,i]
            r = np.unpackbits(data[0])[6:8]
            g = np.unpackbits(data[1])[6:8]
            b = np.unpackbits(data[2])[6:8]
            a = np.unpackbits(data[3])[6:8]
            l.append(a[0])
            l.append(a[1])
            l.append(b[0])
            l.append(b[1])
            l.append(g[0])
            l.append(g[1])
            l.append(r[0])
            l.append(r[1])
            letter = np.array(l)
            letter = np.packbits(letter)
            ch += chr(letter)

        if test == ch:
            return True
        else:
            return False

    def clean(self):
        c = np.copy(self.img)
        a = (self.img & 0b11)
        np.random.shuffle(a)
        return (c & ~a)

    def embedPayload(self, payload, override=False):
        if type(payload) is not Payload:
            raise TypeError("Wrong type for payload!")
        if len(payload.json) > 4 * len(self.img.flatten()):
            raise ValueError("Payload larger than carrier!")
        if override is not True:
            if self.payloadExists():
                raise Exception("Carrier cannot be overwritten!")

        put = np.fromstring(payload.json,dtype=np.uint8)

        c = np.copy(self.img)
        change = int(c.size/(self.img.shape[0]*self.img.shape[1]))
        c.shape = (self.img.shape[0]*self.img.shape[1],change)


        for i in range(len(put)):
            p1 = np.unpackbits(put[i])
            pnew = np.pad(p1, (8-len(p1), 0), 'constant')
            r = np.unpackbits(c[i][0])
            g = np.unpackbits(c[i][1])
            b = np.unpackbits(c[i][2])
            a = np.unpackbits(c[i][3])

            r[6:8] = pnew[6:8]
            g[6:8] = pnew[4:6]
            b[6:8] = pnew[2:4]
            a[6:8] = pnew[0:2]

            c[i][0] = np.packbits(r)
            c[i][1] = np.packbits(g)
            c[i][2] = np.packbits(b)
            c[i][3] = np.packbits(g)

        return (c.reshape(self.img.shape))



    def extractPayload(self):
        if  not self.payloadExists():
            raise Exception("No payload!")
        payload = Payload
        ch = ''
        put = np.fromstring(payload.json,dtype=np.uint8)

        for i in range(len(put)):
            l = []
            data = self.img[0,i]
            r = np.unpackbits(data[0])[6:8]
            g = np.unpackbits(data[1])[6:8]
            b = np.unpackbits(data[2])[6:8]
            a = np.unpackbits(data[3])[6:8]
            l.append(a[0])
            l.append(a[1])
            l.append(b[0])
            l.append(b[1])
            l.append(g[0])
            l.append(g[1])
            l.append(r[0])
            l.append(r[1])
            letter = np.array(l)
            letter = np.packbits(letter)
            ch += chr(letter)
        return Payload(json=ch)

if __name__ == "__main__":
    #with open('data/payload3.txt', 'r') as File:
    #   arr1 = File.read()
    #aee = np.fromstring(arr1,dtype=np.uint8)

    #with open('data/payload1.json', 'r') as File:
    #    arr1 = File.readlines()

    #arr1 = "".join(arr1)
    #arr = list(arr)
    #a = np.array(list(arr))


    #arr1 =  np.loadtxt('data/payload1.json',dtype='str')
    #print (type(arr1))
    arr = np.asarray(Image.open('data/carrier.png'))
    arr1 = np.asarray(Image.open('data/payload1.png'))
    #print (arr)
    #x = '{"type":"color","size":"360,640","isCompressed":true,"content":"VGhlIEVDRTM2NCBQcm9qZWN0"}'
    y = Payload(arr1,5,None)#7 for 2

    a = Carrier(arr)
    Carrier.payloadExists(a)
    Carrier.clean(a)
    Carrier.embedPayload(a,y,True)





