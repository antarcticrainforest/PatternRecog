'''
Created on May 16, 2013

@author: Martin Bergemann
@institution: Monash University School of Mathemetics

@description: This python module should do the following:
    detect.coastline: detect the coastline of a given land-sea distribution
'''

import numpy as np
from netCDF4 import Dataset as nc
import scipy.ndimage as ndimage
import scipy.spatial as spatial
from scipy.ndimage.interpolation import spline_filter


def coastline(data,smooth_radius=2.5):
    """Explanation: this function finds coastlines in a slm-array
        smooth_radius = sigma-value for the canny algorithm
        data= the slm array
    """
    from skimage.feature import canny
    from skimage.morphology import convex_hull_image
    return canny(data, sigma=smooth_radius).astype(np.int8)

if __name__ == "__main__":
    f='/Users/bergem/Data/test/Maritim.nc'
    var="FR_LAND"
    File=nc(f)
    rotpole = File.variables['rotated_pole']
    rotpole = 0
    
    lon=File.variables['lon'][:]
    lat=File.variables['lat'][:]
    d=coastline(File.variables[var][:],smooth_radius=2)
    exit()
    from Plot import Plot
    plot=Plot(d,lon=lon,lat=lat,pole=[135,85])
    fig,ax,im,m=plot.map(cbar=False,rotpole=rotpole)
    fig.waitforbuttonpress()
    fig.show()
    
