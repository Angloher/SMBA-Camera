import glob,os
import matplotlib.image
import matplotlib.pyplot as plt
import cv2
import math
import random
import matplotlib.patches as patches
from .vehicle_positions import VehiclePositions

class Visualizer:
    def __init__(self, camera_model, drive_num):
        self.camera_model = camera_model
        self.drive_num = drive_num
        self.car_count=0
        self.Nocar_count=0

    def getVehicleColor(self, name):
        color='none'
        if name == 'Car':
            color = 'red'
        elif name == 'Van':
            color = 'orange'
        elif name == 'Truck':
            color = 'yellow'
        elif name == 'Tram':
            color = 'blue'
        elif name == 'Cyclist':
            color = 'green'
        elif name == 'Pedestrian':
            color = 'black'
        elif name == 'Person':
            color = 'brown'
        elif name == 'Misc':
            color = 'grey'
        return color

    def save_non_cars(self,img,list):
        height,width,_=img.shape
        xstart=random.randint(0,500)
        ystart=random.randint(0,200)
        for x in range(xstart,width-64,5*96):
            for y in range(ystart,height-64,3*96):
                nocar=True
                for pos in list:
                    if not((x<pos[0]-50) or (x>pos[0]+100)) and ((y<pos[1]+50) or (y>pos[1]-100)):
                        nocar=False
                if nocar:
                    scale=random.uniform(1,2.5)
                    im=img[int(y):int(y+(64/scale)),int(x):int(x+(64/scale))]
                    im = cv2.resize(im, (64, 64))
                    cv2.imwrite('non_vehicles/'+str(self.drive_num)+'Nonvehicle'+str(self.Nocar_count)+'.png',im)
                    self.Nocar_count+=1

    def checkCoord(self,img,pos):
        height,width,_=img.shape
        if pos[0]<0:
            pos[0]=0
        if pos[0]>width-64:
            pos[0]=width-64
        if pos[1]-64<0:
            pos[1]=64
        if pos[1]>height:
            pos[1]=height
        return pos[0],pos[1]


    def save_cars(self,img,list):

        for pos in list:
            scale=(pos[2]/15.0)
            if scale<1:
                scale=1
            pos[0],pos[1]=self.checkCoord(img,pos)
            im=img[int(pos[1]-(64/scale)):int(pos[1]),int(pos[0]):int(pos[0]+(64/scale))]
            im=cv2.resize(im,(64,64))
            cv2.imwrite('vehicles/'+str(self.drive_num)+'vehicle'+str(self.car_count)+'.png',im)

            self.car_count+=1
        self.save_non_cars(img,list)

    def showVisuals(self, path,date,CamNum='00'):
        fig=plt.figure()
        plt.get_current_fig_manager().window.state('zoomed')
        i=0
        vehiclePositions = VehiclePositions(path,date, self.drive_num)

        syncFolder = "{0}_drive_{1}_sync".format(date,self.drive_num)
        imgFolder = "image_{}".format(CamNum)
        imagePath = os.path.join(path, date, syncFolder, date, syncFolder, imgFolder,'data')
        img_glob = os.path.join(imagePath, "*.png")
        print (img_glob)
        for pic in glob.glob(img_glob):
            if not plt.get_fignums():
                # window has been closed
                return
            img=cv2.imread(pic)
            #print ('new Image:')
            ax1=fig.add_subplot(211)
            ax1.imshow(img,cmap='gray')


            ax2=fig.add_subplot(212)
            car_list=[]
            vehicles=vehiclePositions.getVehiclePosition(i)
            count=len(vehicles)
            for j in range(count):
                name=vehicles[j][0]
                color=self.getVehicleColor(name)
                ax2.add_patch(patches.Rectangle((-vehicles[j][2]+vehicles[j][3], vehicles[j][1]-vehicles[j][4]),vehicles[j][3],vehicles[j][4],angle=vehicles[j][5],color=color) )
                vehicleCoord=[vehicles[j][1],vehicles[j][2],vehicles[j][6]]
                image_coords = self.camera_model.projectToImage(vehicleCoord)
                ax1.add_patch(patches.Rectangle(image_coords,2,2,color=color))
                if name=='Car':
                    dist=math.sqrt(vehicleCoord[0]**2+vehicleCoord[1]**2)
                    image_coords.append(dist)
                    car_list.append(image_coords)
            #fig.draw
            if i%6==0:
                self.save_cars(img,car_list)
            ax2.set_ylim([0,100])
            ax2.set_xlim([-25,25])
            ax2.set_aspect(1)
            plt.pause(0.00000001)
            fig.clear()

            #time.sleep(10)
            i+=1

