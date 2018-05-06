import os
from astropy.io import fits
from scottSock import scottSock

def to_dataserver( fname, outfile='test.fits', clobber=True ):

	fitsfd = fits.open( fname )
		

        width = 0
        height = 0
        for ext in fitsfd:
                if hasattr( ext, 'data' ):
                        if ext.data is not None:
                                width+=ext.data.shape[0]
                                height+=ext.data.shape[1]

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


