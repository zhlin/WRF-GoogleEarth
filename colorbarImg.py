'''
A script that dynamically generates log scaled color bar images from a NetCDF dataset for each step with data.

Requires matplotlib and Scientific python.

Use as follows:

import colorbarImg
colorbarImg.getImages('wrfout.nc','FGRNHFX')
'''

from Scientific.IO import NetCDF
import pylab
import scipy
from numpy import *
from matplotlib import pyplot, mpl
from matplotlib.colors import LogNorm
from matplotlib.colorbar import ColorbarBase
from matplotlib.ticker import LogFormatter
import shutil,os

def getImages(filename,vname):
    file=NetCDF.NetCDFFile(filename,'r')
    vdata=file.variables[vname] 
    vsize=vdata.shape[0]
	# create empty files subdirectory for output images
    try:
        shutil.rmtree('colorbarImages')
    except:
        pass
    os.makedirs('colorbarImages')
	# go through the whole dataset and generate a color bar image for each step
    for i in range(vsize):
        varray = vdata[i,:,:,]
        data=pylab.flipud(varray)
        pylab.imshow(data, norm=LogNorm())
        imgNum = 'TimeStep_'+ str(i)	
    	if len(data[data>0])>0:
	    #make a new figure that contains the colorbar
    	    fig=pylab.figure(figsize=(2,5))
    	    ax1 = fig.add_axes([0.35, 0.03, 0.1, 0.9])
    	    vmin=data[data>0].min()
    	    vmax=data.max()
    	    norm = LogNorm(vmin,vmax)
	    #make the colorbar in log scale
    	    logFormatter=LogFormatter(10, labelOnlyBase=False)
    	    cb1 = ColorbarBase(ax1,norm=norm,format=logFormatter,spacing='proportional', orientation='vertical')
	    imgName='colorbarImages/%s.png' %imgNum
    	    fig.savefig(imgName, bbox_inches='tight')
