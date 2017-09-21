import argparse
import cv2
import glob
import os
import sys
import pickle
from datetime import datetime
from Vehicle_detection import VehicleDetection
#import image_processing.vehicle_detection.VehicleDetection as VehicleDetection

def detect_vehicles_and_save(path, file_name):
    start_time = datetime.now()
    images = []
    for i in glob.glob(os.path.join(path, '*.png')):
        images.append(cv2.imread(i))
    vehicle_detector = VehicleDetection(images[0])
    vehicles = []

    counter = 1
    #images = images[:10]
    print("amount of images: {}, takes about {}m".format(len(images), len(images)/0.75))
    for i in images:
        vehicles.append(vehicle_detector.find_vehicles(i))
        now = datetime.now()
        print("{}/{} time remaining: {}".format(counter,len(images), (now-start_time)/counter*(len(images)-counter)))
        counter += 1

    path = os.path.join('data', 'detected_vehicles')
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = os.path.join(path, file_name)

    with open(file_path,'wb') as f:
        pickle.dump(vehicles, f)

def load_detected_vehicles(file_name):
    file_path = os.path.join('data', 'detected_vehicles', file_name)
    with open(file_path, 'rb') as f:
        return pickle.load(f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Renders Kitti data with marked positions of objects')
    parser.add_argument('images_path')
    parser.add_argument('file_name')
    #parser.add_argument('path')
    args = parser.parse_args()
    detect_vehicles_and_save(args.images_path, args.file_name)
    #print(load_detected_vehicles(args.path))
