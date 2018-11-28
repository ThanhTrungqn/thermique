#!/usr/bin/python

import numpy as np
import time
from gpiozero import LED
from htpa import *
from improcess import *
import paho.mqtt.client as mqtt
import mysql.connector

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

# The callback for when a PUBLISH message is received from the server.
def payload(im, temp, presence, pin, pout):
    	im =  np.around(im).astype(int)
    	payload = [ y for x in im for y in x]
    	payload = ','.join(map(str,payload))
    	message = '{"presence":' + str(presence)
    	message += ',"temperature":' + str(temp)
	message += ',"person_in":' + str(pin)
	message += ',"person_out":' + str(pout)
	message += ',"pixel":[' + payload +']'
	message += '}'
    	return message

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)

mydb = mysql.connector.connect(
  host="localhost",
  user="username",
  passwd="password",
  database="dbcomptage"
)


i = 0
take_Offset=False
dev = HTPA(0x1A)
improcess = IMPROCESS(32,32)
#ledR = LED(4)

# Create Filter Gaussian
while(True):

	millis_start = int(round(time.time() * 1000))
	print("Capturing image " + str(i))
	(pixel_values, ptats) = dev.capture_image()
	dev.send_command(dev.generate_expose_block_command(0, blind=False), wait=False)
	(im, temps) = dev.temperature_compensation(pixel_values, ptats)
	im -= 65280


	improcess.image_processing(im,i)

	#if (improcess.person_in > 0):
        message = payload(improcess.img_filtered_dif_pos, (temps - 2731)/10, improcess.presence, improcess.person_in, improcess.person_out)
	client.publish("songohan",payload=message,qos=0,retain=False)
	i += 1
	millis_end = int(round(time.time() * 1000))
	print(millis_end-millis_start)

dev.close()
