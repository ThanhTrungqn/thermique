#!usr/bin/python

class Label:
        def __init__(self,label , size , left, right, top, bottom, sum, updated):
                self.id = label
                self.size = size
                self.left = left
                self.right = right
                self.top = top
                self.bottom = bottom
                self.sum = sum
		self.updated = updated


class Person:
	def __init__(self, label, posx, posy, size, change, firstTime, lastTime, firstX, firstY, readyUpdate , isPerson):
		self.label = label
		self.posX = posx
		self.posY = posy
		self.size = size
		self.change = change
		self.firstTime = firstTime
		self.lastTime = lastTime
		self.firstX = firstX
		self.firstY = firstY
		self.ready = readyUpdate
		self.isPerson = isPerson
		self.lastX = firstX
		self.lastY = firstY

def max(a, b):
	if (a >= b):
		return a
	else:
		return b

def min(a, b):
	if (a <=b):
		return a
	else:
		return b

class TRACKING:
	def __init__ (self):

		#Create list Configuration
		self.Config_Frame		= 10	#fps
		self.Config_Speed1 		= 5	#pixel
		self.Config_Speed2		= 8	#pixel
		self.Config_Speed3		= 10	#pixel
		self.Config_SizeMin		= 5	#pixel
		self.Config_SizeSeuil 		= 80	#pixel
		self.Config_TimeCount		= 1	#second
		self.Config_Delete_Object	= 1	#second
		self.Config_Delete_Person	= 1	#second
		self.Config_Bord_Y		= 12
		self.Config_Bord_X		= 15
		self.Config_Bord_Size		= 2

		#Variable for comptage
		self.person_in = 0
		self.person_out = 0
		#Create list Tracking
		self.tTracking = []
		self.nbTracking = 20
		self.init_list_tracking()
		self.idx = 0

	def init_list_tracking(self):
		for i in range (self.nbTracking):
			self.tTracking.append(Person(0,0,0,0,0,0,0,0,0,False,False))

	def show_text(self,listTracking):
		data=""
		for i in range(20):
			data+= 'index:'+str(i)
			data+= ' x:'+str(listTracking[i].posX)
			data+= ' y:' +str(listTracking[i].posY)
			data+= 'lastx:' +str(listTracking[i].lastX)
			data+= 'lasty:' +str(listTracking[i].lastY)
			data+= ' ready:' + str(listTracking[i].ready)
			data+= ' person:'+ str(listTracking[i].isPerson)
			data+= '\n'
		print(data)

	def check_object_near_label( self, Label, listTracking , radius):
		distance = 255
		id = -1
		for i in range (self.nbTracking):
			if ( self.tTracking[i].lastTime != self.idx and listTracking[i].ready ):
				diffx = (Label.left + Label.right)/2 - listTracking[i].posX
				diffy = (Label.top + Label.bottom)/2 - listTracking[i].posY
				if (diffx < 0):
					diffx = -diffx
				if (diffy < 0):
					diffy = -diffy
				if ( max(diffx, diffy) < distance):
					distance = max (diffx, diffy)
					id = i
		if (distance <= radius ):
			return id
		else:
			return -1

	def check_person_near_label( self, Label, listTracking, radius):
                distance = 255
                id = -1
                for i in range (self.nbTracking):
                        if ( self.tTracking[i].lastTime != self.idx and listTracking[i].isPerson ):
                                diffx = (Label.left + Label.right)/2 - listTracking[i].posX
                                diffy = (Label.top + Label.bottom)/2 - listTracking[i].posY
                                if (diffx < 0):
                                        diffx = -diffx
                                if (diffy < 0):
                                        diffy = -diffy
                                if ( max(diffx, diffy) < distance):
                                        distance = max (diffx, diffy)
                                        id = i
                if (distance < radius ):
                        return id
                else:
                        return -1


	def check_all_near_label(self, Label, listTracking, radius):
		id = -1
		listId=[]
                for i in range (self.nbTracking):
                        if ( listTracking[i].lastTime != self.idx and listTracking[i].ready and listTracking[i].isPerson):
                                diffx = (Label.left + Label.right)/2 - listTracking[i].posX
                                diffy = (Label.top + Label.bottom)/2 - listTracking[i].posY
                                if (diffx < 0):
                                        diffx = -diffx
                                if (diffy < 0):
                                        diffy = -diffy
                                if ( max(diffx, diffy) <= radius):
                                        listId.append(i)
                return listId


	def update_person(self, id , label, newPerson):
		x = (label.left + label.right)/2
                y = (label.top + label.bottom )/2
		print(label.top)
		print(label.bottom)
		self.tTracking[id].posX = x
                self.tTracking[id].posY = y
		self.tTracking[id].size = label.size
		#self.tTracking[id].change = self.
		self.tTracking[id].lastTime = self.idx
		self.tTracking[id].ready = True

		if (newPerson) :
			self.tTracking[id].firstX = x
			self.tTracking[id].firstY = y
			self.tTracking[id].lastX = x
			self.tTracking[id].lastY = y
			self.tTracking[id].firstTime = self.idx

	def update_label(self, listLabel, id):
		listLabel[id].updated = True

	def find_id_disponible (self, listTracking):
		lengthTracking = len(listTracking)
		id_out=-1
		for i in range (lengthTracking):
			if (listTracking[i].ready == False ):
				id_out = i
				break

		return id_out

	def remove_old_person(self, listTracking):
		lengthTracking = len(listTracking)
		for i in range(lengthTracking):
			if (listTracking[i].ready):
				time = self.idx - listTracking[i].lastTime
				if  (time > (self.Config_Delete_Object * self.Config_Frame)):
					#Delete here
					listTracking[i].ready = False
					listTracking[i].isPerson = False

	def decide_person(self, listTracking):
		lengthTracking = len(listTracking)
		for i in range(lengthTracking):
			if (listTracking[i].isPerson == False and listTracking[i].lastTime == self.idx ):
				time = listTracking[i].lastTime - listTracking[i].firstTime
				if (time > self.Config_TimeCount):
					listTracking[i].isPerson = True

		count = 0
		for i in range(lengthTracking):
			if (listTracking[i].isPerson):
				count +=1

		return count

	def check_in_zone(self, x, y, x1, y1, h, w):
		if  (x > x1 and x < (x1 + w) and y > y1 and y < (y1+h)):
			return True
		return False

	def people_comptage(self, listTracking):
		lengthTracking = len( listTracking)
		for i  in range(lengthTracking):
			if (listTracking[i].isPerson):
				if ( self.check_in_zone(listTracking[i].lastX,listTracking[i].lastY,10,0,8,22) == True and self.check_in_zone(listTracking[i].posX,listTracking[i].posY,8,0,10,24) == False):
					self.person_in += 1
					listTracking[i].lastX = listTracking[i].posX
					listTracking[i].lastY = listTracking[i].posY
				if ( self.check_in_zone(listTracking[i].posX,listTracking[i].posY,10,0,8,22) == True and self.check_in_zone(listTracking[i].lastX,listTracking[i].lastY,8,0,10,24) == False ):
					self.person_out += 1
					listTracking[i].lastX = listTracking[i].posX
					listTracking[i].lastY = listTracking[i].posY

	def labelTracking(self, listLabel , listTracking , idx):

		self.idx = idx
		lengthTracking = len(listTracking)
		lengthLabel = len(listLabel)

		for i in range(lengthLabel):	#Loop for 1 person near
			if (listLabel[i].updated == False):
				if (listLabel[i].size > self.Config_SizeMin and listLabel[i].size < self.Config_SizeSeuil):
					id = self.check_person_near_label(listLabel[i] , listTracking , self.Config_Speed1)
					if ( id >= 0 ):
						#Update here
						newPerson = False
						self.update_person(id , listLabel[i], newPerson)
						self.update_label(listLabel, i)
						print("Update 1")
					else:
						id = self.check_object_near_label(listLabel[i] , listTracking, self.Config_Speed1)
						if ( id >= 0):
							#Update here
							newPerson = False
							self.update_person(id, listLabel[i], newPerson)
							self.update_label(listLabel, i)
							print("Update 2")

		for i in range(lengthLabel):    #Loop for 1 person distance
                        if (listLabel[i].updated == False):
                                if (listLabel[i].size > self.Config_SizeMin and listLabel[i].size < self.Config_SizeSeuil):
                                        id = self.check_person_near_label(listLabel[i] , listTracking , self.Config_Speed2)
                                        if ( id >= 0 ):
						#Update here
                                                newPerson = False
                                                self.update_person(id , listLabel[i], newPerson)
                                                self.update_label(listLabel, i)
						print("Update 3")
                                        else:
                                                id = self.check_object_near_label(listLabel[i] , listTracking, self.Config_Speed2)
                                                if ( id >= 0):
                                                        #Update here
                                                	newPerson = False
                                                	self.update_person(id , listLabel[i], newPerson)
                                                	self.update_label(listLabel, i)
							print("Update 4")

						else:
							#Create new
                                                        newPerson = True
							id_person = self.find_id_disponible(listTracking)
                                                        self.update_person(id_person , listLabel[i], newPerson)
                                                        self.update_label(listLabel, i)
							print("Create NEw")


		for i in range(lengthLabel):	#Loop for 2 person
			if (listLabel[i].updated == False):
				if (listLabel[i].size >= self.Config_SizeSeuil):
					listId = self.check_all_near_label( listLabel[i], listTracking , self.Config_Speed3 )
					print(listId)
					if (len(listId) == 0):
						#Create new
						newPerson = True
                                                id_person = self.find_id_disponible(listTracking)
                                                self.update_person(id_person , listLabel[i], newPerson)
                                                self.update_label(listLabel, i)
						print("Create new")

					else:
						#Update
						for j in range(len(listId)):
							#Update here
                                                        newPerson = False
							id = listId[j]
                                                        self.update_person(id , listLabel[i], newPerson)
                                                        self.update_label(listLabel, i)
							print("Update 5")

		self.remove_old_person( listTracking)
		result = self.decide_person( listTracking)
		self.people_comptage (listTracking)
		#self.show_text(listTracking)
		person_in = self.person_in
		person_out = self.person_out
		#print(person_in)
		#print(person_out)
		return (result,person_in,person_out)
