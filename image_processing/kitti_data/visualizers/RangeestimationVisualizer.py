import os
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from ..vehicle_positions import VehiclePositions
import cv2
import sys
import image_processing.util.Util as util
from image_processing.vehicle_detection import VehicleDetection,match_vehicles_stereo
from image_processing.position_estimation import PositionEstimationStereoVision



# detected cars within the kitti images and estimations for distances

class RangeestimationVisualizer:
    def __init__(self, kitti, drive_num, start_frame=0, end_frame=0):
        self.camera_model_velo_camera_0 = kitti.getVeloCameraModel()
        self.camera_model_1 = kitti.getCameraModel(0)
        self.camera_model_2 = kitti.getCameraModel(1)
        self.drive_num = drive_num
        self.vehicledetectioninit = 0
        self.detector = None
        self.start_frame = start_frame
        self.end_frame = end_frame

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

    def getRealVehiclePositions(self, imgId, vehiclePositions):
        ''' finds vehicles within the image. Will just '''
        return vehiclePositions.getVehiclePosition(imgId)

    def findVehiclesOnStereoImages(self, stereovision_image):
        if not self.vehicledetectioninit:
            self.detector=VehicleDetection(stereovision_image.image0)
        self.vehicledetectioninit=1
        cars_img_one=self.detector.find_vehicles(stereovision_image.image0)
        cars_img_two = self.detector.find_vehicles(stereovision_image.image1)
        stereovision_image.vehicles = match_vehicles_stereo(cars_img_one, cars_img_two)

        for vehicle_pair in stereovision_image.vehicles:
            if not (vehicle_pair[0] and vehicle_pair[1]):
                stereovision_image.ranges.append(None)
                continue
            position_estimator = PositionEstimationStereoVision(self.camera_model_1,self.camera_model_2)
            estimated_range = position_estimator.estimate_range_stereo(vehicle_pair[0], vehicle_pair[1])
            stereovision_image.ranges.append(estimated_range)

    def showVisuals(self, path, date):
        generator = self.showVisuals_generator(path, date, wait_for_fig_showing=True)
        for _ in generator:
            a = 1 # consume generator (normally play animation)

    def showVisuals_generator(self, path, date, wait_for_fig_showing=False):
        fig=plt.figure()
        #plt.get_current_fig_manager().window.state('zoomed') works only in win
        i=0
        vehiclePositions = VehiclePositions(path,date, self.drive_num)

        syncFolder = "{0}_drive_{1}_sync".format(date, self.drive_num)
        imgFolder = os.path.join(path, date, syncFolder, date, syncFolder, "image_{}",'data')
        cam0_imgPath = imgFolder.format('02')
        cam1_imgPath = imgFolder.format('03')
        images_camera_0 = map(lambda img: os.path.join(cam0_imgPath, img), os.listdir(cam0_imgPath))
        images_camera_1 = map(lambda img: os.path.join(cam1_imgPath, img), os.listdir(cam1_imgPath))

        # check that for every frame of one camera there is an image from the other
        assert(len(images_camera_0) == len(images_camera_1))
        images_camera_0.sort()
        images_camera_1.sort()
        # load all images:
        sys.stdout.write("Loading images...")
        sys.stdout.flush()
        start_time = time.time()
        loaded_images = []
        for i, (pic0, pic1) in enumerate(zip(images_camera_0, images_camera_1)):

            loaded_pic_0 = cv2.imread(pic0, cv2.IMREAD_UNCHANGED)
            loaded_pic_1 = cv2.imread(pic1, cv2.IMREAD_UNCHANGED)
            vehicles = self.getRealVehiclePositions(i, vehiclePositions)

            loaded_images.append(StereoVisionImage(loaded_pic_0, loaded_pic_1, vehicles))

            # convert RGB between BGR : cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        sys.stdout.write("{}s\n".format(time.time() - start_time))

        if (self.start_frame and self.end_frame):
            loaded_images = loaded_images[self.start_frame:self.end_frame]
        elif (self.start_frame):
            loaded_images = loaded_images[self.start_frame:]
        elif (self.end_frame):
            loaded_images = loaded_images[:self.end_frame]

        # search for vehicles
        sys.stdout.write("Searching for Vehicles in {} images...".format(len(loaded_images)))
        sys.stdout.flush()
        start_time = time.time()
        for stereo_vision_image in loaded_images:
            self.findVehiclesOnStereoImages(stereo_vision_image)
        sys.stdout.write("{}s\n".format(time.time() - start_time))


        print("Show Range estimations...\n")

        for stereo_vision_image in loaded_images:
            img0 = stereo_vision_image.image0
            img1 = stereo_vision_image.image1
            real_vehicle_positions = stereo_vision_image.real_vehicle_positions

            if not plt.get_fignums():
                # window has been closed
                return

            #print ('new Image:')
            ax1=fig.add_subplot(211)
            ax1.imshow(img0,cmap='gray')
            plt.pause(1)

            ax2=fig.add_subplot(212)

            # TODO: use vehicle positions from image analysis
            count = len(real_vehicle_positions)
            for j in range(count):
                v = real_vehicle_positions[j]
                name = v.type
                color = self.getVehicleColor(name)

                # show car in top-view coord system
                ax2.add_patch(
                    patches.Rectangle((- v.yPos + v.width, v.xPos - v.length), v.width, v.length, angle=v.angle,
                                      color=color))

            for vehicle_pair,estimated_range in zip(stereo_vision_image.vehicles, stereo_vision_image.ranges):
                vehicle_0 = vehicle_pair[0]
                coord = mean_point(vehicle_0)
                # show vehicle position in image

                patch = patches.Rectangle(coord, 20, 20, color='red')
                ax1.add_patch(patch)
                # add distance description
                ax1.text(coord[0], coord[1]+40, "{}m".format(estimated_range), color='red')


            #fig.draw
            ax2.set_ylim([0,100])
            ax2.set_xlim([-25,25])
            ax2.set_aspect(1)

            if wait_for_fig_showing:
                plt.pause(0.00001)
            else:
                yield fig

            fig.clear()

            #time.sleep(10)
            i+=1

class StereoVisionImage:
    def __init__(self, imageWithVehicles0, imageWithVehicles1, real_vehicle_positions):
        self.image0 = imageWithVehicles0
        self.image1 = imageWithVehicles1
        self.real_vehicle_positions = real_vehicle_positions
        self.vehicles = []
        self.ranges = []

def mean_point(p):
    mean_p = (
        p[0][0] + 0.5 * (p[1][0] - p[0][0]),
        p[0][1] + 0.5 * (p[1][1] - p[0][1])
    )
    return mean_p
