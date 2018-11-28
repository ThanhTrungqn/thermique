#!/usr/bin/python

import time
import numpy as np
from tracking import *
import copy
import struct
import cv2


class IMPROCESS:
	def __init__(self, height , width):
		#Create constant
		self.img_height = height
		self.img_width  = width
		#Create Gaussian filter
		self.init_filter_Gaussian(5)

		#Create zone for BackGround
		self.bg_sum = np.zeros((height,width))
		self.bg = np.zeros((height,width))
		self.bg_count = 0
		self.bg_size = 1000

		#Create zone for Image
		self.img_pixel = np.zeros((self.img_height, self.img_width))
		self.img_filtered = np.zeros((self.img_height, self.img_width))
		self.img_dif_pos = np.zeros((self.img_height, self.img_width))
		self.img_dif_neg = np.zeros((self.img_height, self.img_width))
		self.img_filtered_dif_pos = np.zeros((self.img_height, self.img_width))
		self.img_filtered_dif_neg = np.zeros((self.img_height, self.img_width))

		#Create zone for ThreshShold
		self.threshold = 40
		self.threshold_min = 4
		self.alpha = 0.1
		self.threshold_seuil = 60 # 60%
		#Create zone for Image ThreshSould
		self.img_binary =  np.zeros((self.img_height, self.img_width))
		self.img_label = np.zeros((self.img_height, self.img_width))
		self.img_one = np.ones((self.img_height, self.img_width))
		#Create zone for Labeling
		self.LabelMax = 100
		self.Label = []
		self.init_list_label()

		self.presence = 0
		self.person_in = 0
		self.person_out = 0
		self.class_tracking = TRACKING()

	def init_list_label(self):
		self.Label = []
		for i in range(self.LabelMax):
			self.Label.append(Label(i,0,0,0,0,0,0,False))

	def get_image_process(self, img):
		self.img_pixel = img
	def init_filter_Gaussian(self ,size):
		self.filter = np.ones((size,size),np.float32)/(size*size)
		#self.filter = cv2.blur(img,(size,size))
	def apply_filter_Gaussian(self, img, filter):
		img_filtered =  cv2.filter2D(img, -1, filter)
		img_filtered =  cv2.blur(img,(5,5))
		return img_filtered

	def update_bg (self):
		if (self.bg_count == 0): #if 1st image
			self.bg_count +=1
			self.bg_sum += self.img_pixel
			self.bg = self.bg_sum / self.bg_count
		else:			#if not 1st image
			if (self.bg_count >= self.bg_size):
				self.bg_count /=2
				self.bg_sum /=2
			if (self.bg_count < self.bg_size):
				img1 = self.img_binary * self.bg
				img2 = (1-self.img_binary) * self.img_pixel
				self.bg_count += 1
				self.bg_sum += img1  + img2
				self.bg = self.bg_sum / self.bg_count

	def get_image_offset(self):
		img_dif = self.img_pixel - self.bg
		self.img_dif_pos = np.where(img_dif > 0,img_dif,0)
		self.img_dif_neg = np.where(img_dif < 0,0 , img_dif)

	def get_threshold (self):
		y,x = np.histogram(self.img_filtered_dif_pos, bins=np.arange(255))
		count = 0
		threshold = 0
		for var in x:
			count += y[var]
			pourcent = (count*100)/(32*32)

			if ( pourcent > self.threshold_seuil):
				threshold = var
				break

		if (threshold < self.threshold_min):
			threshold = self.threshold_min
		self.threshold = self.threshold * 0.9 + threshold * 0.1

	def image_threshold (self):
		self.img_binary = (self.img_filtered_dif_pos >  self.threshold) * self.img_one

	def image_morphology (self):
		kernel = np.ones((3,3),np.uint8)
		self.img_binary = cv2.morphologyEx(self.img_binary, cv2.MORPH_OPEN, kernel)
		self.img_binary = cv2.morphologyEx(self.img_binary, cv2.MORPH_CLOSE, kernel)

	def FloodFill(self, X, Y, Label):
		self.Label[Label].size +=1
		if (self.Label[Label].size == 1):
			self.Label[Label].top=Y
			self.Label[Label].bottom=Y
			self.Label[Label].left=X
			self.Label[Label].right=X
		else:
			if ( self.Label[Label].bottom < Y ):
				self.Label[Label].bottom = Y
			if ( self.Label[Label].top > Y ):
                                self.Label[Label].top = Y
			if ( self.Label[Label].right < X ):
                                self.Label[Label].right = X
			if ( self.Label[Label].left > X ):
                                self.Label[Label].left = X

		self.Label[Label]
    		self.img_label[X,Y] = Label
    		for varY in (Y-1,Y,Y+1):
			for varX in (X-1,X,X+1):
				if (varX >=0 and varX < self.img_width and varY >= 0 and varY < self.img_height ):
        				if ( self.img_label [ varX, varY] == 1):
            					self.FloodFill(varX, varY, Label)

	def connectedComponents(self):
		self.init_list_label()
		Label = 1
		for Y in range(self.img_height):
			for X in range(self.img_width):
				if (self.img_label[X,Y] == 1):
					Label +=1
					self.FloodFill(X,Y,Label)

	def labeling (self):
		self.img_label = self.img_binary*1
		self.connectedComponents()

	def image_processing(self, img, idx):
		#get image
		self.get_image_process(img)
		#update bg
		if (self.bg_count == 0):
			self.update_bg()

		#take image soustract
		self.get_image_offset()
		#filter Gaussian
		self.img_filtered_dif_pos = self.apply_filter_Gaussian(self.img_dif_pos, self.filter)
		self.get_threshold()
		self.image_threshold()
		self.image_morphology()
		self.labeling()
		(self.presence, self.person_in, self.person_out) = self.class_tracking.labelTracking(self.Label, self.class_tracking.tTracking , idx)
		self.update_bg()
		#print(len(self.Label))
