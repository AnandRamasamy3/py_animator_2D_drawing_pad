from math import *

class point2D:
    def __init__(self,x,y,z=0):
        self.x=x
        self.y=y
        self.z=z
    def print(self):
        print (self.x,self.y)
    def list_point(self):
        return [self.x,self.y]

class bezier:
    def __init__(self,x=0,y=0):
        pass
    def midpoint(self,p1,p2,T,t):
        result=point2D(0,0)
        result.x=p1.x+((p2.x-p1.x)/T)*t
        result.y=p1.y+((p2.y-p1.y)/T)*t
        return result
    def make_(self,points,T,t):
        if len(points)==2:
            return self.midpoint(points[0],points[1],T,t)
        new_points=[]
        for point_index in range(len(points)-1):
            mid_=self.midpoint(points[point_index],points[point_index+1],T,t)
            new_points.append(mid_)
        return self.make_(new_points,T,t)
    def find_curve(self,points,T=10):
        # points.append(points[0])
        curve=[points[0]]
        t=1
        while t<T:
            new_points=self.make_(points,T,t)
            curve.append(new_points)
            t+=1
        return curve[:]
    def make_shape(self,points,T=100,radius=None,radius_percentage=10):
        result=[]
        scale=basics()
        if radius==None:
            min_length=999999
            for point_index in range(len(points)-1):
                point_1=points[point_index]
                point_2=points[point_index+1]
                dist=scale.euclidean_distance(point_1,point_2)
                if dist<min_length:
                    min_length=dist
            point_1=points[-1]
            point_2=points[0]
            # print ()
            dist=scale.euclidean_distance(point_1,point_2)
            if dist<min_length:
                min_length=dist
            radius=int(min_length//radius_percentage)
        # print (radius)
        for point_index in range(1,len(points)-1):
            point_1=points[point_index-1]
            point_2=points[point_index]
            point_3=points[point_index+1]
            line_1=scale.DDA_points(point_1,point_2)
            line_2=scale.DDA_points(point_2,point_3)
            # radius=(min(len(line_1),len(line_2)))//10
            # print (len(line_1),len(line_2),radius)
            first_end_point=line_1[-radius]
            result+=line_1[radius:-radius][:]
            second_start_point=line_2[radius]
            # print (first_end_point.x,first_end_point.y)
            # print (point_2.x,point_2.y)
            # print (second_start_point.x,second_start_point.y)
            # print ()
            current_input_points=[first_end_point,point_2,second_start_point]
            curve_pixels=self.find_curve(current_input_points,T=T)
            result+=curve_pixels[:]
            # for point in curve_pixels:
            #     result.append(point)
            # result+=line_2[radius:-radius][:]
        point_index=len(points)
        point_1=points[point_index-2]
        point_2=points[point_index-1]
        point_3=points[0]
        scale=basics()
        line_1=scale.DDA_points(point_1,point_2)
        line_2=scale.DDA_points(point_2,point_3)
        first_end_point=line_1[-radius]
        result+=line_1[radius:-radius][:]
        second_start_point=line_2[radius]
        current_input_points=[first_end_point,point_2,second_start_point]
        curve_pixels=self.find_curve(current_input_points,T=T)
        result+=curve_pixels[:]
        #
        point_1=points[len(points)-1]
        point_2=points[0]
        point_3=points[1]
        scale=basics()
        line_1=scale.DDA_points(point_1,point_2)
        line_2=scale.DDA_points(point_2,point_3)
        first_end_point=line_1[-radius]
        result+=line_1[radius:-radius][:]
        second_start_point=line_2[radius]
        current_input_points=[first_end_point,point_2,second_start_point]
        curve_pixels=self.find_curve(current_input_points,T=T)
        result+=curve_pixels[:]
        return result[:]


class basics:
    def __init__(self):
        pass
    def circle(self,point,radius,angle):
        x=int(point.x+radius*cos(angle))
        y=int(point.y+radius*sin(angle))
        return point2D(x,y)
    def angle(self,point_1,point_2,point_3):
        ang = degrees(
            atan2(point_3.y-point_2.y,point_3.x-point_2.x)-atan2(point_1.y-point_2.y,point_1.x-point_2.x))
        return ang + 360 if ang < 0 else ang
    def euclidean_distance(self,point_1,point_2):
        point=sqrt( ((point_1.x-point_2.x)**2)+((point_1.y-point_2.y)**2) )
        return point
    def DDA_points(self,point_1,point_2):
        points=[]
        x1,y1,x2,y2=point_1.x,point_1.y,point_2.x,point_2.y
        x,y = x1,y1
        length=max(abs(x2-x1),abs(y2-y1))
        if length==0:length=-1
        dx=(x2-x1)/float(length)
        dy=(y2-y1)/float(length)
        points.append(point2D(int(x+0.5),int(y+0.5)))
        # print (length)
        i=0
        while i<length:
            x+=dx
            y+=dy
            points.append(point2D(int(x+0.5),int(y+0.5)))
            i+=1
        return points
