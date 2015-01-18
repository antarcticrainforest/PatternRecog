'''
Created on Jun 5, 2013

@author: Martin Bergemann
@institution: School of Mathematical Sciences, Monash University

@description: This python module should do the following:
    Return some geometric features out of a data-array
'''
import numpy as np
from scipy.spatial import KDTree
class Geometry(object):
    def __init__(self,data,slm,coastline=1,hour=0,box=5,ratio=25,shape=(12,24),\
            beam=25):
        """
        data = this should be the array where the just the coastline is stored
        coastline = the value that represents the coastline in the data array
        slm = the land-sea mask (distribution)
        box = how many boxes representing the coastal area within slm
        ratio = how many km is on box long
        shape = devide the given data-array into a smaller one with the 
                shape of shape
        beam = the tolerance for the beam alignmet in %
        """
        self.shape=shape
        self.data=data
        self.slm = slm
        self.beam = beam
        #Reshape the data-array (len(ary),[x,y])
        self.hour=hour
        idx = np.where(self.data == coastline)
        self.index= np.array([idx[1],idx[0]]).T
        
        self.ratio = ratio
        self.box = box

        tmp=np.where(slm!=-1)
        self.landtype = np.array([tmp[1],tmp[0]]).T
        del tmp

        #Create a search-tree with leaf-lenght = 10
        self.tree=KDTree(self.index)
        
    def getBox(self,center):
        """Explanation : This function takes the center of a detected feature 
                        and decides to which box-array (smaller array) it 
                        belongs
            center = the center of the given array
        """
        lat=np.arange(self.shape[0])
        lon=np.arange(self.shape[1])
        x,y=center
        dx=self.slm.shape[1]/float(self.shape[1])
        dy=self.slm.shape[0]/float(self.shape[0])
        ix=(np.fabs(lon*dx-x).argmin())
        iy=(np.fabs(lat*dy-y).argmin())
        return ix,iy

    def __find_nearest(P,):
        """Explanation : Help function to get the points in data array that are
        nearest to points that may not be contained in that data-array
        P =the oints of which the corresponding data-points are to be found """
        idx=(np.abs(P[0]-self.data[-1])).argmin()
        idy=(np.abs(P[1]-self.data[0])).argmin()
        return idy,idx
    def getGradient(self,midpoint):
        grad_x,y = np.gradient(self.data)
        x=np.ma.masked_where(grad_x == 0,grad_x)
        angle=np.arctan(y/x).filled(0)
        index=np.where(self.data == 1)
        return index
    
    def shiftObject(self,center):
        
        """Explanation: shifts an objects with a given center
                         to the next coastline
            center : the center of the object
         
        """
        center=np.array(center)
        dist=self.index-center
        
        #Get the point that has the closest distance to the center
        d_tmp=(np.sqrt(dist[:,0]**2+dist[:,1]**2)).argmin()
        d = self.index[d_tmp]
        
        #if center[0] < d[0]: #Center is left of coast
        #    D = d - center
        #else:
        #    D = center - d
        return np.round(d - center,0).astype(np.int32)
    def getLandtype(self,center):
        """Explanation: Check the kind of land-point, center is next to
            center : center of the ellipse
        """
        center=np.array(center)
        dist=self.landtype-center
        #Get the point that has the closest distance to the center
        d_tmp=(np.sqrt(dist[:,0]**2+dist[:,1]**2)).argmin()
        d = tuple(np.roll(self.landtype[d_tmp],1))
        return int(self.slm[d])
    def getTips(self,center,angle,mAxis):
        """Explanation: Check if the tips of a Given Ellipse are over land or
        water
        center : Center of the Ellipse
        angel  : Orientation of the Ellipse
        mAxis  : length of the major Axis
        """
        
        
        center=np.array(center)
        #Construct a Vector from the Center of the Ellipse to the tip of the
        #ellipse (along the major Axis)
        X=mAxis/2*np.array([np.cos(np.pi * (90+angle) / 180),np.sin(np.pi *\
            (90+angle) / 180)])
        #Get the tips of the ellipses in P(y,x) not P(x,y)
        A=tuple(np.roll((center+X).astype(np.int32),1))
        B=tuple(np.roll((center-X).astype(np.int32),1))
        #Check whether the ellipses are over land or water
        #if self.slm[A] != self.slm[B]:
         #   print A,B
            #exit()
            #One tip os over land whereas the other is over water
            #Caostline is somewhere crossed (where is it crossed?)
            
            
        return center+X,center-X
    def getRectAngle(self,points):
        """Explanation : Measure the orientation of a given line
                        and an rectangle
        points = are the points of the rectangle
        """
        p11,p12,p21,p22=points
        P1=self.__find_nearest((p11,p12))
        P2=self.__find_nearest((p21,p22))
        #Calculate the slope between P1 and P2
        M=np.abs(P1[0] - P2[0] / ((P1[1] - P2[1])+0.001))
        #Calculate the slope between the given points
        m=np.abs(p12 - p22 / ((p11 - p21)+0.001))
        #Return the difference between the slope-angles
        return 180/np.pi*np.abs(np.arctan(M) - np.arctan(m))
    def getOrientation(self,center,mAxes):
        """Explanation : Measure the orientation of a given line
                        and an Ellipse
        center = the coordinates of the ellipse-center
        mAxes = the lenght of the Main-Axes
        return = the angle of the Coastline at a certain point
        """
        #Now get the vectors from each point of the data-array to the center
        
        dist = self.index - np.array(center)
        
        #Get the point that has the closet distance to the center
        d_tmp=(np.sqrt(dist[:,0]**2+dist[:,1]**2)).argmin()
        d = self.index[d_tmp]
        
        #Get the pointes that are within a certain radius:
        r=min(mAxes/2,3) #Define the radius
        P=self.tree.query_ball_point(d,r) #Get the indexes from the KD-Tree

        if self.index[P[-1]][0] < d[1]:
            #Last point in the Radius is north of d
            a,b = self.index[P[-1]],d
        else:
            a,b = d,self.index[P[-1]]
        if a[0]-b[0] == 0:
            a,b = self.index[P[0]],self.index[P[-1]]  
        #Now calculate the slope between the first and the last point
        m = (a[1]-b[1])/(a[0]-b[0]+0.0001)
        
        #Return the angle of the slope
        return 180/np.pi * np.arctan(m),a,b
        
        
    def getEAngle(self,center,mAxes,angle):
        """
        Explanation : Construct a Vector from the Center of the
                        Ellipse to its tip and from the Center
                        to the closet point of the coast
        center = center of the Ellipse
        mAxes = the lenght of the Main-Axes
        return = the angle between the computed Vectors
        """
        #Now get the vectors from each point of the data-array to the center
        center=np.array(center)
        dist=self.index-center
        
        #Get the point that has the closet distance to the center
        d_tmp=(np.sqrt(dist[:,0]**2+dist[:,1]**2)).argmin()
        d = self.index[d_tmp]


        #Construct a Vector from the Center of the Ellipse to the tip of the \
        #ellipse (along the major Axis)
        X=mAxes/2*np.array([np.cos(np.pi * (90+angle) / 180),np.sin(np.pi * \
            (90+angle) / 180)])
        #Now construct the Vector from the Center of the Ellipse to the \
        #closed coastal point
        
        if center[0] < d[0]: #Center is left of coast
            D = d - center
        else:
            D = center - d
        if np.linalg.norm(D) < 2:
            return 1000,X,D
        #Now calculate the angle (cos(a) = X*D/|D|*|X|
        
        CosA = np.dot(X,D)/(np.linalg.norm(X)*np.linalg.norm(D))
        
        return 180/np.pi * np.fabs(np.arccos(CosA)),X,D
    def __getMinLength(self,A):
        if self.beam > 1:
            self.beam = (100 - self.beam)/100.
        else:
            self.beam = 1 - self.beam
        A = np.ma.masked_greater(A,self.box**2) + 1e-5
        mul = 1+np.ma.masked_where(np.diagflat(A)!=0,np.diagflat(A))
        X=np.ma.masked_outside(np.outer(A,1./A)*mul,self.beam,1)
        n,m=X.shape
        if  X.mask.all() or len(A) == 0:
            return 1e23
        for i in xrange(n):
            for j in xrange(m):
                if X[i,j] == X.min():
                    a,b = i,j
        return (A[a] + A[b])/2
    def evaluateLength(self,A,B):
        self.slm.shape
        maximum=np.linalg.norm(np.array(self.slm.shape))
        a,b= self.__getMinLength(A),self.__getMinLength(B)
        if a > maximum and b > maximum:
            if np.sort(A).mean() < np.sort(B).mean():
                tmp = 'a'
                l = a
            else:
                tmp = 'b'
                l = b
        else:
            if a < b:
                tmp = 'a'
                l = a
            else:
                tmp = 'b'
                l = b
        if l <= self.box**2:
            return True,tmp
        else:
            return False,tmp

        
    def getLength(self,center,angle,mAxis,idx):
        """Explanation: get the distance of three points to the coastline
            and calculate the standard deviation
            points: the points for the calculation (tipA,tipB,center)
        """
        tips=self.getTips(center, angle, mAxis)
        self.idx = idx
        center=np.array(center)
        
        #Construct a vector that points to the coast for the
        #given point (in 90 deg)
        vec = np.array([center-tips[0],tips[0]-center,center-tips[1]])
        points = np.array([tips[0],center,tips[1]])
        #Coast is right of the center --> rotate -90 deg
        d=np.array([0,0,0])
        rot = np.pi * 90 / 180
        D = np.array([[np.cos(rot),-np.sin(rot)],[np.sin(rot),np.cos(rot)]])
        length=np.array([0,0,0])
        A = []
        B = []
        for i in xrange(3):
            vx,vy = np.dot(D,vec[i])
            if points[i][0] >= 0 and points[i][1] >= 0 and points[i][1] \
            <= self.slm.shape[0]-1 and points[i][0] <= self.slm.shape[1]-1:
                s = self.__intersect((vx,vy),points[i])
                try:
                    A.append(self.__getbeam(angle-90,s[0],points[i]))
                    B.append(self.__getbeam(angle-90,s[1],points[i]))
                except KeyError:
                    return None,None
    
        return A,B
    def __getbeam(self,angle,intersect,point):
        x,y=intersect
        if angle % 90 != 0:
            length = int(np.hypot(np.fabs(x-point[0]), np.fabs(y-point[1])))
            X, Y = np.linspace(x, point[0], length), np.linspace(y, point[1],\
                    length)
        else:
            if angle % 180 == 0:
                #Intersection with upper or lower x-Axis
                length=int(np.fabs(y-point[1]))
                X,Y = x*np.ones(length),np.linspace(y,point[1],length)
            else:
                #Intersection with right or left y-Axis
                length=int(np.fabs(x-point[0]))
                X,Y = np.linspace(x,point[0],length),y*np.ones(length)
        
        zi = np.zeros(self.slm.shape)
        
        try:
            zi[(Y.astype(np.int32),X.astype(np.int32))] \
                    = self.data[(Y.astype(np.int32),X.astype(np.int32))]
        except IndexError:
            return None,None
        
        index = np.where(zi == 1)
        if len(index[0]) != 0:
            index = np.array([index[1],index[0]]).T
            dist=index-point
    
            #Get the point that has the closet distance to the center
            a = np.sqrt(dist[:,0]**2+dist[:,1]**2).argmin()
            A = (point,index[a])
        else:
            A = (point.astype(np.int32),np.array([x,y]))

        return A


    def __intersect(self,vec,point):
        """Explanation: Get the intersection of four given Axis
                        with a straight line
            vec : vector of the straight line
            point : point of the straight line
        """

        #Define the axis for the intersections
        x0,y0 = 0,0
        y1,x1 = self.slm.shape[0]-1,self.slm.shape[1]-1
        vx,vy = vec
        px,py = point
        #Get the intersection with the Axis y=0 (i0y,0)
        i0y = (px + (y0 - py)*vx/(vy+1e-25),y0)
        #Get the intersection with the Axis x=0 (0,i0x)
        i0x = (x0,py + (x0 - px)*vy/(vx+1e-25))
        #Get the intersection with the Axis y=y1 (i1y,y1)
        i1y = (px + (y1 - py)*vx/(vy+1e-25),y1)
        #Get the intersection with the Axis x=0 (x1,i1x)
        i1x = (x1,py + (x1 - px)*vy/(vx+1e-25))
        #Get the intersection with the Axis x=axis[0] (axis[0],b)
        intersect = {}
        for s in [i0y,i0x,i1y,i1x]:
            sx,sy = s
            if sx >= 0 and sy >= 0:
                try:
                    tmp=self.slm[sy,sx]
                    if round(sx,2) == round(px,2):
                        if sy > py:
                            intersect[1] = (int(sx),int(sy))
                        else:
                            intersect[0] = (int(sx),int(sy))
                    elif sx < px:
                        intersect[1] = (int(sx),int(sy))
                    else:
                        intersect[0] = (int(sx),int(sy))
                except IndexError:
                    pass
        return intersect
