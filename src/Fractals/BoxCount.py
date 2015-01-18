'''
Created on Jun 3, 2013

@author: Martin Bergemann
@institution: School of Mathematical Sciences, Monash University
@purpose: Box-Counting purpose
'''
import numpy as np
import scipy.ndimage as ndimage
import scipy.spatial as spatial
import scipy.misc as misc

from scipy import polyfit , polyval
class BBox(object):
    def __init__(self, x1, y1, x2, y2):
        '''
        (x1, y1) is the upper left corner,
        (x2, y2) is the lower right corner,
        with (0, 0) being in the upper left corner.
        '''
        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
    def taxicab_diagonal(self):
        '''
        Return the taxicab distance from (x1,y1) to (x2,y2)
        '''
        return self.x2 - self.x1 + self.y2 - self.y1
    def overlaps(self, other):
        '''
        Return True iff self and other overlap.
        '''
        return not ((self.x1 > other.x2)
                    or (self.x2 < other.x1)
                    or (self.y1 > other.y2)
                    or (self.y2 < other.y1))
    def __eq__(self, other):
        return (self.x1 == other.x1
                and self.y1 == other.y1
                and self.x2 == other.x2
                and self.y2 == other.y2)

def slice_to_bbox(slices,scale=4):
    for s in slices:
        dy, dx = s[:2]
        yield BBox(dx.start, dy.start, dx.stop+scale, dy.stop+scale)

def remove_overlaps(bboxes,scale=4):
    '''
    Return a set of BBoxes which contain the given BBoxes.
    When two BBoxes overlap, replace both with the minimal BBox that contains both.
    '''
    # list upper left and lower right corners of the Bboxes
    corners = []

    # list upper left corners of the Bboxes
    ulcorners = []

    # dict mapping corners to Bboxes.
    bbox_map = {}

    for bbox in bboxes:
        ul = (bbox.x1, bbox.y1)
        lr = (bbox.x2, bbox.y2)
        bbox_map[ul] = bbox
        bbox_map[lr] = bbox
        ulcorners.append(ul)
        corners.append(ul)
        corners.append(lr)        

    # Use a KDTree so we can find corners that are nearby efficiently.
    tree = spatial.KDTree(corners)
    new_corners = []
    for corner in ulcorners:
        bbox = bbox_map[corner]
        # Find all points which are within a taxicab distance of corner
        indices = tree.query_ball_point(
            corner, bbox_map[corner].taxicab_diagonal(), p = 1)
        for near_corner in tree.data[indices]:
            near_bbox = bbox_map[tuple(near_corner)]
            if bbox != near_bbox and bbox.overlaps(near_bbox):
                # Expand both bboxes.
                # Since we mutate the bbox, all references to this bbox in
                # bbox_map are updated simultaneously.
                bbox.x1 = near_bbox.x1 = min(bbox.x1, near_bbox.x1)
                bbox.y1 = near_bbox.y1 = min(bbox.y1, near_bbox.y1) 
                bbox.x2 = near_bbox.x2 = max(bbox.x2, near_bbox.x2)
                bbox.y2 = near_bbox.y2 = max(bbox.y2, near_bbox.y2) 
    return set(bbox_map.values())
class Box(object):
    """Explanation: This class creates boxes of a certain scale arround certain features (box-counting method)
       scale = the with of the squares
       mask = value of the feature to be 'boxed', for example put boxes arround the coastline, then the non-coastline is
              identified by value mask
    """
    
    def __init__(self,data,scale=4,mask=1):
        #Get the shape of the data
        nY,nX=data.shape
        
        #Now sclice the data array into scale-big slices
        #get the scale of it
        ny,nx=data[::scale].shape
        
        #Create oure desired boxed array
        self.box=np.zeros((nY,nX))
        
        #Cycle through the date array in scale-steps
        for i in xrange(scale,nY-scale,scale):
            for j in xrange(scale,nX-scale,scale):
                if data[i-scale:i+scale,j-scale:j+scale].mean() != mask:    
                    #if the mean-area of the scale-box is not equal to maks
                    #then there this current scale-box is over the coastline
                    self.box[i-scale:i+scale,j-scale:j+scale] = 1
                    #set this box to 1