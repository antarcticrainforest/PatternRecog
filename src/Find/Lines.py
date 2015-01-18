'''
Created on May 22, 2013

@author: Martin Bergemann
@institution: School of Mathematical Sciences, Monash University
@purpose: Detect Lines in an given Data-Array
'''

import numpy as np
from netCDF4 import Dataset as nc

#from Plot import *
from netCDF4 import num2date,date2num,date2index

import datetime,cv2,time
from scipy import ndimage
from src.detect import coastline
from src.Find.Geometry import *
import os
from scipy.ndimage import gaussian_filter as bl


def etime():
    #See how much user and system time this process has used
    #so far and return the sum
    user,sys,chuser,chsys,real=os.times()
    return user+sys

class Info(object):
    def __init__(self,shape=(12,24)):
        """
        Explanation: This Class just creates some array's where some additional
        information about the contours (number of contours in each box
        quantity of rainfall in each-box and the distance from the coast)
        is sotred:
        shape = is the shape the array should have where the info is stored
        """
        #The number of the detected contours in each box
        self.cnt=np.zeros(shape,dtype=np.float32)
        #The quantity of rainfall in each box
        self.quant=np.zeros(shape,dtype=np.float32)
        #The distance from the coastline from each box
        self.dist=np.zeros(shape,dtype=np.float32)
        #The area of each contour in the box
        self.area=np.zeros(shape,dtype=np.float32)
        #The toatl


class Lines(object):
    def __init__(self,array,thresh,coast,g,resol=0.25,blur=(3,3),noise=2,\
            mask=None):
        """
        array = the data-array
        thresh = the threshold for at which a mask should be applied
        coast = the box-counting coastline
        resol = the horizontal resolution of the grid in deg
        blur  = tuple that determines the blurring factor for the image
        mask  = the coastline
        g = the geometry objects with all geometry functions
        """
        #Instanciate all variables
        self.thresh=thresh
        self.g = g
        self.ma_array=np.ma.masked_where(array<=thresh,array)
        self.array=array
        self.noise=noise
        self.coast=coast
        self.blur=blur
        self.mask = mask
        
        self.resol=resol
        #Create a black and white image from precip data
        tmp=self.ma_array.filled(0)
        tmp[np.where(tmp!=0)]=255
        bw=tmp.astype(np.uint8)
        
        #Now detect the edges of the black-and-white image
        #But first close small holes with erosion and dilation
        #For this purpose we need a kernel (this case a cross)
        self.element = cv2.getStructuringElement(cv2.MORPH_CROSS,\
                (blur[0]-1,blur[1]-1))
        #erosion and dilation
        closed=cv2.morphologyEx(bw,cv2.MORPH_CLOSE,(blur[0]+5,blur[1]+5))
        for c in xrange(3):
            closed=cv2.morphologyEx(closed,cv2.MORPH_CLOSE,(blur[0]+5,blur[1]+5))

        #blur the closed-hole image
        closed = bl(bw,0.35)
        
        #Now get the contours with canny-edge detection
        self.contours, self.hierarchy = \
                cv2.findContours(closed,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
       #Now just get the number of coastal features
        self.tcnt, h  =\
        cv2.findContours((closed*self.coast[0]).astype(np.uint8),\
                cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        self.tcnt=len(self.tcnt)
        tmp=np.roll(tmp,-4,axis=0)
        self.img=cv2.cvtColor((0*np.ma.masked_less_equal(bw,\
                thresh)).filled(255).astype(np.uint8),cv2.COLOR_GRAY2BGR)
        #self.img=255+self.img*0
        del bw,closed
    
    def getEllipse(self,info,coast=True,area=500,ecce=0.95,maxAngle=10):
        """
        Explanation: This Lines function fits objects to a rot. ellipse
                    and determinds whether the objects thin or not
        info = info-object
        coast = Shall we only consider objects cloasted the to coast?
        area = thershold in px for synoptic scale precip
        ecce = threshold for the eccentricity to determind thin_objs
        maxAngle = straight line standard deviation obj's
        Returns:
            (nd-array) the array with detected objects
        """
        thin_objects=[]
        #What area could be defined as synoptic scale ~ 1000 km^2
        maximum=area*self.resol**2 # This is the synoptic threshold in deg^2 
        #(above these value we treat precip as synoptic)
        #Create a geometry object where for the indexes where the mask array 
        #is equal 1 
        tmpary=np.zeros(self.coast[0].shape)
        for index,cnt in enumerate(self.contours):
            #Calculate the area covert by the contour in deg**2
            Area=self.resol**2*cv2.contourArea(cnt)
            if self.hierarchy[0][index][-1] == -1:
                if Area > 0. and Area < maximum:
                    if len(cnt) < 5:
                        cv2.drawContours(tmpary,[cnt],-1,1,-1)
                        labeled,num=ndimage.label(tmpary)
                        labeled=np.ma.masked_where(labeled!=0,labeled).filled(1)
                        tmpary=tmpary*0
                        if self.coast[1][np.where(labeled==1)].mean() >= 0.75:
                            M=cv2.moments(cnt)
                            x = M['m10']/M['m00']
                            y = M['m01']/M['m00']
                            thin_objects.append(cnt)
                            self.getInfo(labeled,(x,y),Area,info)
                    else:
                        #Fit an Minimal-Ellipse the the contour
                        ellipse=cv2.fitEllipse(cnt)
                        epsCenter,epsAxes,epsOrientation = ellipse
                        #Calculate major and minor-Axes Length
                        majoraxis_length = max(epsAxes)
                        minoraxis_length = min(epsAxes)
                        #Calculate the eccentricity of the ellipse
                        eccentricity = \
                                np.sqrt(1-(minoraxis_length/majoraxis_length)**2)
                        if eccentricity > ecce:
                            #If we do not want to detect coastal \
                            #obj's we do not need #to calculate the \
                            #angle of the coast of and obj but if so: do it
                            
                            cv2.drawContours(tmpary,[cnt],-1,1,-1)
                            
                            labeled, num = ndimage.label(tmpary)
                            labeled=np.ma.masked_where\
                                    (labeled!=0,labeled).filled(1)
                            tmpary=tmpary*0
                            
                            if self.coast[1][np.where(labeled ==1)].mean()\
                                    >= 0.75  and Area > 4:
                                tips=self.g.getTips(epsCenter,epsOrientation\
                                        ,majoraxis_length)
                                thin_objects.append(cnt)
                                #Save some info about the contour
                                cv2.drawContours(self.img,[cnt],-1,(0,0,255),-1)
                                self.getInfo(labeled,epsCenter,Area,info)
                                
                            elif self.coast[0][np.where(labeled==1)].mean()\
                                    >= 0.5:

                                D = self.g.shiftObject(epsCenter)
                                tmp = np.roll(np.roll(labeled,D[1],axis=0),\
                                        D[0],axis=1)

                                if self.coast[-1][np.where(tmp ==1)].mean()\
                                        >= 0.75 and Area > 9:

                                    thin_objects.append(cnt)
                                    cv2.drawContours(self.img,[cnt],-1,(0,0,255),-1)
                                    #Save some info about the contour
                                    self.getInfo(labeled,epsCenter,Area,info)
                                else:
                                    try:
                                        tipsA,tipsB=self.g.getLength(epsCenter,\
                                                epsOrientation,\
                                                majoraxis_length,index)
                                    except TypeError:
                                        pass
                                    try:
                                        if tipsA and tipsB:
                                            A=[]
                                            B=[]
                                            for i in xrange(len(tipsA)):
                                                A.append(np.linalg.norm(tipsA\
                                                        [i][0]-tipsA[i][1]))

                                                B.append(np.linalg.norm(tipsB\
                                                        [i][0]-tipsB[i][1]))

                                            allign,point=self.g.evaluateLength(\
                                                    np.array(A),np.array(B))
                                            if point == 'a':
                                                a=tuple(tipsA[i][0].astype(np.int32))
                                                b=tuple(tipsA[i][1].astype(np.int32))
                                            else:
                                                a=tuple(tipsB[i][0].astype(np.int32))
                                                b=tuple(tipsB[i][1].astype(np.int32))

                                            if allign:
                                                thin_objects.append(cnt)
                                                #Save some info about the contour
                                                self.getInfo(labeled,epsCenter,\
                                                        Area,info)
                                            else:
                                                pass


                                    except UnboundLocalError:
                                        pass
        #thin_ojects is a list
        #make an array out of it an return it
        ary = np.zeros(self.coast[0].shape)
        cv2.drawContours(ary,thin_objects,-1,1,-1)
        #Last step rerasing the pseudo thin objects
        #And return the retrun-value
        del thin_objects
        return ary
    def getRect(self,mask,coast=True,asp=0.7,maxAngle=10):
        """
        Explanation: This Lines function fits objects to a rot. rectangle
                    and determinds whether the objects thin or not
        mask = thin coastline to determine the orientation of the
               detected objects relative to the coastline (mask)
        coast = Shall we only consider objects cloasted the to coast?
        area = threshold in px for synoptic scale precip
        asp = threshold for the aspect_ratio to determine thin objs
        maxAngle = the maximum angel between the coastline and the obj's
        """
        thin_objects=[]
        #What area could be defined as synoptic scale ~ 1000 km^2
        maximum=area*self.resol**2 # This is the synoptic threshold 
                    #in deg^2 (above these value we treat precip as synoptic)
        #Create a geometry object where for the 
                    #indexes where the mask array is equal 1
        g=Geometry(np.where(mask==1))
        for cnt in self.contours:
            Area=self.resol**2 * cv2.contourArea(cnt)
            if Area > 0. and Area < maximum:
                rect = cv2.minAreaRect(cnt)
                x1,x2,x3,x4 = cv2.cv.BoxPoints(rect)
                dx,dy = x1-x2, x2-x3
                l,w=np.sqrt(dx[0]**2+dx[1]**2),np.sqrt(dy[0]**2+dy[1]**2)
                h,b=max(l,w)+0.0001,min(l,w)
                aspect_ratio=b/float(h)
                if aspect_ratio < asp:
                    X1=x1
                    if l > w:
                        X2=x2
                    else:
                        X2=x3
                    if coast:
                    #If we do not want to detect coastal obj's we do not need 
                    #to calculate the angle of the coast of and obj
                    #but if so: do it
                        angle=g.getAngle((X1[0],X1[1],X2[0],X2[1]))
                        if angle < 10:
                            thin_objects.append(cnt)
                    else:
                        thin_objects.append(cnt)
        
        #thin_ojects is a list
        #make an array out of it an return it
        ary = (np.zeros(self.coast.shape))
        cv2.drawContours(ary,thin_objects,-1,1,-1)
        #Last step rerasing the pseudo thin objects
        #And return the retrun-value
        self.contours=thin_objects
        return self.eraseBiggerItems(ary)
    def getInfo(self,cnt,center,area,info):
        """
        Explanation: This Lines function calculates some additionale info
                    for each detected contour (num on contour, where is the 
                    contour, how-much precip is falling in that contour)
        cnt = the contour 
        center = the center of the contour
        """

        #The contour should be mapped, let's get the index of this map
        ix,iy = self.g.getBox(center)
        #Now we know where the information can be stored
        #but we want to know what info should be stored
        
        #1) the number of the contours in that box, should be easy
        try:
            info.cnt[iy,ix] += 1
        except IndexError:
            print center,ix,iy,self.g.slm.shape,self.g.hour
            exit()
        
        #2) the area of the contour, should also be easy
        info.area[iy,ix] += area

        #3) the precipitation out of that contour, little bit more complex
        info.quant[iy,ix] += self.ma_array[np.where(cnt == 1)].mean()

        #4) the distance of that feature to the coast, most complex here
        dist = self.g.index-np.array(center)
        info.dist[iy,ix] += (np.sqrt(dist[:,0]**2+dist[:,1]**2)).min()
    def eraseBiggerItems(self,thin_objects):
        """
        Explanation: This Lines function takes small detected areas
                    and checks if these are pseudo-isolated.
                    Pseudo-isolated means objects are aritficially
                    isolated, due to the application of a threshold.
        thin_objects = the detected regions
        """
        
        #Prepare the data-array (mask values belwo 0.05 mm/3h)
        
        mask=np.ma.masked_where(self.array<=0.05,self.array)
        
        ztmp = np.zeros(mask.data.shape) #Just for temperory use

        #Not all found contours are contours of interest
        #the indexes of the contours of interest will be stored hit
        hit=[]
        
        #Cycle through the found contours (contours i a Lines object instance)
        for n,cnt in enumerate(self.contours):
            #Get the area of the contour once more
            
            area = cv2.contourArea(cnt)
            
            #Fit the contour to a rotated ellipse
            Center,Axes,Orientation = cv2.fitEllipse(cnt)
            Axes=tuple(0+np.array(Axes))

            cv2.ellipse(ztmp,(Center,Axes,Orientation),1,-1)
            #cv2.ellipse(self.img,(Center,Axes,Orientation),(255,0,0),-1)
            
            #tmpindex=np.where(ztmp!=1)
            #tmp-array is now need for different purpose (copy mask to tmp) 
            #np.copyto(ztmp,mask.mask.astype(np.int0),casting='unsafe')
            ztmp = ztmp *  mask.mask.astype(np.int0)
            #ztmp[tmpindex] = 0 #Set every value outside of the box to 0
            
            #print np.where(ztmp==1)
            #exit()
            #Again find contours in that box 
            #(this time the data-array without erosion-dilation is used)
            tmpCnt = cv2.findContours(ztmp.astype(np.uint8),\
                    cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[0]
            if len(tmpCnt): #If any new contours are found
            #Finally all criteria are met that the found 
            #contour is indeed a thin-contour
                hit.append(n)
            
            ztmp = ztmp * 0 #Blank the tmp array for new use

        #Create an array were the found contours will be drawn to
        ary = np.zeros(mask.data.shape)
        if len(hit):
            #If anything was found we can draw it to ary
            cv2.drawContours(ary,np.array(self.contours)[hit],-1,1,-1)

        return ary
    def __getCoastalObj(self,objects):
        #Create an array where the detected contours are stored
        ary=(np.zeros(self.coast.shape))
        cv2.drawContours(ary,objects,-1,1,-1)
        #Count the contours and label them
        labeled, num = ndimage.label(ary)
        for i in xrange(1,num+1):
            index=np.where(labeled==i)
            if self.coast[index].mean() < 0.8 :
                ary[index] = 0
        return ary
