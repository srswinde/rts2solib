import os
from astropy.io import fits
from scottSock import scottSock
import sys
import numpy as np


NOPIL = False
try:
    from PIL import Image
    from PIL import ImageFont
    from PIL import ImageDraw

except Exception as err:
    NOPIL=True


def to_jpg(fname):
    if NOPIL:
        raise ImportError("This function is not available b/c we can not import PIL")

    fd = fits.open(fname)

    arr = np.hstack((fd[1].data, fd[2].data))
    arr = np.log(arr)
    arr = arr/arr.max()
    arr = (255*arr).astype("uint8")
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    #font = ImageFont.truetype("sans-serif.ttf", 16)
    draw.text((0, 0),fname.split("/")[-1],(255,255,255))
    return img



def to_dataserver( fname, outfile='test.fits', clobber=True ):

    fitsfd = fits.open( fname )


    width = 0
    height = 0
    for ext in fitsfd:
        if hasattr( ext, 'data' ):
            if ext.data is not None or ext.data is not []:
                try:
                    width+=ext.data.shape[0]
                    height+=ext.data.shape[1]
                except Exception as err:
                    print(" log E err is {} ext.data is {}".format(err, ext.data))

    fitsfd.close()
    fsize = os.stat(fname).st_size

    fd = open(fname, 'rb')


    if clobber:
            clobber_char = '!'
    else:
            clobber_char = ''
    meta = "          {} {}{} 1 {} {} 0".format( fsize, clobber_char, '/home/rts2obs/data/rts2'+outfile, width, height )
    meta = meta + (256-len(meta))*' '

    data = meta+fd.read()
    lendata = len(data)
    soc = scottSock( '10.30.1.1', 6543 )

    counter = 0
    socsize = 1024
    buffsize = 0
    while buffsize < len(data):
        sent = soc.send( data[buffsize:buffsize+1024] )
        buffsize+=sent


