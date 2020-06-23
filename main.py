import pygame,sys,time,math,threading,os,random
from pygame.locals import *
import sqlite3
import json
import datetime
import warnings

from src.fundamentals import *

pygame.init()
WIDTH,HEIGHT=1220,670
surface=pygame.display.set_mode((WIDTH,HEIGHT),0,32)
fps=100
ft=pygame.time.Clock()
pygame.display.set_caption('Animator Drawing Pad')

class app:
    def __init__(self,surface):
        self.surface=surface
        mouse=pygame.mouse.get_pos()
        self.mouse=point2D(mouse[0],mouse[1])
        click=pygame.mouse.get_pressed()
        self.click=point2D(click[0],click[1],click[2])
        self.database={}
        self.colors={}
        self.mode_setters={}
        self.tools={}
        self.navigators={}
        self.get_database()
        self.set_custom_database()
        self.point_index=0
        self.grabbed=None
        self.scale=basics()
        self.bezier=bezier()
        self.last_clicked=time.time()
        self.control_visible=True
        self.joints_pool=[]
        self.edges_pool=[]
        self.bones=[]
        self.joint_radius=5
        self.edge_radius=3
        self.mode="adjusting"
        self.new_node={
            "points":[],
            "last_clicked":time.time()
        }
        self.neighbors_distance=30
        self.making_bubble_ball_last_clicked=time.time()
        self.sync_target=None
        self.garbage=[]
        self.support_garbage=[]
        self.delete_hidden_manager_size=30
        self.delete_show_hidden=False
        self.delete_show_hidden_last_clicked=time.time()
        self.tools_hidden_manager_size=30
        self.tools_show_hidden=False
        self.tools_show_hidden_last_clicked=time.time()
        self.current_alphabet=None
    def set_custom_database(self):
        self.database={}
    def get_database(self):
        fobj=open("src/database.json",)
        data=json.load(fobj)
        self.color=data["general_colors"]
        self.mode_setters=data["mode_setters"]
        self.tools=data["tools"]
        self.navigators=data["navigators"]
        fobj.close()
    def save_backup(self):
        joints_pool=[]
        for point in self.joints_pool:
            joints_pool.append(point.list_point())
        edges_pool=[]
        for point in self.edges_pool:
            edges_pool.append(point.list_point())
        backup={
            "joints_pool":joints_pool,
            "edges_pool":edges_pool,
            "bones":self.bones
        }
        not_exists=True
        file_names=os.listdir("src/backups/")
        latest_file_name=max([int(file_name.split(".")[0]) for file_name in file_names]) if len(file_names)>0 else None
        if latest_file_name==None:
            fobj=open("src/backups/"+str(int(time.time()))+".json","w")
            json.dump(backup,fobj)
            fobj.close()
        else:
            fobj=open("src/backups/"+str(latest_file_name)+".json",)
            latest_data=json.load(fobj)
            fobj.close()
            if latest_data!=backup:
                fobj=open("src/backups/"+str(int(time.time()))+".json","w")
                json.dump(backup,fobj)
                fobj.close()
    def get_neighborhoods(self,point):
        neighbors=[]
        neighbors.append(point2D(point.x-self.neighbors_distance,point.y-self.neighbors_distance))
        neighbors.append(point2D(point.x+self.neighbors_distance,point.y-self.neighbors_distance))
        neighbors.append(point2D(point.x+self.neighbors_distance,point.y+self.neighbors_distance))
        neighbors.append(point2D(point.x-self.neighbors_distance,point.y+self.neighbors_distance))
        return neighbors
    def adjusting(self):
        if self.grabbed!=None:
            if self.grabbed["type"]=="joint_adjusting":
                if self.click.x==1:
                    pass
                    # bone adjusting
                    bone_index=self.grabbed["bone_index"]
                    joint_position=self.grabbed["joint_position"]
                    joints_pool_index=self.bones[bone_index][joint_position]["point"]
                    diff_x=self.mouse.x-self.joints_pool[joints_pool_index].x
                    diff_y=self.mouse.y-self.joints_pool[joints_pool_index].y
                    self.joints_pool[joints_pool_index].x=self.mouse.x
                    self.joints_pool[joints_pool_index].y=self.mouse.y
                    # related bubble ball adjusting
                    for edges_pool_index in self.bones[bone_index][joint_position]["bubble_ball"]:
                        # print ("before",self.edges_pool[edges_pool_index].list_point())
                        self.edges_pool[edges_pool_index].x+=diff_x
                        self.edges_pool[edges_pool_index].y+=diff_y
                        # print ("after",self.edges_pool[edges_pool_index].list_point())
                        # print (diff_x,diff_y)
                        if [diff_x,diff_y] not in self.garbage:
                            self.garbage.append([diff_x,diff_y])
                            self.support_garbage.append(1)
                        else:
                            self.support_garbage[self.garbage.index([diff_x,diff_y])]+=1
                else:
                    # print ("resetted")
                    self.grabbed=None
            elif self.grabbed["type"]=="bubble_ball_adjusting":
                if self.click.x==1:
                    pass
                    # bubble_ball adjusting
                    bubble_ball_index=self.grabbed["bubble_ball_index_of_edges_pool"]
                    self.edges_pool[bubble_ball_index].x=self.mouse.x
                    self.edges_pool[bubble_ball_index].y=self.mouse.y
                else:
                    # print ("resetted")
                    self.grabbed=None
            elif self.grabbed["type"]=="new_bubble_ball_point":
                if self.click.x==1:
                    pass
                    bone_index=self.grabbed["bone_index"]
                    joint_position=self.grabbed["joint_position"]
                    index_to_be_inserted=self.grabbed["index_to_be_inserted"]
                    point_to_be_inserted=self.grabbed["point_to_be_inserted"]
                    self.edges_pool.append(point_to_be_inserted)
                    # print (point_to_be_inserted.list_point())
                    self.bones[bone_index][joint_position]["bubble_ball"].insert(index_to_be_inserted,self.edges_pool.index(point_to_be_inserted))
                    self.grabbed=None
                else:
                    # print ("resetted")
                    self.grabbed=None
    def draw_bones(self):
        pass
        for bone in self.bones:
            # print (bone)
            # --------- first joint
            # if self.control_visible:
            #     pygame.draw.circle(self.surface,self.color["transparent_black"],self.joints_pool[bone["joint_front"]["point"]].list_point(),self.joint_radius)
            # print (self.mode)
            if self.mode in ["adjusting","sync_bones","delete_bones"]:
                if self.grabbed==None:
                    if self.click.x==1:
                        distance=self.scale.euclidean_distance(self.mouse,self.joints_pool[bone["joint_front"]["point"]])
                        if self.mode=="adjusting":
                            type="joint_adjusting"
                        else:
                            type=self.mode
                        if distance<=self.joint_radius:
                            self.grabbed={
                                "type":type,
                                "bone_index":self.bones.index(bone),
                                "joint_position":"joint_front"
                            }
            # --------- second joint
            # if self.control_visible:
            #     pygame.draw.circle(self.surface,self.color["transparent_black"],self.joints_pool[bone["joint_rear"]["point"]].list_point(),self.joint_radius)
            if self.mode in ["adjusting","sync_bones","delete_bones"]:
                if self.grabbed==None:
                    if self.click.x==1:
                        distance=self.scale.euclidean_distance(self.mouse,self.joints_pool[bone["joint_rear"]["point"]])
                        if self.mode=="adjusting":
                            type="joint_adjusting"
                        else:
                            type=self.mode
                        if distance<=self.joint_radius:
                            self.grabbed={
                                "type":type,
                                "bone_index":self.bones.index(bone),
                                "joint_position":"joint_rear"
                            }
            # --------- bone
            # if self.control_visible:
            #     pygame.draw.line(self.surface,self.color["transparent_black"],self.joints_pool[bone["joint_front"]["point"]].list_point(),self.joints_pool[bone["joint_rear"]["point"]].list_point(),3)
            # --------- first joint bubble ball
            bubble_ball_points=[]
            bubble_ball_points_for_bezier=[]
            for point_index in bone["joint_front"]["bubble_ball"]:
                if self.mode in ["adjusting","sync_bubble_ball_points","delete_bubble_ball","delete_bubble_ball_edge"]:
                    if self.grabbed==None:
                        if self.click.x==1:
                            distance=self.scale.euclidean_distance(self.mouse,self.edges_pool[point_index])
                            if self.tools_show_hidden:
                                self.grabbed={
                                    "type":"applying_tools_properties",
                                    "bone_index":self.bones.index(bone),
                                    "joint_position":"joint_front",
                                    "bubble_ball_index":bone["joint_front"]["bubble_ball"].index(point_index),
                                    "bubble_ball_index_of_edges_pool":point_index
                                }
                                # self.grabbed=None
                            else:
                                if self.mode=="adjusting":
                                    type="bubble_ball_adjusting"
                                else:
                                    type=self.mode
                                if distance<=self.joint_radius:
                                    # print ("got placed")
                                    self.grabbed={
                                    "type":type,
                                    "bone_index":self.bones.index(bone),
                                    "joint_position":"joint_front",
                                    "bubble_ball_index":bone["joint_front"]["bubble_ball"].index(point_index),
                                    "bubble_ball_index_of_edges_pool":point_index
                                    }
                point=self.edges_pool[point_index].list_point()
                if self.control_visible:
                    pygame.draw.circle(self.surface,self.color["transparent_black"],point,self.edge_radius)
                bubble_ball_points.append(point)
                bubble_ball_points_for_bezier.append(self.edges_pool[point_index])
            if len(bubble_ball_points)>2:
                result=self.bezier.make_shape(bubble_ball_points_for_bezier,T=100,radius=None,radius_percentage=5)
                bezier_curve_result=[point.list_point() for point in result]
                fill=bone["joint_front"]["fill"]
                fill_color=bone["joint_front"]["fill_color"]
                border_size=bone["joint_front"]["border_size"]
                border_color=bone["joint_front"]["border_color"]
                if fill:
                    pygame.draw.polygon(self.surface,fill_color,bezier_curve_result)
                pygame.draw.polygon(self.surface,border_color,bezier_curve_result,border_size)
                # pygame.draw.polygon(self.surface,self.color["transparent_black_for_sync"],bezier_curve_result)
                # pygame.draw.polygon(self.surface,self.color["transparent_black"],bubble_ball_points,1)
            # --------- second joint bubble ball
            bubble_ball_points=[]
            bubble_ball_points_for_bezier=[]
            for point_index in bone["joint_rear"]["bubble_ball"]:
                if self.mode in ["adjusting","sync_bubble_ball_points","delete_bubble_ball","delete_bubble_ball_edge"]:
                    if self.grabbed==None:
                        if self.click.x==1:
                            distance=self.scale.euclidean_distance(self.mouse,self.edges_pool[point_index])
                            if self.tools_show_hidden:
                                self.grabbed={
                                    "type":"applying_tools_properties",
                                    "bone_index":self.bones.index(bone),
                                    "joint_position":"joint_rear",
                                    "bubble_ball_index":bone["joint_rear"]["bubble_ball"].index(point_index),
                                    "bubble_ball_index_of_edges_pool":point_index
                                }
                                # self.grabbed=None
                            else:
                                if self.mode=="adjusting":
                                    type="bubble_ball_adjusting"
                                else:
                                    type=self.mode
                                if distance<=self.joint_radius:
                                    self.grabbed={
                                    "type":type,
                                    "bone_index":self.bones.index(bone),
                                    "joint_position":"joint_rear",
                                    "bubble_ball_index":bone["joint_rear"]["bubble_ball"].index(point_index),
                                    "bubble_ball_index_of_edges_pool":point_index
                                    }
                point=self.edges_pool[point_index].list_point()
                if self.control_visible:
                    pygame.draw.circle(self.surface,self.color["transparent_black"],point,self.edge_radius)
                bubble_ball_points.append(point)
                bubble_ball_points_for_bezier.append(self.edges_pool[point_index])
            if len(bubble_ball_points)>2:
                result=self.bezier.make_shape(bubble_ball_points_for_bezier,T=100,radius=None,radius_percentage=5)
                bezier_curve_result=[point.list_point() for point in result]
                # print (bone["joint_rear"]["fill"])
                fill=bone["joint_rear"]["fill"]
                fill_color=bone["joint_rear"]["fill_color"]
                border_size=bone["joint_rear"]["border_size"]
                border_color=bone["joint_rear"]["border_color"]
                if fill:
                    pygame.draw.polygon(self.surface,fill_color,bezier_curve_result)
                pygame.draw.polygon(self.surface,border_color,bezier_curve_result,border_size)
                # pygame.draw.polygon(self.surface,self.color["transparent_black"],bubble_ball_points,1)
            # --------- first joint bubble ball intersecting points
            if self.click.x==1:
                if self.grabbed==None:
                    if self.mode=="adjusting":
                        for bone in self.bones:
                            for point_index in range(len(bone["joint_front"]["bubble_ball"])-1):
                                current_point=self.edges_pool[bone["joint_front"]["bubble_ball"][point_index]]
                                cursor_point=self.mouse
                                next_point=self.edges_pool[bone["joint_front"]["bubble_ball"][point_index+1]]
                                angle=self.scale.angle(current_point,cursor_point,next_point)
                                if 179<=angle<=181:
                                    self.grabbed={
                                        "type":"new_bubble_ball_point",
                                        "bone_index":self.bones.index(bone),
                                        "joint_position":"joint_front",
                                        "index_to_be_inserted":point_index+1,
                                        "point_to_be_inserted":cursor_point
                                    }
                                    break
                            if len(bone["joint_front"]["bubble_ball"])>2:
                                current_point=self.edges_pool[bone["joint_front"]["bubble_ball"][-1]]
                                cursor_point=self.mouse
                                next_point=self.edges_pool[bone["joint_front"]["bubble_ball"][0]]
                                angle=self.scale.angle(current_point,cursor_point,next_point)
                                if 179<=angle<=181:
                                    self.grabbed={
                                        "type":"new_bubble_ball_point",
                                        "bone_index":self.bones.index(bone),
                                        "joint_position":"joint_front",
                                        "index_to_be_inserted":len(bone["joint_rear"]["bubble_ball"]),
                                        "point_to_be_inserted":cursor_point
                                    }
                            if self.grabbed!=None:
                                break
            # --------- second joint bubble ball intersecting points
            if self.click.x==1:
                if self.grabbed==None:
                    if self.mode=="adjusting":
                        for bone in self.bones:
                            for point_index in range(len(bone["joint_rear"]["bubble_ball"])-1):
                                current_point=self.edges_pool[bone["joint_rear"]["bubble_ball"][point_index]]
                                cursor_point=self.mouse
                                next_point=self.edges_pool[bone["joint_rear"]["bubble_ball"][point_index+1]]
                                angle=self.scale.angle(current_point,cursor_point,next_point)
                                if 179<=angle<=181:
                                    self.grabbed={
                                        "type":"new_bubble_ball_point",
                                        "bone_index":self.bones.index(bone),
                                        "joint_position":"joint_rear",
                                        "index_to_be_inserted":point_index+1,
                                        "point_to_be_inserted":cursor_point
                                    }
                                    break
                            if len(bone["joint_rear"]["bubble_ball"])>2:
                                current_point=self.edges_pool[bone["joint_rear"]["bubble_ball"][-1]]
                                cursor_point=self.mouse
                                next_point=self.edges_pool[bone["joint_rear"]["bubble_ball"][0]]
                                angle=self.scale.angle(current_point,cursor_point,next_point)
                                if 179<=angle<=181:
                                    self.grabbed={
                                        "type":"new_bubble_ball_point",
                                        "bone_index":self.bones.index(bone),
                                        "joint_position":"joint_rear",
                                        "index_to_be_inserted":len(bone["joint_rear"]["bubble_ball"]),
                                        "point_to_be_inserted":cursor_point
                                    }
                            if self.grabbed!=None:
                                break
            # ------------------------
        # ------------ bubble ball outlines
        if self.control_visible:
            for bone in self.bones:
                # --------- first joint bubble ball
                bubble_ball_points=[]
                for point_index in bone["joint_front"]["bubble_ball"]:
                    point=self.edges_pool[point_index].list_point()
                    bubble_ball_points.append(point)
                if len(bubble_ball_points)>2:
                    pygame.draw.polygon(self.surface,self.color["transparent_black"],bubble_ball_points,1)
                # --------- second joint bubble ball
                bubble_ball_points=[]
                for point_index in bone["joint_rear"]["bubble_ball"]:
                    point=self.edges_pool[point_index].list_point()
                    bubble_ball_points.append(point)
                if len(bubble_ball_points)>2:
                    pygame.draw.polygon(self.surface,self.color["transparent_black"],bubble_ball_points,1)
        # ------------ draw bones
        if self.control_visible:
            for bone in self.bones:
                pygame.draw.circle(self.surface,self.color["transparent_black"],self.joints_pool[bone["joint_front"]["point"]].list_point(),self.joint_radius)
                pygame.draw.circle(self.surface,self.color["transparent_black"],self.joints_pool[bone["joint_rear"]["point"]].list_point(),self.joint_radius)
                pygame.draw.line(self.surface,self.color["transparent_black"],self.joints_pool[bone["joint_front"]["point"]].list_point(),self.joints_pool[bone["joint_rear"]["point"]].list_point(),3)
    def draw_hidden_manager(self):
        pygame.draw.circle(self.surface,self.color["hidden_manager"],(WIDTH,HEIGHT),self.delete_hidden_manager_size)
        if self.grabbed==None:
            if self.click.x==1:
                if time.time()>self.delete_show_hidden_last_clicked+1:
                    self.delete_show_hidden_last_clicked=time.time()
                    distance=self.scale.euclidean_distance(self.mouse,point2D(WIDTH,HEIGHT))
                    if distance<=self.delete_hidden_manager_size:
                        pass
                        self.delete_show_hidden=not self.delete_show_hidden
                        self.mode="adjusting"
        else:
            if self.grabbed["type"] in ["tools_properties","applying_tools_properties","make_these_changes"]:
                if self.click.x==1:
                    if time.time()>self.delete_show_hidden_last_clicked+1:
                        self.delete_show_hidden_last_clicked=time.time()
                        distance=self.scale.euclidean_distance(self.mouse,point2D(WIDTH,HEIGHT))
                        if distance<=self.delete_hidden_manager_size:
                            pass
                            self.delete_show_hidden=not self.delete_show_hidden
                            self.mode="adjusting"
        pygame.draw.circle(self.surface,self.color["hidden_manager"],(0,HEIGHT),self.tools_hidden_manager_size)
        if self.grabbed==None:
            if self.click.x==1:
                # print ("got here ")
                if time.time()>self.tools_show_hidden_last_clicked+1:
                    self.tools_show_hidden_last_clicked=time.time()
                    distance=self.scale.euclidean_distance(self.mouse,point2D(0,HEIGHT))
                    if distance<=self.tools_hidden_manager_size:
                        pass
                        self.tools_show_hidden=not self.tools_show_hidden
                        self.grabbed=None
                        self.mode="adjusting"
        else:
            if self.grabbed["type"] in ["tools_properties","applying_tools_properties","make_these_changes"]:
                if self.click.x==1:
                    # print ("got here ")
                    if time.time()>self.tools_show_hidden_last_clicked+1:
                        self.tools_show_hidden_last_clicked=time.time()
                        distance=self.scale.euclidean_distance(self.mouse,point2D(0,HEIGHT))
                        if distance<=self.tools_hidden_manager_size:
                            pass
                            self.tools_show_hidden=not self.tools_show_hidden
                            self.grabbed=None
                            self.mode="adjusting"
    def draw_tools(self):
        pass
        # time_font=pygame.font.SysFont("Menlo, Consolas, DejaVu Sans Mono, monospace",11,bold=True,italic=False)
        # object_time_font=time_font.render("Border Size",False,self.color["black"])
        # self.surface.blit(object_time_font,(80,HEIGHT-35))
        # print (self.tools)
        for tool in self.tools:
            # print (self.tools[tool])
            x=self.tools[tool]["x"]
            y=self.tools[tool]["y"]
            widths=self.tools[tool]["widths"][:]
            height=self.tools[tool]["height"]
            label=self.tools[tool]["label"]
            value=self.tools[tool]["value"]
            cumulative_width=0
            for width_index in range(len(widths)):
                if width_index==0:
                    pygame.draw.rect(self.surface,self.color["tools_box"],(x+cumulative_width,y,widths[width_index],height))
                    temp_font=pygame.font.SysFont("Menlo, Consolas, DejaVu Sans Mono, monospace",13,bold=True,italic=False)
                    object_temp_font=temp_font.render(label,False,self.color["black"])
                    self.surface.blit(object_temp_font,(x+cumulative_width+10,y+5))
                else:
                    pygame.draw.rect(self.surface,self.color["tools_box"],(x+cumulative_width,y,widths[width_index],height),1)
                    if self.click.x==1:
                        if time.time()>self.tools_show_hidden_last_clicked+1:
                            self.tools_show_hidden_last_clicked=time.time()
                        if x+cumulative_width<=self.mouse.x<=x+cumulative_width+widths[width_index] and y<=self.mouse.y<=y+height:
                            # print (tool,width_index)
                            self.grabbed={
                                "type":"tools_properties",
                                "tool":tool,
                                "input_index":width_index-1
                            }
                    if tool=="fill":
                        if value[width_index-1]==1:
                            pygame.draw.rect(self.surface,self.color["tools_box"],(x+cumulative_width+5,y+5,widths[width_index]-10,height-10))
                        else:
                            pygame.draw.rect(self.surface,self.color["tools_box"],(x+cumulative_width+10,y+10,widths[width_index]-20,height-20))
                    else:
                        temp_font=pygame.font.SysFont("Menlo, Consolas, DejaVu Sans Mono, monospace",13,bold=True,italic=False)
                        object_temp_font=temp_font.render(str(value[width_index-1]),False,self.color["white"])
                        self.surface.blit(object_temp_font,(x+cumulative_width+10,y+5))
                cumulative_width+=widths[width_index]
        # ------------------ help_line
        help_line="Alter these and click on Bones or Skins to set these properties"
        temp_font=pygame.font.SysFont("Menlo, Consolas, DejaVu Sans Mono, monospace",13,bold=True,italic=False)
        object_temp_font=temp_font.render(help_line,False,self.color["white"])
        # self.surface.blit(object_temp_font,(150,HEIGHT-30))
        # ------------------ make a pen
        x,y,radius=1000,615,30
        pygame.draw.circle(self.surface,self.color["tools_box"],(x,y),radius)
        type="make_these_changes"
        labels=type.split("_",)
        init_y=y-radius+5
        for label in labels:
            temp_font=pygame.font.SysFont("Menlo, Consolas, DejaVu Sans Mono, monospace",11,bold=True,italic=False)
            object_temp_font=temp_font.render(label,False,self.color["black"])
            self.surface.blit(object_temp_font,(x-((len(label)/2)*8),init_y))
            init_y+=15
        if self.click.x==1:
            distance=self.scale.euclidean_distance(self.mouse,point2D(x,y))
            if distance<=radius:
                self.grabbed={
                    "type":type
                }
        # ----------------------------
    def set_current_tools_properties(self):
        # print ("",end="")
        pass
        if self.grabbed!=None:
            if self.grabbed["type"]=="tools_properties":
                if self.grabbed["tool"]=="fill":
                    tool=self.grabbed["tool"]
                    input_index=self.grabbed["input_index"]
                    if input_index==0:
                        self.tools[tool]["value"]=[1,0]
                    elif input_index==1:
                        self.tools[tool]["value"]=[0,1]
                else:
                    tool=self.grabbed["tool"]
                    input_index=self.grabbed["input_index"]
                    existing_value=self.tools[tool]["value"][input_index]
                    limit=30 if tool=="border_size" else 255
                    if self.current_alphabet!=None:
                        if self.current_alphabet!="negative":
                            if self.current_alphabet==-1:
                                new_value=existing_value//10
                                self.tools[tool]["value"][input_index]=new_value
                            else:
                                new_value=(existing_value*10)+self.current_alphabet
                                self.tools[tool]["value"][input_index]=min(new_value,limit)
    def manage_mode_setters(self):
        for mode_setter_index in self.mode_setters:
            # print (mode_setter_index)
            if (self.mode_setters[mode_setter_index]["hidden"]=="True" and self.delete_show_hidden) or self.mode_setters[mode_setter_index]["hidden"]=="False":
                x=self.mode_setters[mode_setter_index]["x"]
                y=self.mode_setters[mode_setter_index]["y"]
                radius=self.mode_setters[mode_setter_index]["radius"]
                fill_color=self.mode_setters[mode_setter_index]["fill_color"]
                pygame.draw.circle(self.surface,fill_color,(x,y),radius)
                image=pygame.image.load(self.mode_setters[mode_setter_index]["image_URL"])
                image=pygame.transform.scale(image,(int(radius*1.5),int(radius*1.5)))
                self.surface.blit(image,(x-radius+radius//4,y-radius))
                if self.grabbed==None:
                    if self.click.x==1:
                        dist=self.scale.euclidean_distance(self.mouse,point2D(x,y))
                        if dist<=radius:
                            self.mode=mode_setter_index
                            # print (mode_setter_index)
                            self.click.x=0
                            self.grabbed=None
    def make_bones(self):
        if self.click.x==1:
            if time.time()>=self.new_node["last_clicked"]+1:
                self.new_node["last_clicked"]=time.time()
                self.click.x=0
                if len(self.new_node["points"])<2:
                    not_exist=True
                    for point in self.new_node["points"]:
                        if point.x==self.mouse.x and point.y==self.mouse.y:
                            not_exist=False
                    if not_exist:
                        self.new_node["points"].append(self.mouse)
                        if len(self.new_node["points"])==2:
                            self.joints_pool.append(self.new_node["points"][0])
                            self.joints_pool.append(self.new_node["points"][1])
                            self.bones.append(
                                {
                                    "joint_front":{
                                        "point":self.joints_pool.index(self.new_node["points"][0]),
                                        "bubble_ball":[],
                                        "fill":True,
                                        "fill_color":[0,0,0],
                                        "border_size":1,
                                        "border_color":[0,0,0]
                                    },
                                    "joint_rear":{
                                        "point":self.joints_pool.index(self.new_node["points"][1]),
                                        "bubble_ball":[],
                                        "fill":True,
                                        "fill_color":[0,0,0],
                                        "border_size":1,
                                        "border_color":[0,0,0]
                                    }
                                }
                            )
                            self.new_node["points"]=[]
        if len(self.new_node["points"])==1:
            joint_front=self.new_node["points"][0].list_point()
            joint_rear=self.mouse.list_point()
            pygame.draw.line(self.surface,self.color["transparent_black"],joint_front,joint_rear,1)
    def sync_bones(self):
        if self.grabbed!=None:
            if self.grabbed["type"]=="sync_bones":
                if self.click.x==1:
                    pass
                    for bone in self.bones:
                        if self.bones.index(bone)!=self.grabbed["bone_index"]:
                            distance=self.scale.euclidean_distance(self.joints_pool[bone["joint_front"]["point"]],self.mouse)
                            if distance<=self.joint_radius:
                                # print ("front",self.bones.index(bone),time.time())
                                target_joint_index_of_joints_pool=bone["joint_front"]["point"]
                                # grabbed_bone_index=self.grabbed["bone_index"]
                                self.bones[self.grabbed["bone_index"]][self.grabbed["joint_position"]]["point"]=target_joint_index_of_joints_pool
                                pass
                            distance=self.scale.euclidean_distance(self.joints_pool[bone["joint_rear"]["point"]],self.mouse)
                            if distance<=self.joint_radius:
                                # print ("rear",self.bones.index(bone),time.time())
                                target_joint_index_of_joints_pool=bone["joint_rear"]["point"]
                                # grabbed_bone_index=self.grabbed["bone_index"]
                                self.bones[self.grabbed["bone_index"]][self.grabbed["joint_position"]]["point"]=target_joint_index_of_joints_pool
                                pass
                else:
                    self.grabbed=None
    def make_bubble_ball_points(self):
        # print ("make_bubble_ball_points")
        if self.click.x==1:
            if time.time()>self.making_bubble_ball_last_clicked+1:
                self.making_bubble_ball_last_clicked=time.time()
                for bone in self.bones:
                    if len(bone["joint_front"]["bubble_ball"])==0:
                        distance=self.scale.euclidean_distance(self.joints_pool[bone["joint_front"]["point"]],self.mouse)
                        if distance<=self.joint_radius:
                            neighbors=self.get_neighborhoods(self.joints_pool[bone["joint_front"]["point"]])
                            for neighbor in neighbors:
                                self.edges_pool.append(neighbor)
                                self.bones[self.bones.index(bone)]["joint_front"]["bubble_ball"].append(self.edges_pool.index(neighbor))
                            self.making_bubble_ball_last_clicked=time.time()
                            break
                    if len(bone["joint_rear"]["bubble_ball"])==0:
                        distance=self.scale.euclidean_distance(self.joints_pool[bone["joint_rear"]["point"]],self.mouse)
                        if distance<=self.joint_radius:
                            pass
                            neighbors=self.get_neighborhoods(self.joints_pool[bone["joint_rear"]["point"]])
                            for neighbor in neighbors:
                                self.edges_pool.append(neighbor)
                                self.bones[self.bones.index(bone)]["joint_rear"]["bubble_ball"].append(self.edges_pool.index(neighbor))
                            self.making_bubble_ball_last_clicked=time.time()
                            break
    def sync_bubble_ball_points(self):
        if self.grabbed!=None:
            if self.grabbed["type"]=="sync_bubble_ball_points":
                if self.click.x==1:
                    pass
                    grabbed_bone_index=self.grabbed["bone_index"]
                    grabbed_bubble_ball_index=self.grabbed["bubble_ball_index"]
                    grabbed_joint_position=self.grabbed["joint_position"]
                    grabbed_bubble_ball_point=self.edges_pool[self.bones[grabbed_bone_index][grabbed_joint_position]["bubble_ball"][grabbed_bubble_ball_index]]
                    victim=None
                    for bone in self.bones:
                        # if self.bones.index(bone)!=self.grabbed["bone_index"]:
                        # print ("hahahahahahaha")
                        # joint front
                        for bubble_ball_index in bone["joint_front"]["bubble_ball"]:
                            current_bubble_ball_point=self.edges_pool[bubble_ball_index]
                            distance=self.scale.euclidean_distance(current_bubble_ball_point,self.mouse)
                            if distance<=self.edge_radius:
                                victim={
                                    "bone_index":self.bones.index(bone),
                                    "joint_position":"joint_front",
                                    "bubble_ball_index":bubble_ball_index
                                }
                        # joint rear
                        for bubble_ball_index in bone["joint_rear"]["bubble_ball"]:
                            current_bubble_ball_point=self.edges_pool[bubble_ball_index]
                            distance=self.scale.euclidean_distance(current_bubble_ball_point,self.mouse)
                            if distance<=self.edge_radius:
                                victim={
                                    "bone_index":self.bones.index(bone),
                                    "joint_position":"joint_rear",
                                    "bubble_ball_index":bubble_ball_index
                                }
                    if victim!=None:
                        victim_bone_index=victim["bone_index"]
                        victim_joint_position=victim["joint_position"]
                        victim_bubble_ball_index=victim["bubble_ball_index"]
                        self.bones[grabbed_bone_index][grabbed_joint_position]["bubble_ball"][grabbed_bubble_ball_index]=victim_bubble_ball_index
                else:
                    self.grabbed=None
    def delete_bones(self):
        if self.grabbed!=None:
            if self.grabbed["type"]=="delete_bones":
                if self.click.x==1:
                    pass
                    self.bones.pop(self.grabbed["bone_index"])
                    self.grabbed=None
                else:
                    self.grabbed=None
    def delete_bubble_ball(self):
        if self.grabbed!=None:
            if self.grabbed["type"]=="delete_bubble_ball":
                if self.click.x==1:
                    pass
                    self.bones[self.grabbed["bone_index"]][self.grabbed["joint_position"]]["bubble_ball"]=[]
                    self.grabbed=None
                else:
                    self.grabbed=None
    def delete_bubble_ball_edge(self):
        if self.grabbed!=None:
            if self.grabbed["type"]=="delete_bubble_ball_edge":
                if self.click.x==1:
                    pass
                    self.bones[self.grabbed["bone_index"]][self.grabbed["joint_position"]]["bubble_ball"].pop(self.grabbed["bubble_ball_index"])
                    self.grabbed=None
                else:
                    self.grabbed=None
    def make_these_changes(self):
        if self.grabbed!=None:
            if self.grabbed["type"]=="make_these_changes":
                if self.click.x==1:
                    for bone in self.bones:
                        # ----- joint_front
                        distance=self.scale.euclidean_distance(self.mouse,self.joints_pool[self.bones[self.bones.index(bone)]["joint_front"]["point"]])
                        if distance<=self.joint_radius:
                            fill=self.tools["fill"]["value"]
                            self.bones[self.bones.index(bone)]["joint_front"]["fill"]=True if fill==[0,1] else False
                            fill_color=self.tools["fill_color"]["value"][:]
                            self.bones[self.bones.index(bone)]["joint_front"]["fill_color"]=fill_color
                            border_size=self.tools["border_size"]["value"][0]
                            self.bones[self.bones.index(bone)]["joint_front"]["border_size"]=border_size
                            border_color=self.tools["border_color"]["value"][:]
                            self.bones[self.bones.index(bone)]["joint_front"]["border_color"]=border_color
                        # ----- joint_rear
                        distance=self.scale.euclidean_distance(self.mouse,self.joints_pool[self.bones[self.bones.index(bone)]["joint_rear"]["point"]])
                        if distance<=self.joint_radius:
                            fill=self.tools["fill"]["value"]
                            self.bones[self.bones.index(bone)]["joint_rear"]["fill"]=True if fill==[0,1] else False
                            fill_color=self.tools["fill_color"]["value"][:]
                            self.bones[self.bones.index(bone)]["joint_rear"]["fill_color"]=fill_color
                            border_size=self.tools["border_size"]["value"][0]
                            self.bones[self.bones.index(bone)]["joint_rear"]["border_size"]=border_size
                            border_color=self.tools["border_color"]["value"][:]
                            self.bones[self.bones.index(bone)]["joint_rear"]["border_color"]=border_color
    def draw_navigators(self):
        # print (self.navigators)
        pygame.draw.circle(self.surface,self.color["navigator"],(0,HEIGHT//2),10)
        pygame.draw.circle(self.surface,self.color["navigator"],(WIDTH//2,HEIGHT),10)
        for navigator in self.navigators:
            x=self.navigators[navigator]["x"]
            y=self.navigators[navigator]["y"]
            width=self.navigators[navigator]["width"]
            height=self.navigators[navigator]["height"]
            pygame.draw.rect(self.surface,self.color["navigator"],(x,y,width,height))
            if self.click.x==1:
                if (x)<=self.mouse.x<=(x+width) and (y)<=self.mouse.y<=(y+height):
                    # print ()
                    adjust_x,adjust_y=0,0
                    adjust_range=10
                    if navigator=="up":
                        adjust_y=+adjust_range
                    elif navigator=="down":
                        adjust_y=-adjust_range
                    elif navigator=="left":
                        adjust_x=adjust_range
                    elif navigator=="right":
                        adjust_x=-adjust_range
                    for joints_pool_index in range(len(self.joints_pool)):
                        self.joints_pool[joints_pool_index].x+=adjust_x
                        self.joints_pool[joints_pool_index].y+=adjust_y
                    for edges_pool_index in range(len(self.edges_pool)):
                        self.edges_pool[edges_pool_index].x+=adjust_x
                        self.edges_pool[edges_pool_index].y+=adjust_y
    def do_main_operations(self):
        self.draw_bones()
        self.draw_hidden_manager()
        if self.control_visible:
            self.manage_mode_setters()
            self.draw_navigators()
        if self.tools_show_hidden:
            self.draw_tools()
            self.set_current_tools_properties()
        self.make_these_changes()
        self.save_backup()
        if self.mode=="adjusting":
            self.adjusting()
        elif self.mode=="make_bones":
            self.make_bones()
        elif self.mode=="sync_bones":
            self.sync_bones()
        elif self.mode=="make_bubble_ball_points":
            self.make_bubble_ball_points()
        elif self.mode=="sync_bubble_ball_points":
            self.sync_bubble_ball_points()
        elif self.mode=="delete_bones":
            self.delete_bones()
        elif self.mode=="delete_bubble_ball":
            self.delete_bubble_ball()
        elif self.mode=="delete_bubble_ball_edge":
            self.delete_bubble_ball_edge()
        # --------------------------------
        # print (self.grabbed)
        # print (self.grabbed,self.tools["fill"]["value"][0])
        # print (self.bones)
        # print (self.tools_show_hidden)
        # print (self.tools["fill"]["value"][0])
        # print (self.mouse.list_point())
        # print(self.click.list_point())
        # --------------------------------
    def run(self):
        play=True
        while play:
            surface.fill(self.color["background"])
            mouse=pygame.mouse.get_pos()
            self.mouse=point2D(mouse[0],mouse[1])
            click=pygame.mouse.get_pressed()
            self.click=point2D(click[0],click[1],click[2])
            for event in pygame.event.get():
                if event.type==QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type==KEYDOWN:
                    if event.key==K_TAB:
                        play=False
                    elif event.key==K_SPACE:
                        self.control_visible=not self.control_visible
                    elif event.key==K_ESCAPE:
                        if self.mode=="make_bones":
                            self.new_node["points"]=[]
                    elif 48<=event.key<=57 or 97<=event.key<=122 or event.key==45:
                        # - 45
                        if 48<=event.key<=57:
                            self.current_alphabet=int(chr(event.key))
                        if event.key==45:
                            self.current_alphabet="negative"
                    elif event.key==K_BACKSPACE:
                        self.current_alphabet=-1
            #--------------------------------------------------------------
            self.do_main_operations()
            self.current_alphabet=None
            # -------------------------------------------------------------
            pygame.display.update()
            ft.tick(fps)
        # print (self.garbage)
        # print (self.support_garbage)

if __name__=="__main__":
    app(surface).run()



# #----------------
