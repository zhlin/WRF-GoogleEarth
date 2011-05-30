#!/usr/bin/env python

'''
A simple python module for creating images out of netcdf arrays and outputing
kml files for Google Earth.   The base class ncEarth cannot be used on its own,
it must be subclassed with certain functions overloaded to provide location and
plotting that are specific to a model's output files.

Requires matplotlib and Scientific python.

Use as follows:

import ncEarth
kml=ncEarth.ncEpiSim('episim_0010.nc')
kml.write_kml(['Susceptible','Infected','Recovered','Dead'])

or

kmz=ncEarth.ncWRFFire_mov('wrfout')
kmz.write('FGRNHFX','fire.kmz')

Author: Jonathan Beezley (jon.beezley@gmail.com)
Date: Oct 5, 2010

kmz=ncEarth.ncWRFFire_mov('wrfout')
kmz.write_preload('FGRNHFX')

Modified verison does not require 'wrfout_times' file and it preloads the GroundOverlays
in the .kmz file.

Modified by Lin Zhang
Date: Dec 20, 2010 
'''

from matplotlib import pylab
import numpy as np
from Scientific.IO import NetCDF
import cStringIO
from datetime import datetime
import zipfile
import shutil,os

class ncEarth(object):
    
    '''Base class for reading NetCDF files and writing kml for Google Earth.'''
    
    kmlname='ncEarth.kml'  # default name for kml output file
    progname='baseClass'   # string describing the model (overload in subclass)
    
    # base kml file format string
    # creates a folder containing all images
    kmlstr= \
    '''<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
    <Folder>
    <name>%(prog)s visualization</name>
    <description>Variables from %(prog)s output files visualized in Google Earth</description>
    %(content)s
    </Folder>
    </kml>'''
    
    # format string for each image
    kmlimage= \
    '''<GroundOverlay>
      <name>%(name)s</name>
      <color>8fffffff</color>
      <Icon>
        <href>%(filename)s</href>
        <viewBoundScale>0.75</viewBoundScale>
      </Icon>
      <altitude>0.0</altitude>
      <altitudeMode>clampToGround</altitudeMode>
      <LatLonBox>
        <north>%(lat2)f</north>
        <south>%(lat1)f</south>
        <east>%(lon2)f</east>
        <west>%(lon1)f</west>
        <rotation>0.0</rotation>
      </LatLonBox>
      %(time)s
    </GroundOverlay>'''

    # string for static Ground Overlays
    kmlimageStatic= \
    '''<GroundOverlay>
    <name>%(name)s</name>
    <color>08ffffff</color> #Have to play with the color of the layers
    <Icon>
    <href>%(filename)s</href>
    <viewBoundScale>0.75</viewBoundScale>
    </Icon>
    <altitude>0.0</altitude>
    <altitudeMode>clampToGround</altitudeMode>
    <LatLonBox>
    <north>%(lat2)f</north>
    <south>%(lat1)f</south>
    <east>%(lon2)f</east>
    <west>%(lon1)f</west>
    <rotation>0.0</rotation>
    </LatLonBox>
    </GroundOverlay>'''

    # time interval specification for animated output
    timestr=\
    '''<TimeSpan>
    %(begin)s
    %(end)s
    </TimeSpan>'''
    
    beginstr='<begin>%s</begin>'
    endstr='<end>%s</end>'
  
    def __init__(self,filename,hsize=5):
        '''Class constructor:
           filename : string NetCDF file to read
           hsize : optional, width of output images in inches'''
        self.filename = filename
        self.f=NetCDF.NetCDFFile(filename,'r')
        self.hsize=hsize
    
    def get_bounds(self):
        '''Return the latitude and longitude bounds of the image.  Must be provided
        by the subclass.'''
        raise Exception("Non-implemented base class method.")
    
    def get_array(self,vname):
        '''Return a given array from the output file.  Must be returned as a
        2D array with top to bottom orientation (like an image).'''
        v=self.f.variables[vname]
        v=pylab.flipud(v)
        return v
    
    def view_function(self,v):
        '''Any function applied to the image data before plotting.  For example,
        to show the color on a log scale.'''
        return v
    
    def get_image(self,v):
        '''Create an image from a given data.  Returns a png image as a string.'''
                
        # kludge to get the image to have no border
        fig=pylab.figure(figsize=(self.hsize,self.hsize*float(v.shape[0])/v.shape[1]))
        ax=fig.add_axes([0,0,1,1])
        
        pylab.imshow(self.view_function(v))
        pylab.axis('off')
        self.process_image()
        
        # create a string buffer to save the file
        im=cStringIO.StringIO()
        
        pylab.savefig(im,format='png')
        
        # return the buffer
        return im.getvalue()
    
    def process_image(self):
        '''Do anything to the current figure window before saving it as an image.'''
        pass
    
    def get_kml_dict(self,name,filename):
        '''returns a dictionary of relevant info the create the image
        portion of the kml file'''
        
        lon1,lon2,lat1,lat2=self.get_bounds()
        d={'lat1':lat1,'lat2':lat2,'lon1':lon1,'lon2':lon2, \
           'name':name,'filename':filename,'time':self.get_time()}
        return d

    def get_static_kml_dict(self,name,filename):
        '''returns a dictionary of relevant info the create the image
        portion of the kml file'''
        
        lon1,lon2,lat1,lat2=self.get_bounds()
        d={'lat1':lat1,'lat2':lat2,'lon1':lon1,'lon2':lon2, \
           'name':name,'filename':filename}
        return d
     
    def get_time(self):
        '''Return the time interval information for this image using the kml
        format string `timestr'.  Or an empty string to disable animations.'''
        return ''
    
    def image2kml(self,varname,filename=None):
        '''Read data from the NetCDF file, create a psuedo-color image as a png,
        then create a kml string for displaying the image in Google Earth.  Returns
        the kml string describing the GroundOverlay.  Optionally, the filename
        used to write the image can be specified, otherwise a default will be used.'''
        
        vdata=self.get_array(varname)
        im=self.get_image(vdata)
        if filename is None:
            filename='%s.png' % varname
        f=open(filename,'w')
        f.write(im)
        f.close()
        d=self.get_kml_dict(varname,filename)
        pylab.close('all')
        return self.__class__.kmlimage % d

    def image2kmlStatic(self,varname,filename=None):
        '''Read data from the NetCDF file, create a psuedo-color image as a png,
	then create a kml string for displaying the image in Google Earth. Returns
	the kml string describing the GroundOverlay. Optionally, the filename
	used to write the image can be specified, otherwise a default will be used.'''
        
        vdata=self.get_array(varname)
        im=self.get_image(vdata)
        if filename is None:
            filename='%s.png' % varname
        f=open(filename,'w')
        f.write(im)
        f.close()
        d=self.get_static_kml_dict(varname,filename)
        pylab.close('all')
        return self.__class__.kmlimageStatic % d

    def write_kml(self,varnames):
        '''Create the actual kml file for a list of variables by calling image2kml
        for each variable in a list of variable names.'''
        if type(varnames) is str:
            varnames=(varnames,)
        content=[]
        for varname in varnames:
            content.append(self.image2kml(varname))
        kml=self.__class__.kmlstr % \
                     {'content':'\n'.join(content),\
                      'prog':self.__class__.progname}
        f=open(self.__class__.kmlname,'w')
        f.write(kml)
        f.close()

class ncEpiSim(ncEarth):
    '''Epidemic model file class.'''
    
    kmlname='epidemic.kml'
    progname='EpiSim'
    
    def get_bounds(self):
        '''Get the lat/lon bounds of the output file... assumes regular lat/lon (no projection)'''
        lat=self.f.variables['latitude']
        lon=self.f.variables['longitude']
        
        lat1=lat[0]
        lat2=lat[-1]
        lon1=lon[0]
        lon2=lon[-1]
        
        return (lon1,lon2,lat1,lat2)
    
    def view_function(self,a):
        '''We display populations in log scale so they look better'''
        return pylab.log(a)

class ncWRFFire(ncEarth):
    '''WRF-Fire model file class.'''
    
    kmlname='fire.kml'
    progname='WRF-Fire'
    wrftimestr='%Y-%m-%d_%H:%M:%S'

    def __init__(self,filename,hsize=5,istep=0):
        '''Overloaded constructor for WRF output files:
           filename : output NetCDF file
           hsize : output image width in inches
           istep : time slice to output (between 0 and the number of timeslices in the file - 1)'''
        ncEarth.__init__(self,filename,hsize)
        self.istep=istep
    
    def get_bounds(self):
        '''Get the latitude and longitude bounds for an output domain.  In general,
        we need to reproject the data to a regular lat/lon grid.  This can be done
        with matplotlib's BaseMap module, but is not done here.'''
        
        lat=self.f.variables['XLAT']
        lon=self.f.variables['XLONG']
        lat1=np.min(lat)
        lat2=np.max(lat)
        lon1=np.min(lon)
        lon2=np.max(lon)
        return (lon1,lon2,lat1,lat2)
    
    def get_array(self,vname):
        '''Return a single time slice of a variable from a WRF output file.'''
        v=self.f.variables[vname]
        v=v[self.istep,:,:]
        v=pylab.flipud(v)
        return v
    
    def get_time(self):
        '''Process the time information from the WRF output file to create a
        proper kml TimeInterval specification.'''
        start=''
        end=''
        time=''
        times=self.f.variables["Times"]
        if self.istep > 0:
            start=ncEarth.beginstr % \
               datetime.strptime(times[self.istep,:].tostring(),\
                                     self.__class__.wrftimestr).isoformat()
        if self.istep < times.shape[0]-1:
            end=ncEarth.endstr % \
               datetime.strptime(times[self.istep+1,:].tostring(),\
                                     self.__class__.wrftimestr).isoformat()
        if start is not '' or end is not '':
            time=ncEarth.timestr % {'begin':start,'end':end}
        return time
    
    def view_function(self,v):
        return pylab.log(v)

class ncWRFFire_mov(object):
    
    '''A class the uses ncWRFFire to create animations from WRF history output file.'''
    
    def __init__(self,filename,hsize=5,nstep=None):
        '''Class constructor:
           filename : NetCDF output file name
           hsize : output image width in inces
           nstep : the number of frames to process (default all frames in the file)'''
        
        self.filename=filename
	
        f=NetCDF.NetCDFFile(filename,'r')
        #g=NetCDF.NetCDFFile('wrfout_times','r')
        self.nstep=nstep
        if nstep is None:
            # in case nstep was not specified read the total number of time slices from the file
            self.nstep=f.variables['Times'].shape[0]

    def write_preload(self,vname,kmz='fire_preload.kmz'):
        '''Create a kmz file from multiple time steps of a wrfout file. The kml file consists of a set of
	GroundOverlays with time tag and a copy of the set without the time tag to preload the
	images that are used in the GroundOverlays.'''
        
        
        imgs=[] # to store a list of all images created
        content=[] # the content of the main kml
        vstr='files/%s_%05i.png' # format specification for images (all stored in `files/' subdirectory)
        
        # create empty files subdirectory for output images
        try:
            shutil.rmtree('files')
        except:
            pass
            os.makedirs('files')
        
        # loop through all time slices and create the image data
        # appending to the kml content string for each image
        for i in xrange(0,self.nstep,1):
            print i
            kml=ncWRFFire(self.filename,istep=i)
            img=vstr % (vname,i)
            imgs.append(img)
            content.append(kml.image2kmlStatic(vname,img))

	for i in xrange(0,self.nstep,1):
            print i
            kml=ncWRFFire(self.filename,istep=i)
            img=vstr % (vname,i)
            imgs.append(img)
            content.append(kml.image2kml(vname,img))

        # create the main kml file
        kml=ncWRFFire.kmlstr % \
            {'content':'\n'.join(content),\
             'prog':ncWRFFire.progname}
        
        # create a zipfile to store all images + kml into a single compressed file
        z=zipfile.ZipFile(kmz,'w',compression=zipfile.ZIP_DEFLATED)
        z.writestr(kmz[:-3]+'kml',kml)
        for img in imgs:
            z.write(img)
        z.close()
    
    def write(self,vname,kmz='fire.kmz'):
        '''Create a kmz file from multiple time steps of a wrfout file.
        vname : the variable name to visualize
        kmz : optional, the name of the file to save the kmz to'''
        
        imgs=[]     # to store a list of all images created
        content=[]  # the content of the main kml
        vstr='files/%s_%05i.png' # format specification for images (all stored in `files/' subdirectory)
        
        # create empty files subdirectory for output images
        try:
            shutil.rmtree('files')
        except:
            pass
        os.makedirs('files')
        
        # loop through all time slices and create the image data
        # appending to the kml content string for each image
        for i in xrange(0,self.nstep,1):
            print i
            kml=ncWRFFire(self.filename,istep=i)
            img=vstr % (vname,i)
            imgs.append(img)
            content.append(kml.image2kml(vname,img))
        
        # create the main kml file
        kml=ncWRFFire.kmlstr % \
            {'content':'\n'.join(content),\
             'prog':ncWRFFire.progname}
        
        # create a zipfile to store all images + kml into a single compressed file
        z=zipfile.ZipFile(kmz,'w',compression=zipfile.ZIP_DEFLATED)
        z.writestr(kmz[:-3]+'kml',kml)
        for img in imgs:
            z.write(img)
        z.close()