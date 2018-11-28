#!/usr/bin/python

from periphery import I2C
import time
import numpy as np
np.set_printoptions(threshold=np.inf)
import copy
import struct

class HTPA:
	def __init__(self, address, revision="2018"):
		self.address = address
		self.i2c = I2C("/dev/i2c-1")

		if revision == "2018":
			self.blockshift = 4
		else:
			self.blockshift = 2

		print("Wakeup systeme")
		wakeup_and_blind = self.generate_command(0x01, 0x01) # wake up the device

		print("Get EEPROM data")
		eeprom = self.get_eeprom()
		self.extract_eeprom_parameters(eeprom)
		self.eeprom=eeprom

		print("Write config capteur")
		print(self.MBITc)
		print(self.BIASc)
		print(self.CLKc)
		print(self.BPAc)
		print(self.PUc)
		adc_res = self.generate_command(0x03, self.MBITc) # set ADC resolution to 16 bits
		pull_ups = self.generate_command(0x09, self.PUc)

		print("Initializing capture settings")

		self.send_command(wakeup_and_blind)
		self.send_command(adc_res)
		self.send_command(pull_ups)

		self.set_bias_current(self.BIASc)
		self.set_clock_speed(self.CLKc)
		self.set_cm_current(self.BPAc)


		# initialize offset to zero
		self.offset = np.zeros((32, 32))

	def set_bias_current(self, bias):
		if bias > 31:
			bias = 31
		if bias < 0:
			bias = 0

		bias = int(bias)

		bias_top = self.generate_command(0x04, bias)
		bias_bottom = self.generate_command(0x05, bias)

		self.send_command(bias_top)
		self.send_command(bias_bottom)

	def set_clock_speed(self, clk):
		if clk > 63:
			clk = 63
		if clk < 0:
			clk = 0

		clk = int(clk)

		clk_speed = self.generate_command(0x06, clk)

		self.send_command(clk_speed)

	def set_cm_current(self, cm):
		if cm > 31:
			cm = 31
		if cm < 0:
			cm = 0

		cm = int(cm)

		cm_top = self.generate_command(0x07, cm)
		cm_bottom = self.generate_command(0x08, cm)

		self.send_command(cm_top)
		self.send_command(cm_bottom)

	def get_eeprom(self, eeprom_address=0x50):
		# Two separate I2C transfers in case the buffer size is small
		q1 = [I2C.Message([0x00, 0x00]), I2C.Message([0x00]*4000, read=True)]
		q2 = [I2C.Message([0x0f, 0xa0]), I2C.Message([0x00]*4000, read=True)]
		self.i2c.transfer(eeprom_address, q1)
		self.i2c.transfer(eeprom_address, q2)
		return np.array(q1[1].data + q2[1].data)

	def extract_eeprom_parameters(self, eeprom):
		#ThGrad
		ThGrad =   eeprom[0x0740:0x0F40:2] + (eeprom[0x0741:0x0F40:2] << 8)
		ThGrad = [tg - 65536 if tg >= 32768 else tg for tg in ThGrad]
		ThGrad = np.reshape(ThGrad, (32, 32))
		ThGrad[16:,:] = np.flipud(ThGrad[16:,:])
		self.ThGrad = ThGrad
		print(ThGrad)
		#ThOffset
		ThOffset = eeprom[0x0F40:0x1740:2] + (eeprom[0x0F41:0x1740:2] << 8)
		ThOffset = [to - 65536 if to >= 32768 else to for to in ThOffset]
		ThOffset = np.reshape(ThOffset, (32, 32))
		ThOffset[16:,:] = np.flipud(ThOffset[16:,:])
		self.ThOffset = ThOffset
		print(ThOffset)
		#P
		P =        eeprom[0x1740::2] + (eeprom[0x1741::2] << 8)
		P = np.reshape(P, (32, 32))
		P[16:, :] = np.flipud(P[16:,:])
		self.P = P
		#PixC
		epsilon = float(eeprom[0x000D])
		GlobalGain = eeprom[0x0055] + (eeprom[0x0056] << 8)
		Pmin = eeprom[0x0000:0x0004]
		Pmax = eeprom[0x0004:0x0008]
		Pmin = struct.unpack('f', reduce(lambda a,b: a+b, [chr(p) for p in Pmin]))[0]
		Pmax = struct.unpack('f', reduce(lambda a,b: a+b, [chr(p) for p in Pmax]))[0]
		self.PixC = (P * (Pmax - Pmin) / 65535. + Pmin) * (epsilon / 100) * float(GlobalGain) / 100 / 10000000
		self.gradScale = eeprom[0x0008]
		self.VddCalib = eeprom[0x0046] + (eeprom[0x0047] << 8)
		print(self.VddCalib)
		self.Vdd = 3280.0
		self.VddScaling = eeprom[0x004E]

		PTATgradient = eeprom[0x0034:0x0038]
		self.PTATgradient = struct.unpack('f', reduce(lambda a,b: a+b, [chr(p) for p in PTATgradient]))[0]
		PTAToffset = eeprom[0x0038:0x003c]
		self.PTAToffset = struct.unpack('f', reduce(lambda a,b: a+b, [chr(p) for p in PTAToffset]))[0]
		#Calib
		#self.MBITc = eeprom[0x001A]
		#self.BIASc = eeprom[0x001B]
		self.MBITc = 11
                self.BIASc = 11
		self.adc = self.MBITc +4
		self.CLKc  = eeprom[0x001C]
		self.BPAc  = eeprom[0x001D]
		self.PUc   = eeprom[0x001E]

		#vddCompensation
                self.VddComp = eeprom[0x0540:0x0740:2] + (eeprom[0x0541:0x0740:2] << 8)
                vddComp = np.zeros(1024)
		vddCompensation = np.zeros(1024)
		for block in range(0,4):
                	vddComp[0  + block*128  : 128  +  block*128] = self.VddComp[0:128]
                	vddComp[896- block*128  : 1024 -  block*128] = self.VddComp[128:256]

		delta =  self.Vdd - self.VddCalib/10
		vddCompensation = delta * vddComp / pow(2, self.VddScaling)
		self.vddCompensation = np.reshape(vddCompensation,(32,32))

	def temperature_compensation(self, im, ptat):
	    comp = np.zeros((32,32))
	    delta = self.Vdd - self.VddCalib/10
            self.ptat =  np.mean(ptat)
	    Ta = self.ptat * self.PTATgradient + self.PTAToffset

	    #ThermalOffset
	    thermalOffset = (self.ThGrad * Ta) / pow(2, self.gradScale)+ self.ThOffset
	    #temperature

	    Vcomp =  np.reshape(im,(32, 32)) - thermalOffset -  self.vddCompensation
	    return (Vcomp,Ta)
	def convert_image(self, im):
	 	return np.around(im).astype(int)

	def offset_compensation(self, im):
		return im - self.offset

	def sensitivity_compensation(self, im):
		return im/self.PixC

	def measure_observed_offset(self):
		print("Measuring observed offsets")
		print("    Camera should be against uniform temperature surface")
		mean_offset = np.zeros((32, 32))

		for i in range(10):
			print("    frame " + str(i))
			(p, pt) = self.capture_image()
			im = self.temperature_compensation(p, pt)
			mean_offset += im/10.0

		self.offset = mean_offset

	def measure_electrical_offset(self):
		(offset) = self.capture_offset(blind=True)
		self.offset = offset

	def capture_offset(self, blind=True):
		pixel_values = np.zeros(1024)
		block = 0
		self.send_command(self.generate_expose_block_command(block, blind=blind), wait=False)
		query = [I2C.Message([0x02]), I2C.Message([0x00], read=True)]
                expected = 1 + (block << 2)
                done = False
		while not done:
                	self.i2c.transfer(self.address, query)

                        if not (query[1].data[0] == expected):
                        	print("Not ready, received " + str(query[1].data[0]) + ", expected " + str(expected))
                                time.sleep(0.005)
                        else:
                                done = True

                read_block = [I2C.Message([0x0A]), I2C.Message([0x00]*258, read=True)]
                self.i2c.transfer(self.address, read_block)
                top_data = np.array(copy.copy(read_block[1].data))

                read_block = [I2C.Message([0x0B]), I2C.Message([0x00]*258, read=True)]
                self.i2c.transfer(self.address, read_block)
                bottom_data = np.array(copy.copy(read_block[1].data))

		top_data = top_data[1::2] + (top_data[0::2] << 8)
                bottom_data = bottom_data[1::2] + (bottom_data[0::2] << 8)

                for nbblock in range(0,4):
			pixel_values[(0+nbblock*128):(128+nbblock*128)] = top_data[1:]
                        # bottom data is in a weird shape
                        pixel_values[(992-nbblock*128):(1024-nbblock*128)] = bottom_data[1:33]
                        pixel_values[(960-nbblock*128):(992-nbblock*128)] = bottom_data[33:65]
                        pixel_values[(928-nbblock*128):(960-nbblock*128)] = bottom_data[65:97]
                        pixel_values[(896-nbblock*128):(928-nbblock*128)] = bottom_data[97:]

		pixel_values = np.reshape(pixel_values, (32, 32))
		print (pixel_values)
                return pixel_values


	def capture_image(self, blind=False):
		pixel_values = np.zeros(1024)
		ptats = np.zeros(8)

		for block in range(4):
			# print("Exposing block " + str(block))
			#if not (blind == False and block == 0):
			self.send_command(self.generate_expose_block_command(block, blind=blind), wait=False)

			query = [I2C.Message([0x02]), I2C.Message([0x00], read=True)]
			expected = 1 + (block << 2)

			done = False
			millis_start = int(round(time.time() * 1000))


			while not done:
				self.i2c.transfer(self.address, query)

				if not (query[1].data[0] == expected):
					#print("Not ready, received " + str(query[1].data[0]) + ", expected " + str(expected))
					time.sleep(0.002)
				else:
					done = True


			read_block = [I2C.Message([0x0A]), I2C.Message([0x00]*258, read=True)]
			self.i2c.transfer(self.address, read_block)
			top_data = np.array(copy.copy(read_block[1].data))

			read_block = [I2C.Message([0x0B]), I2C.Message([0x00]*258, read=True)]
			self.i2c.transfer(self.address, read_block)
			bottom_data = np.array(copy.copy(read_block[1].data))
			#millis_end = int(round(time.time() * 1000))
                        #print(millis_end - millis_start)
			#millis_start = int(round(time.time() * 1000))

			top_data = top_data[1::2] + (top_data[0::2] << 8)
			bottom_data = bottom_data[1::2] + (bottom_data[0::2] << 8)

			pixel_values[(0+block*128):(128+block*128)] = top_data[1:] << (16-self.adc)
			# bottom data is in a weird shape
			pixel_values[(992-block*128):(1024-block*128)] = bottom_data[1:33] << (16-self.adc)
			pixel_values[(960-block*128):(992-block*128)] = bottom_data[33:65] << (16-self.adc)
			pixel_values[(928-block*128):(960-block*128)] = bottom_data[65:97] << (16-self.adc)
			pixel_values[(896-block*128):(928-block*128)] = bottom_data[97:] << (16-self.adc)

			ptats[block] = top_data[0]
			ptats[7-block] = bottom_data[0]
			millis_end = int(round(time.time() * 1000))
                        #print("Time all process" + str(millis_end - millis_start))

		pixel_values = np.reshape(pixel_values, (32, 32))

		return (pixel_values, ptats)

	def generate_command(self, register, value):
		return [I2C.Message([register, value])]

	def generate_expose_block_command(self, block, blind=False):
		if blind:
			return self.generate_command(0x01, 0x09 + (block << self.blockshift) + 0x02)
		else:
			return self.generate_command(0x01, 0x09 + (block << self.blockshift))

	def send_command(self, cmd, wait=True):
		self.i2c.transfer(self.address, cmd)
		if wait:
			time.sleep(0.005) # sleep for 5 ms

	def close(self):
		sleep = self.generate_command(0x01, 0x00)
		self.send_command(sleep)



