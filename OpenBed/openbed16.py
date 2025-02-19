from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5 import uic
from pyqtgraph import PlotWidget, plot
from skin_module import AD7171, SkinSensor
from datetime import datetime
import sys, subprocess, time
import RPi.GPIO as GPIO
import pyqtgraph as pg
import redis

weightDb = redis.Redis(host='127.0.0.1', port=6379, db=0)
class WARNING(QtWidgets.QMainWindow):
	def __init__(self):
		QtWidgets.QMainWindow.__init__(self)
		self.uiWarning = uic.loadUi('warning16.ui', self)
		self.pushButton.clicked.connect(self.okButton)
	
	def okButton(self):
		self.uiWarning.close()

class SET_DATE_TIME(QtWidgets.QMainWindow):
	def __init__(self):
		QtWidgets.QMainWindow.__init__(self)
		self.uiDateTime = uic.loadUi('setDateTime16.ui', self)
		self.warningWindow = 0
		try:
			serialFile = open('/boot/serial.txt', 'r')
			serialNo = serialFile.read(3)
			if(len(serialNo) != 3):
				serialNo = "000"
			try:
				int(serialNo)
			except:
				serialNo = "000"
			serialFile.close()
		except:
			serialNo = "000"
			
		self.label_9.setText("AYT-1001-" + serialNo)
		
		self.setHour = 0
		self.setMin = 0
		self.setDay = 1
		self.setMonth = 1
		self.setYear = 2023
		
		self.lcdNumber.display("00")
		self.lcdNumber_2.display("00")
		self.lcdNumber_3.display("01")
		self.lcdNumber_4.display("01")
		self.lcdNumber_5.display("2023")
		
		langFile = open("lang.txt", "r")
		lang =langFile.read()
		langFile.close()
		
		self.enPixmap = QtGui.QPixmap("/home/eomedical/images/united-kingdom.png")
		self.ruPixmap = QtGui.QPixmap("/home/eomedical/images/russia.png")
		self.trPixmap = QtGui.QPixmap("/home/eomedical/images/turkey.png")
		
		if(lang == "en"):
			self.currentLanguage = 0 # English
			self.label_16.setPixmap(self.enPixmap)
			self.label_17.setText("English")
			
		elif(lang == "ru"):
			self.currentLanguage = 1 # Russian
			self.label_16.setPixmap(self.ruPixmap)
			self.label_17.setText("Русский")
			
		elif(lang == "tr"):
			self.currentLanguage = 2 # Turkish
			self.label_16.setPixmap(self.trPixmap)
			self.label_17.setText("Türkçe")
		
		else:
			# If lang.txt file wrong, fix it and set default English
			self.currentLanguage = 0  # English
			self.label_16.setPixmap(self.enPixmap)
			self.label_17.setText("English")
			langFile = open("lang.txt", "w")
			langFile.write("en")
			langFile.close()

		self.pushButton.clicked.connect(self.upHour)
		self.pushButton_2.clicked.connect(self.downHour)
		self.pushButton_3.clicked.connect(self.upMin)
		self.pushButton_4.clicked.connect(self.downMin)
		self.pushButton_5.clicked.connect(self.upDay)
		self.pushButton_6.clicked.connect(self.downDay)
		self.pushButton_7.clicked.connect(self.upMonth)
		self.pushButton_8.clicked.connect(self.downMonth)
		self.pushButton_9.clicked.connect(self.upYear)
		self.pushButton_10.clicked.connect(self.downYear)
		self.pushButton_11.clicked.connect(self.setDateTimeValue)
		self.pushButton_12.clicked.connect(self.closeWindow)
		self.pushButton_13.clicked.connect(self.calib0)
		self.pushButton_14.clicked.connect(self.calib5)
		self.pushButton_15.clicked.connect(self.tare)
		self.pushButton_16.clicked.connect(self.langLeft)
		self.pushButton_17.clicked.connect(self.langRight)
		
		self.cntDisableSet = 0
		self.timerDisableSet = QtCore.QTimer()
		self.timerDisableSet.setInterval(2000)
		self.timerDisableSet.timeout.connect(self.disableSet)
		
		self.scaleIsActive = False		# False : not connected / True : is connected
		self.weight1raw = 0
		self.weight2raw = 0
		
		self.timerCheckScale = QtCore.QTimer()
		self.timerCheckScale.setInterval(100)
		self.timerCheckScale.timeout.connect(self.checkScale)
		self.timerCheckScale.start()
		
		self.cntCalib0 = 0
		self.weight1calib0 = 0
		self.weight2calib0 = 0
		self.timerCalib0 = QtCore.QTimer()
		self.timerCalib0.setInterval(1000)
		self.timerCalib0.timeout.connect(self.calibFunction0)
		
		self.cntCalib5 = 0
		self.weight1calib5 = 0
		self.weight2calib5 = 0
		self.timerCalib5 = QtCore.QTimer()
		self.timerCalib5.setInterval(1000)
		self.timerCalib5.timeout.connect(self.calibFunction5)
		
		f = open("tare.txt", 'r')
		tareData = f.read().split(";")
		f.close()
		self.cntTare = 0
		self.tare1 = float(tareData[0])
		self.tare2 = float(tareData[1])
		self.tare1sum = 0
		self.tare2sum = 0
		self.timerTare = QtCore.QTimer()
		self.timerTare.setInterval(1000)
		self.timerTare.timeout.connect(self.tareFunction)
		
		self.calib0data = [0, 0]
		self.calib5data = [0, 0]
				
		self.cntClear = 0
		self.timerClearLabel = QtCore.QTimer()
		self.timerClearLabel.setInterval(2000)
		self.timerClearLabel.timeout.connect(self.clearLabel)
		
		self.cntWeight = 0
		self.weight1sum = 0
		self.weight2sum = 0
		self.weightCurrent = 0
		self.weight = 0
		self.timerCalculateWeight = QtCore.QTimer()
		self.timerCalculateWeight.setInterval(1000)
		self.timerCalculateWeight.timeout.connect(self.calculateWeight)
		self.timerCalculateWeight.start()
		
	def upHour(self):
		self.setHour += 1
		if(self.setHour > 23):
			self.setHour = 0
		
		if(self.setHour<10):
			setHourText = "0" + str(self.setHour)
		else:
			setHourText = str(self.setHour)
			
		self.lcdNumber.display(setHourText)
		
	def downHour(self):
		self.setHour -= 1
		if(self.setHour < 0):
			self.setHour = 23
			
		if(self.setHour<10):
			setHourText = "0" + str(self.setHour)
		else:
			setHourText = str(self.setHour)
			
		self.lcdNumber.display(setHourText)
		
	def upMin(self):
		self.setMin += 1
		if(self.setMin > 59):
			self.setMin = 0
		
		if(self.setMin<10):
			setMinText = "0" + str(self.setMin)
		else:
			setMinText = str(self.setMin)
			
		self.lcdNumber_2.display(setMinText)
		
	def downMin(self):
		self.setMin -= 1
		if(self.setMin < 0):
			self.setMin = 59
			
		if(self.setMin<10):
			setMinText = "0" + str(self.setMin)
		else:
			setMinText = str(self.setMin)
			
		self.lcdNumber_2.display(setMinText)
		
	def upDay(self):
		self.setDay += 1
		if(self.setDay > 31):
			self.setDay = 1
		
		if(self.setDay<10):
			setDayText = "0" + str(self.setDay)
		else:
			setDayText = str(self.setDay)
			
		self.lcdNumber_3.display(setDayText)
		
	def downDay(self):
		self.setDay -= 1
		if(self.setDay < 1):
			self.setDay = 31
			
		if(self.setDay<10):
			setDayText = "0" + str(self.setDay)
		else:
			setDayText = str(self.setDay)
			
		self.lcdNumber_3.display(setDayText)
		
	def upMonth(self):
		self.setMonth += 1
		if(self.setMonth > 12):
			self.setMonth = 1
		
		if(self.setMonth < 10):
			setMonthText = "0" + str(self.setMonth)
		else:
			setMonthText = str(self.setMonth)
			
		self.lcdNumber_4.display(setMonthText)
		
	def downMonth(self):
		self.setMonth -= 1
		if(self.setMonth < 1):
			self.setMonth = 12
			
		if(self.setMonth<10):
			setMonthText = "0" + str(self.setMonth)
		else:
			setMonthText = str(self.setMonth)
			
		self.lcdNumber_4.display(setMonthText)
		
	def upYear(self):
		self.setYear += 1
		if(self.setYear > 9999):
			self.setYear = 2023
			
		setYearText = str(self.setYear)
			
		self.lcdNumber_5.display(setYearText)
		
	def downYear(self):
		self.setYear -= 1
		if(self.setYear < 2023):
			self.setYear = 2023
			
		setYearText = str(self.setYear)
						
		self.lcdNumber_5.display(setYearText)
		
		
	def setDateTimeValue(self):
		self.cntDisableSet = 0
		self.pushButton_11.setEnabled(False)
		self.timerDisableSet.start()
		
	
	def disableSet(self):
		if(self.setMonth<10):
			hwclockText = "\"0" + str(self.setMonth) + "/"
		else:
			hwclockText = "\"" + str(self.setMonth) + "/"
		if(self.setDay<10):
			hwclockText = hwclockText + "0" + str(self.setDay) + "/"
		else:
			hwclockText = hwclockText + str(self.setDay) + "/"
		
		hwclockText = hwclockText + str(self.setYear) + " "
		
		if(self.setHour < 10):
			hwclockText = hwclockText + "0" + str(self.setHour) + ":"
		else:
			hwclockText = hwclockText + str(self.setHour) + ":"
		if(self.setMin<10):
			hwclockText = hwclockText + "0" + str(self.setMin) + ":00\""
		else:
			hwclockText = hwclockText + str(self.setMin) + ":00\""

		hwclockText = "sudo hwclock --set --date " + hwclockText 
		print(hwclockText)
		
		outputData = subprocess.getoutput(hwclockText)
		if(outputData == ''):
			if(self.currentLanguage == 0):
				self.label_10.setText("Successful")
			elif(self.currentLanguage == 1):
				self.label_10.setText("Успешно")
			elif(self.currentLanguage == 2):
				self.label_10.setText("Başarılı")
				
		else:
			if(self.currentLanguage == 0 ):
				self.label_10.setText("Failed")
			elif(self.currentLanguage == 1):
				self.label_10.setText("Неудачно")
			elif(self.currentLanguage == 2):
				self.label_10.setText("Başarısız")
				
		self.timerClearLabel.start()
		outputData = subprocess.getoutput("sudo hwclock -s")
		self.pushButton_11.setEnabled(True)
		self.timerDisableSet.stop()
		
	def langLeft(self):
		self.currentLanguage = (self.currentLanguage - 1)%3
		if(self.currentLanguage == 0):
			self.label_16.setPixmap(self.enPixmap)
			self.label_17.setText("English")
			
		elif(self.currentLanguage == 1):
			self.label_16.setPixmap(self.ruPixmap)
			self.label_17.setText("Русский")
			
		elif(self.currentLanguage == 2):
			self.label_16.setPixmap(self.trPixmap)
			self.label_17.setText("Türkçe")
		
	def langRight(self):
		self.currentLanguage = (self.currentLanguage + 1)%3
		if(self.currentLanguage == 0):
			self.label_16.setPixmap(self.enPixmap)
			self.label_17.setText("English")
			
		elif(self.currentLanguage == 1):
			self.label_16.setPixmap(self.ruPixmap)
			self.label_17.setText("Русский")
			
		elif(self.currentLanguage == 2):
			self.label_16.setPixmap(self.trPixmap)
			self.label_17.setText("Türkçe")
			
	def checkScale(self):
		self.weight1raw = float(weightDb.get("weight1raw"))
		self.weight2raw = float(weightDb.get("weight2raw"))
		if(self.weight1raw==0 and self.weight2raw==0):
			self.scaleIsActive = False
			self.pushButton_13.setEnabled(False)
			self.pushButton_14.setEnabled(False)
			self.pushButton_15.setEnabled(False)
		else:
			self.scaleIsActive = True
			if(self.timerCalib0.isActive() or self.timerCalib5.isActive() or self.timerTare.isActive()):
				self.pushButton_13.setEnabled(False)
				self.pushButton_14.setEnabled(False)
				self.pushButton_15.setEnabled(False)
			else:
				self.pushButton_13.setEnabled(True)
				self.pushButton_14.setEnabled(True)
				self.pushButton_15.setEnabled(True)			
			
	def calib0(self):
		rollValue = round(float(weightDb.get("roll")))
		if((rollValue < -1) or (rollValue > 1)):
			if(self.warningWindow == 0):
				self.warningWindow = WARNING()
			else:
				self.warningWindow.show()
			self.warningWindow.setWindowFlags(QtCore.Qt.FramelessWindowHint)
			self.warningWindow.setGeometry(50,580, 500, 200)
			if(self.currentLanguage == 0):
				messageText = "Please make sure that the\nTrendelenburg angle is 0 degrees."
			elif(self.currentLanguage == 1):
				messageText = "Убедитесь, что угол\nТренделенбурга равен 0 градусов."
			elif(self.currentLanguage == 2):
				messageText = "Lütfen Trendelenburg açısının\n0 derece olduğundan emin olunuz."
			self.warningWindow.label_2.setText(messageText)
			self.warningWindow.show()
		else:
			self.timerCalib0.start()
			self.cntCalib0 = 0
			self.weight1calib0 = 0
			self.weight2calib0 = 0
		
	def calib5(self):
		rollValue = round(float(weightDb.get("roll")))
		if((rollValue < -1) or (rollValue > 1)):
			if(self.warningWindow == 0):
				self.warningWindow = WARNING()
			else:
				self.warningWindow.show()
			self.warningWindow.setWindowFlags(QtCore.Qt.FramelessWindowHint)
			self.warningWindow.setGeometry(50,580, 500, 200)
			if(self.currentLanguage == 0):
				messageText = "Please make sure that the\nTrendelenburg angle is 0 degrees."
			elif(self.currentLanguage == 1):
				messageText = "Убедитесь, что угол\nТренделенбурга равен 0 градусов."
			elif(self.currentLanguage == 2):
				messageText = "Lütfen Trendelenburg açısının\n0 derece olduğundan emin olunuz."
			self.warningWindow.label_2.setText(messageText)
			self.warningWindow.show()
		else:
			self.timerCalib5.start()
			self.cntCalib5 = 0
			self.weight1calib5 = 0
			self.weight2calib5 = 0
		
	def tare(self):
		rollValue = round(float(weightDb.get("roll")))
		if((rollValue < -1) or (rollValue > 1)):
			if(self.warningWindow == 0):
				self.warningWindow = WARNING()
			else:
				self.warningWindow.show()
			self.warningWindow.setWindowFlags(QtCore.Qt.FramelessWindowHint)
			self.warningWindow.setGeometry(50,580, 500, 200)
			if(self.currentLanguage == 0):
				messageText = "Please make sure that the\nTrendelenburg angle is 0 degrees."
			elif(self.currentLanguage == 1):
				messageText = "Убедитесь, что угол\nТренделенбурга равен 0 градусов."
			elif(self.currentLanguage == 2):
				messageText = "Lütfen Trendelenburg açısının\n0 derece olduğundan emin olunuz."
			self.warningWindow.label_2.setText(messageText)
			self.warningWindow.show()
		else:
			self.timerTare.start()
			self.tare1sum = 0
			self.tare2sum = 0
			self.cntTare = 0
		
	def calibFunction0(self):
		if(self.scaleIsActive):
			if(self.weight1raw>1000000 and self.weight1raw<1400000 and self.weight2raw>1000000 and self.weight2raw<1400000):
				self.weight1calib0 = self.weight1calib0 + self.weight1raw
				self.weight2calib0 = self.weight2calib0 + self.weight2raw
				self.cntCalib0 += 1
				
				if(self.currentLanguage == 0 ):
					messageText = "Calibrating, please wait"
				elif(self.currentLanguage == 1):
					messageText = "Выполняется калибровка, подождите"
				elif(self.currentLanguage == 2):
					messageText = "Kalibre ediliyor, lütfen bekleyiniz"
					
				if(self.cntCalib0%3 == 0):
					messageText = messageText + "..."
				if(self.cntCalib0%3 == 1):
					messageText = messageText + ".  "
				if(self.cntCalib0%3 == 2):
					messageText = messageText + ".. "
				self.label_14.setText(messageText)
				if(self.cntCalib0 == 6):
					self.weight1calib0 = self.weight1calib0/6
					self.weight2calib0 = self.weight2calib0/6
					self.timerCalib0.stop()
					self.calib0data = [self.weight1calib0, self.weight2calib0]
					f = open("calib0.txt", 'w')
					f.write(str(self.weight1calib0) + "; " + str(self.weight2calib0))
					f.close()
					if(self.currentLanguage == 0):
						messageText = "0 kg calibration successful"
					elif(self.currentLanguage == 1):
						messageText = "Калибровка 0 кг успешна"
					elif(self.currentLanguage == 2):
						messageText = "0 kg kalibrasyonu başarılı"
						
					self.label_14.setText(messageText)
					self.tare1 = 0
					self.tare2 = 0
					self.timerClearLabel.start()
					return self.calib0data
			else:
				self.weight1calib0 = 0
				self.weight2calib0 = 0
				self.calib0data = [0, 0]
				self.timerCalib0.stop()
				if(self.currentLanguage == 0):
					messageText = "0 kg calibration failed"
				elif(self.currentLanguage == 1):
					messageText = "Калибровка 0 кг неудачна"
				elif(self.currentLanguage == 2):
					messageText = "0 kg kalibrasyonu başarısız"					
				self.label_14.setText(messageText)
				self.timerClearLabel.start()
				return self.calib0data
		else:
			self.weight1calib0 = 0
			self.weight2calib0 = 0
			self.calib0data = [0, 0]
			self.timerCalib0.stop()
			if(self.currentLanguage == 0):
				messageText = "0 kg calibration failed"
			elif(self.currentLanguage == 1):
				messageText = "Калибровка 0 кг неудачна"
			elif(self.currentLanguage == 2):
				messageText = "0 kg kalibrasyonu başarısız"
			self.label_14.setText(messageText)
			self.timerClearLabel.start()
			return self.calib0data
			
	def calibFunction5(self):
		if(self.scaleIsActive):
			if(self.weight1raw>2000000 and self.weight1raw<2400000 and self.weight2raw>2000000 and self.weight2raw<2400000):
				self.weight1calib5 = self.weight1calib5 + self.weight1raw
				self.weight2calib5 = self.weight2calib5 + self.weight2raw
				self.cntCalib5 += 1
				if(self.currentLanguage == 0):
					messageText = "Calibrating, please wait"
				elif(self.currentLanguage == 1):
					messageText = "Выполняется калибровка, подождите"
				elif(self.currentLanguage == 2):
					messageText = "Kalibre ediliyor, lütfen bekleyiniz"
					
				if(self.cntCalib5%3 == 0):
					messageText = messageText + "..."
				if(self.cntCalib5%3 == 1):
					messageText = messageText + ".  "
				if(self.cntCalib5%3 == 2):
					messageText = messageText + ".. "
				self.label_14.setText(messageText)
				if(self.cntCalib5 == 6):
					self.weight1calib5 = self.weight1calib5/6
					self.weight2calib5 = self.weight2calib5/6
					self.timerCalib5.stop()
					self.calib5data = [self.weight1calib5, self.weight2calib5]
					f = open("calib5.txt", 'w')
					f.write(str(self.weight1calib5) + "; " + str(self.weight2calib5))
					f.close()
					if(self.currentLanguage == 0):
						messageText = "5 kg calibration successful"
					elif(self.currentLanguage == 1):
						messageText = "Калибровка 5 кг успешна"
					elif(self.currentLanguage == 2):
						messageText = "5 kg kalibrasyonu başarılı"
						
					self.label_14.setText(messageText)
					self.tare1 = 0
					self.tare2 = 0
					self.timerClearLabel.start()
					return self.calib5data
			else:
				self.weight1calib5 = 0
				self.weight2calib5 = 0
				self.calib5data = [0, 0]
				self.timerCalib5.stop()
				if(self.currentLanguage == 0):
					messageText = "5 kg calibration failed"
				elif(self.currentLanguage == 1):
					messageText = "Калибровка 5 кг неудачна"
				elif(self.currentLanguage == 2):
					messageText = "5 kg kalibrasyonu başarısız"
					
				self.label_14.setText(messageText)
				self.timerClearLabel.start()
				return self.calib5data
		else:
			self.weight1calib5 = 0
			self.weight2calib5 = 0
			self.calib5data = [0, 0]
			self.timerCalib5.stop()
			if(self.currentLanguage == 0):
				messageText = "5 kg calibration failed"
			elif(self.currentLanguage == 1):
				messageText = "Калибровка 5 кг неудачна"
			elif(self.currentLanguage == 2):
				messageText = "5 kg kalibrasyonu başarısız"
				
			self.label_14.setText(messageText)
			self.timerClearLabel.start()
			return self.calib5data
		
			
	def tareFunction(self):
		if(self.scaleIsActive):
			if(self.weight1raw>1000000 and self.weight1raw<1600000 and self.weight2raw>1000000 and self.weight2raw<1600000):
				self.tare1sum = self.tare1sum + self.weight1raw
				self.tare2sum = self.tare2sum + self.weight2raw
				self.cntTare += 1
				if(self.currentLanguage == 0):
					messageText = "Taring, please wait"
				elif(self.currentLanguage == 1):
					messageText = "Выполняется тарирование, подождите"
				elif(self.currentLanguage == 2):
					messageText = "Dara alınıyor, lütfen bekleyiniz"
					
				if(self.cntTare%3 == 0):
					messageText = messageText + "..."
				if(self.cntTare%3 == 1):
					messageText = messageText + ".  "
				if(self.cntTare%3 == 2):
					messageText = messageText + ".. "
				self.label_14.setText(messageText)
				if(self.cntTare == 6):
					self.timerTare.stop()
					f = open("calib0.txt", 'r')
					calib0data = f.read().split(";")
					f.close()
					weight1calib0 = float(calib0data[0])
					weight2calib0 = float(calib0data[1])
					self.tare1 = (self.tare1sum/6) - weight1calib0
					self.tare2 = (self.tare2sum/6) - weight2calib0
					f = open("tare.txt", 'w')
					f.write(str(self.tare1) + "; " + str(self.tare2))
					f.close()
					if(self.currentLanguage == 0):
						self.label_14.setText("Taring successful")
					elif(self.currentLanguage == 1):
						self.label_14.setText("Тарирование успешно")
					elif(self.currentLanguage == 2):
						self.label_14.setText("Dara alma başarılı")
						
					self.timerClearLabel.start()
			else:
				self.timerTare.stop()
				if(self.currentLanguage == 0):
					self.label_14.setText("Taring failed")
				elif(self.currentLanguage == 1):
					self.label_14.setText("Тарирование неудачно")
				elif(self.currentLanguage == 2):
					self.label_14.setText("Dara alma başarısız")
				self.timerClearLabel.start()
		else:
			self.timerTare.stop() 
			if(self.currentLanguage == 0):
				self.label_14.setText("Taring failed")
			elif(self.currentLanguage == 1):
				self.label_14.setText("Тарирование неудачно")
			elif(self.currentLanguage == 2):
				self.label_14.setText("Dara alma başarısız")
			self.timerClearLabel.start()
				
	def clearLabel(self):
		self.cntClear += 1
		if(self.cntClear>1):
			self.label_14.setText("")
			self.label_10.setText("")
			self.cntClear = 0
			self.timerClearLabel.stop()
			
	def calculateWeight(self):
		self.weight1sum = self.weight1sum + self.weight1raw - self.tare1
		self.weight2sum = self.weight2sum + self.weight2raw - self.tare2
		self.cntWeight += 1
		if(self.cntWeight == 1):
			f = open("calib0.txt", 'r')
			calib0data = f.read().split(";")
			f.close()
			f = open("calib5.txt", 'r')
			calib5data = f.read().split(";")
			f.close()
			weight1calib0 = float(calib0data[0])
			weight2calib0 = float(calib0data[1])
			weight1calib5 = float(calib5data[0])
			weight2calib5 = float(calib5data[1])
			percent1raw = (weight1calib5 - weight1calib0)/5000
			percent2raw = (weight2calib5 - weight2calib0)/5000
			weight1 = ((self.weight1sum/1) - weight1calib0) / percent1raw
			weight2 = ((self.weight2sum/1) - weight2calib0) / percent2raw
			self.weightCurrent = round((weight1 + weight2) / 2)
			self.weight = self.weightCurrent
			if(self.weight<0):
				self.weight = 0
			self.cntWeight = 0
			self.weight1sum = 0
			self.weight2sum = 0
			
	def closeWindow(self):
		self.label_10.setText("")
		mainWindow.showFullScreen()
		self.close()


class OPENBED_APP(QtWidgets.QMainWindow):
	def __init__(self):
		QtWidgets.QMainWindow.__init__(self)
		self.ui = uic.loadUi('openbed16.ui', self)
		
		self.dateTimeWindow = SET_DATE_TIME()
		
		self.heaterPin = 12
		self.lamp1Pin = 23
		self.lamp2Pin = 24
		self.buzzerPin = 25
		self.alarmLedPin = 6
		self.powerStatusPin = 26
		
		self.skinValidFlag = 0
		self.skinTempData = 0
		self.servoSet = 36.0
		
		
		self.heaterStatus = False
		self.lamp1Status = False
		self.lamp2Status = False
		self.buzzerStatus = True
		self.alarmLedStatus = False
		
		GPIO.setwarnings(False)
		
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.heaterPin, GPIO.OUT)
		GPIO.setup(self.lamp1Pin, GPIO.OUT)
		GPIO.setup(self.lamp2Pin, GPIO.OUT)
		GPIO.setup(self.buzzerPin, GPIO.OUT)
		GPIO.setup(self.alarmLedPin, GPIO.OUT)
		GPIO.setup(self.powerStatusPin, GPIO.IN)
		
		GPIO.output(self.heaterPin, self.heaterStatus)
		GPIO.output(self.lamp1Pin, self.lamp1Status)
		GPIO.output(self.lamp2Pin, self.lamp2Status)
		GPIO.output(self.buzzerPin, self.buzzerStatus)
		GPIO.output(self.alarmLedPin, self.alarmLedStatus)
		self.powerStatus = GPIO.input(self.powerStatusPin)
		
		time.sleep(0.25)
		GPIO.output(self.buzzerPin, False)
		
		self.batteryVoltage = 0
		self.lightingIcon = QtGui.QIcon("/home/eomedical/images/battery-lighting.png")
		self.fullBatteryIcon = QtGui.QIcon("/home/eomedical/images/battery-full.png")
		self.halfBatteryIcon = QtGui.QIcon("/home/eomedical/images/battery-half.png")
		self.lowBatteryIcon = QtGui.QIcon("/home/eomedical/images/battery-low.png")
		self.pushButton_13.setIconSize(QtCore.QSize(60, 60))
		
			
		
		self.heaterMode = 0 		#0:Prewarm 1:Manual 2:Skin
		self.heaterPWM = GPIO.PWM(self.heaterPin, 1)	#1 Hz
		self.heaterPWM.start(0)
		self.pwmValue = 0
				
		self.enable37Flag = 0
		
		self.timerModeValue = 0		# Apgar
		self.timerMinutes = 0
		self.timerSeconds = 0
		self.timerSetValue = 0
		self.timerText = "00:00"
		self.lcdNumber.display(self.timerText)
		self.pushButton_9.setVisible(False)
		self.pushButton_10.setVisible(False)
		self.pushButton_11.setVisible(False)
		self.timerTimer = QtCore.QTimer()
		self.timerTimer.setInterval(1000)
		self.timerTimer.timeout.connect(self.timerCalculator)
		
		self.buzzerCounter = 0
		self.timerBuzzerShort = QtCore.QTimer()
		self.timerBuzzerShort.setInterval(100)
		self.timerBuzzerShort.timeout.connect(self.buzzerShort)
		self.timerBuzzerLong = QtCore.QTimer()
		self.timerBuzzerLong.setInterval(100)
		self.timerBuzzerLong.timeout.connect(self.buzzerLong)
		
		self.keylockValue = 0 	# Unlocked
		self.sliderCounter = 0
		self.horizontalSlider.setValue(self.keylockValue)
		self.unlockPixmap = QtGui.QPixmap("/home/eomedical/images/unlock_rev1.png")
		self.lockPixmap = QtGui.QPixmap("/home/eomedical/images/lock_rev1.png")
		self.label_9.setPixmap(self.unlockPixmap)
		
		self.pushButton.clicked.connect(self.heatUp)
		self.pushButton_2.clicked.connect(self.heatDown)
		self.pushButton_3.clicked.connect(self.heaterControl)
		self.pushButton_4.clicked.connect(self.setSkinUp)
		self.pushButton_5.clicked.connect(self.setSkinDown)
		self.pushButton_6.clicked.connect(self.enable37)
		self.pushButton_7.clicked.connect(self.timerUp)
		self.pushButton_8.clicked.connect(self.timerDown)
		self.pushButton_9.clicked.connect(self.timerStart)
		self.pushButton_10.clicked.connect(self.timerPause)
		self.pushButton_11.clicked.connect(self.timerStop)
		self.pushButton_12.clicked.connect(self.timerMode)
		self.pushButton_13.clicked.connect(self.powerStatusCheck)
		self.pushButton_14.clicked.connect(self.settings)
		self.pushButton_16.clicked.connect(self.muteAlarmFunction)
		self.pushButton_17.clicked.connect(self.trendInterval)
		self.pushButton_18.clicked.connect(self.zoomIn)
		self.pushButton_19.clicked.connect(self.trendChange)
		self.radioButton_2.clicked.connect(self.lamp1Control)
		self.radioButton_3.clicked.connect(self.lamp2Control)
		self.horizontalSlider.sliderReleased.connect(self.keylockStatus)
		
		self.pushButton_6.setVisible(False)
		
		self.trendMode = False				#False: skin / True: heater
		self.trendIntervalMode = 0		#0:1h / 1:2h / 2:4h / 3:6h / 4:8h / 5:12h / 6:24h / 7:48h / 8:72h / 9:1w
		self.skinData = "--.--"
		self.graphWidget = pg.PlotWidget()
		self.x = list(range(60))
		self.y = [0 for _ in range(60)]
		self.allTempData = [0 for _ in range(10080)]
		self.allHeatData = [0 for _ in range(10080)]
		
		self.graphWidget.setBackground('w')
		pen = pg.mkPen(color = (0, 162, 232), width=2)
		
		self.graphWidget.showGrid(x=True, y=True)
		#self.graphWidget.setXRange(0, 60, padding=0)
		self.graphWidget.setYRange(0, 50, padding=0)
		self.graphWidget.hideAxis('bottom')
		self.dataLine = self.graphWidget.plot(self.x, self.y, pen=pen)
		self.verticalLayout_2.addWidget(self.graphWidget)
		self.groupBox.setEnabled(False)
		
		self.zoomStatus = False
		
		self.timerGraph = QtCore.QTimer()
		self.timerGraph.setInterval(60*1000)
		self.timerGraph.timeout.connect(self.updatePlotData)
		self.timerGraph.start()
		
		self.timerPowerStatus = QtCore.QTimer()
		self.timerPowerStatus.setInterval(200)
		self.timerPowerStatus.timeout.connect(self.updatePowerStatus)
		self.timerPowerStatus.start()
		
		self.timerClearVoltage = QtCore.QTimer()
		self.timerClearVoltage.setInterval(1000)
		self.timerClearVoltage.timeout.connect(self.clearVoltage)
		
		self.listWidget.setEnabled(False)
		self.alarmMode = False
		self.alarmList = [False, False, False,		#Crit Temp, High Temp, Low Temp 
						  False, False,				#Power Fail, Low Battery,
						  False, False,				#Skin Not plugged, Skin Error
						  False]					#Manual Mode Reminder
		self.alarmListOld = [False, False, False,		#Crit Temp, High Temp, Low Temp 
						  False, False,				#Power Fail, Low Battery,
						  False, False,				#Skin Not plugged, Skin Error
						  False]					#Manual Mode Reminder
						  
		self.timerAlarmMode = QtCore.QTimer()
		self.timerAlarmMode.setInterval(200)
		self.timerAlarmMode.timeout.connect(self.runAlarmMode)
		
		self.timerManualModeReminder = QtCore.QTimer()
		self.timerManualModeReminder.setInterval(15*60*1000)
		self.timerManualModeReminder.timeout.connect(self.manualModeReminder)
		
		self.timerCheckAlarms = QtCore.QTimer()
		self.timerCheckAlarms.setInterval(200)
		self.timerCheckAlarms.timeout.connect(self.checkAlarms)
		self.timerCheckAlarms.start()
		
		self.isMuted = False
		self.timerMute = QtCore.QTimer()
		self.timerMute.setInterval(15*60*1000)
		self.timerMute.timeout.connect(self.muteTimeout)
		
		self.thread = {}
		
		self.updateSkinWorker()
		self.updateDateWorker()
		
		self.timerCheckLanguage = QtCore.QTimer()
		self.timerCheckLanguage.setInterval(500)
		self.timerCheckLanguage.timeout.connect(self.checkLanguage)
		self.timerCheckLanguage.start()
		
		
		self.currentLanguage = self.dateTimeWindow.currentLanguage
		self.oldLanguage = self.dateTimeWindow.currentLanguage
		
		if(self.currentLanguage == 0):
			self.englishLanguage()
		elif(self.currentLanguage == 1):
			self.russianLanguage()
		elif(self.currentLanguage == 2):
			self.turkishLanguage()
			
		'''
		self.englishLanguageIcon = QtGui.QIcon("/home/eomedical/images/lang-english.png")
		self.pushButton_14.setIcon(self.englishLanguageIcon)
		self.pushButton_14.setIconSize(QtCore.QSize(60, 60))
		'''
		
		self.timerUpdateWeight = QtCore.QTimer()
		self.timerUpdateWeight.setInterval(1000)
		self.timerUpdateWeight.timeout.connect(self.updateWeight)
		self.timerUpdateWeight.start()
		
		self.timerUpdateAngle = QtCore.QTimer()
		self.timerUpdateAngle.setInterval(1000)
		self.timerUpdateAngle.timeout.connect(self.updateAngle)
		self.timerUpdateAngle.start()
		
		self.setHeater(0, 25, False)
		
	def heaterControl(self):
		if(self.skinValidFlag and not(self.alarmList[5])):
			self.heaterMode = (self.heaterMode+1)%3
		else:
			self.heaterMode = (self.heaterMode+1)%2
		if(self.heaterMode == 0):
			self.setHeater(0, 25, False)
		if(self.heaterMode == 1):
			self.setHeater(1, 50, False)
		if(self.heaterMode == 2):
			self.setHeater(2, 0, False)
		
	def setHeater(self, heater_mode, pwm_value, mute_alarm_reminder):
		self.heaterMode = heater_mode
		self.pwmValue = pwm_value
		if(self.heaterMode == 0):	# Prewarm Mode
			self.enable37Flag = 0
			self.label_5.setText(str(self.pwmValue)+"%")
			self.heaterPWM.ChangeDutyCycle(self.pwmValue)
			if(self.currentLanguage == 0):
				self.pushButton_3.setText("Prewarm")
			elif(self.currentLanguage == 1):
				self.pushButton_3.setText("Пред.\nнагрев")
			elif(self.currentLanguage == 2):
				self.pushButton_3.setText("Ön Isıtma")
				
			self.pushButton.setVisible(False)
			self.pushButton_2.setVisible(False)
			self.pushButton_4.setVisible(False)
			self.pushButton_5.setVisible(False)
			self.pushButton_6.setVisible(False)
			self.label_7.setVisible(False)
			self.label_8.setVisible(False)
			self.alarmList[7] = mute_alarm_reminder
			self.timerManualModeReminder.stop()

		if(self.heaterMode == 1):
			self.enable37Flag = 0
			self.label_5.setText(str(self.pwmValue)+"%")
			self.heaterPWM.ChangeDutyCycle(self.pwmValue)
			if(self.currentLanguage == 0):
				self.pushButton_3.setText("Manual")
			elif(self.currentLanguage == 1):
				self.pushButton_3.setText("Ручной")
			elif(self.currentLanguage == 2):
				self.pushButton_3.setText("Manuel")
			self.pushButton.setVisible(True)
			self.pushButton_2.setVisible(True)
			self.pushButton_4.setVisible(False)
			self.pushButton_5.setVisible(False)
			self.pushButton_6.setVisible(False)
			self.label_7.setVisible(False)
			self.label_8.setVisible(False)
			self.alarmList[7] = mute_alarm_reminder
			self.timerManualModeReminder.start()

			
		if(self.heaterMode == 2):
			self.servoSet = 36.0
			self.label_7.setText(str(round(self.servoSet, 1)))
			if(self.currentLanguage == 0):
				self.pushButton_3.setText("Servo")
			elif(self.currentLanguage == 1):
				self.pushButton_3.setText("Серво")
			elif(self.currentLanguage == 2):
				self.pushButton_3.setText("Servo")
			self.pushButton.setVisible(False)
			self.pushButton_2.setVisible(False)
			self.pushButton_4.setVisible(True)
			self.pushButton_5.setVisible(True)
			self.label_7.setVisible(True)
			self.label_8.setVisible(True)
			self.alarmList[7] = mute_alarm_reminder
			self.timerManualModeReminder.stop()
			
	def manualModeReminder(self):
		self.alarmList[7] = True
			
	def heatUp(self):
		self.pwmValue = self.pwmValue + 5
		if(self.pwmValue>=100):
			self.pwmValue = 100
		self.heaterPWM.ChangeDutyCycle(self.pwmValue)
		self.label_5.setText(str(self.pwmValue)+"%")
		self.alarmList[7] = False
		self.timerManualModeReminder.stop()
		self.timerManualModeReminder.start()	
		
	def heatDown(self):
		self.pwmValue = self.pwmValue - 5
		if(self.pwmValue<=0):
			self.pwmValue = 0
		self.heaterPWM.ChangeDutyCycle(self.pwmValue)
		self.label_5.setText(str(self.pwmValue)+"%")
		self.alarmList[7] = False
		self.timerManualModeReminder.stop()
		self.timerManualModeReminder.start()
		
	def setSkinUp(self):
		self.servoSet = self.servoSet + 0.1
		if(self.servoSet >= 37):
			if(self.enable37Flag == 1):
				if(self.servoSet>=38):
					self.servoSet = 38.0
			else:
				self.servoSet = 37.0
			if(self.enable37Flag == 0):	
				self.pushButton_6.setVisible(True)
			else: 
				self.pushButton_6.setVisible(False)
		self.label_7.setText(str(round(self.servoSet, 1)))
		
	def setSkinDown(self):
		self.servoSet = self.servoSet - 0.1
		if(self.servoSet <= 37 ):
			self.enable37Flag = 0
		if(self.servoSet <= 30):
			self.servoSet = 30.0
		self.label_7.setText(str(round(self.servoSet, 1)))
		self.pushButton_6.setVisible(False)
		
	def enable37(self):
		if(self.enable37Flag == 0):
			self.enable37Flag = 1
			self.pushButton_6.setVisible(False)
		
	def lamp1Control(self):
		self.lamp1Status = not(self.lamp1Status)
		GPIO.output(self.lamp1Pin, self.lamp1Status)
		
	def lamp2Control(self):
		self.lamp2Status = not(self.lamp2Status)
		GPIO.output(self.lamp2Pin, self.lamp2Status)
		
	def timerMode(self):
		self.timerModeValue = 0
		'''self.timerModeValue = (self.timerModeValue + 1) % 2
		if(self.timerModeValue == 0):
			self.pushButton_12.setText("Apgar")
		else:
			self.pushButton_12.setText("CPR")'''
			
	def timerUp(self):
		self.timerSetValue += 5
		if(self.timerSetValue>=90):
			self.timerSetValue = 90
		if(self.timerSetValue<10):
			self.timerText = "0" + str(self.timerSetValue) + ":00"
		else:
			self.timerText = str(self.timerSetValue) + ":00"
		self.lcdNumber.display(self.timerText)
		if(self.timerSetValue != 0):
			self.pushButton_9.setVisible(True)
		else:
			self.pushButton_9.setVisible(False)
		
	def timerDown(self):
		self.timerSetValue-= 5
		if(self.timerSetValue<=0):
			self.timerSetValue = 0
		if(self.timerSetValue<10):
			self.timerText = "0" + str(self.timerSetValue) + ":00"
		else:
			self.timerText = str(self.timerSetValue) + ":00"
		self.lcdNumber.display(self.timerText)
		if(self.timerSetValue != 0):
			self.pushButton_9.setVisible(True)
		else:
			self.pushButton_9.setVisible(False)
			
	def timerStart(self):
		if(self.pushButton_12.isEnabled()):
			self.lcdNumber.display("00:00")
			if(self.alarmMode == False):
				self.timerBuzzerLong.start()	
		self.timerTimer.start()
		self.pushButton_7.setVisible(False)
		self.pushButton_8.setVisible(False)
		self.pushButton_9.setVisible(False)
		self.pushButton_10.setVisible(True)
		self.pushButton_11.setVisible(True)
		self.pushButton_12.setEnabled(False)
		
	def timerPause(self):
		self.timerTimer.stop()
		self.pushButton_7.setVisible(False)
		self.pushButton_8.setVisible(False)
		self.pushButton_9.setVisible(True)
		self.pushButton_10.setVisible(False)
		self.pushButton_11.setVisible(True)
		self.pushButton_12.setEnabled(False)
		
	def timerStop(self):
		self.timerTimer.stop()
		if(self.alarmMode == False):
			self.timerBuzzerShort.start()
		self.timerSetValue = 0
		self.timerMinutes = 0
		self.timerSeconds = 0
		self.lcdNumber.display("00:00")
		self.pushButton_7.setVisible(True)
		self.pushButton_8.setVisible(True)
		self.pushButton_9.setVisible(False)
		self.pushButton_10.setVisible(False)
		self.pushButton_11.setVisible(False)
		if(self.keylockValue == 100):
			self.pushButton_7.setEnabled(False)
			self.pushButton_8.setEnabled(False)
			self.pushButton_12.setEnabled(False)
		else:
			self.pushButton_7.setEnabled(True)
			self.pushButton_8.setEnabled(True)
			self.pushButton_12.setEnabled(True)
		
	def timerCalculator(self):
		self.timerSeconds += 1
		if(self.timerSeconds == 60):
			self.timerMinutes += 1
			self.timerSeconds = 0
		if(self.timerMinutes == self.timerSetValue):
			self.timerStop()
		else:	
			if(self.timerModeValue == 0):	#Apgar
				if(self.timerMinutes == 1 and self.timerSeconds == 0):
					if(self.alarmMode == False):
						self.timerBuzzerLong.start()
				if(self.timerMinutes%5 == 0 and self.timerSeconds == 0):
					if(self.alarmMode == False):
						self.timerBuzzerLong.start()
			
		if(self.timerMinutes <10):
			self.timerText = "0" + str(self.timerMinutes)
			if(self.timerSeconds < 10):
				self.timerText = self.timerText + ":0" + str(self.timerSeconds)
			else:
				self.timerText = self.timerText + ":" + str(self.timerSeconds)
		else:
			self.timerText = str(self.timerMinutes)
			if(self.timerSeconds < 10):
				self.timerText = self.timerText + ":0" + str(self.timerSeconds)
			else:
				self.timerText = self.timerText + ":" + str(self.timerSeconds)
		self.lcdNumber.display(self.timerText)
		
	def buzzerShort(self):
		self.buzzerStatus = not self.buzzerStatus
		GPIO.output(self.buzzerPin, self.buzzerStatus)
		self.buzzerCounter += 1
		if(self.buzzerCounter == 10):
			self.buzzerCounter = 0
			self.timerBuzzerShort.stop()

	def buzzerLong(self):
		self.buzzerCounter += 1
		if(self.buzzerCounter<10):
			self.buzzerStatus = True
			GPIO.output(self.buzzerPin, self.buzzerStatus)
		else:
			self.buzzerCounter = 0
			self.buzzerStatus = False
			GPIO.output(self.buzzerPin, self.buzzerStatus)
			self.timerBuzzerLong.stop()
			
	def updatePowerStatus(self):
		f = open("/sys/bus/iio/devices/iio:device0/in_voltage0_raw")
		self.batteryVoltage =  int(f.read()) * 0.062500 * 4.3
		self.batteryVoltage = round(self.batteryVoltage)
		f.close()
		self.powerStatus = GPIO.input(self.powerStatusPin)
		if(self.powerStatus == True):
			self.pushButton_13.setIcon(self.lightingIcon)
		else:
			if(self.batteryVoltage > 3805):
				self.pushButton_13.setIcon(self.fullBatteryIcon)
			if(self.batteryVoltage > 3655 and self.batteryVoltage < 3800):
				self.pushButton_13.setIcon(self.halfBatteryIcon)
			if(self.batteryVoltage < 3650):
				self.pushButton_13.setIcon(self.lowBatteryIcon)
			
	def powerStatusCheck(self):
		self.label_10.setText(str(self.batteryVoltage) + " mV")
		self.timerClearVoltage.start()
		
	def clearVoltage(self):
		self.label_10.setText("")
		self.timerClearVoltage.stop()
		
	def runAlarmMode(self):
		self.buzzerStatus = not self.buzzerStatus;
		self.alarmLedStatus = not self.alarmLedStatus;
		GPIO.output(self.buzzerPin, self.buzzerStatus)
		GPIO.output(self.alarmLedPin, self.alarmLedStatus)
		
	def muteAlarmMode(self):
		self.timerAlarmMode.stop()
		self.alarmMode = 0
		self.buzzerStatus = False
		self.alarmLedStatus = False
		GPIO.output(self.buzzerPin, self.buzzerStatus)
		GPIO.output(self.alarmLedPin, self.alarmLedStatus)
		
	
	def stopAlarmMode(self):
		self.timerAlarmMode.stop()
		self.alarmMode = False
		self.buzzerStatus = False
		self.alarmLedStatus = True
		GPIO.output(self.buzzerPin, self.buzzerStatus)
		GPIO.output(self.alarmLedPin, self.alarmLedStatus)
		
	def checkLanguage(self):
		self.currentLanguage = self.dateTimeWindow.currentLanguage
		if(self.currentLanguage != self.oldLanguage):
			if(self.currentLanguage == 0):
				self.englishLanguage()
				langFile = open("lang.txt", "w")
				langFile.write("en")
				langFile.close()
			elif(self.currentLanguage == 1):
				self.russianLanguage()
				langFile = open("lang.txt", "w")
				langFile.write("ru")
				langFile.close()
			elif(self.currentLanguage == 2):
				self.turkishLanguage()
				langFile = open("lang.txt", "w")
				langFile.write("tr")
				langFile.close()
				
		self.oldLanguage = self.currentLanguage
		
	def englishLanguage(self):
		self.radioButton_2.setText("Lamp1")
		self.radioButton_3.setText("Lamp2")
		self.label_8.setText("Set (°C)")
		self.pushButton_12.setText("Apgar")
		self.pushButton_16.setText("Mute")
		if(self.trendIntervalMode == 0):
			self.pushButton_17.setText("1\nHour")
		elif(self.trendIntervalMode == 1):
			self.pushButton_17.setText("2\nHours")
		elif(self.trendIntervalMode == 2):
			self.pushButton_17.setText("4\nHours")
		elif(self.trendIntervalMode == 3):
			self.pushButton_17.setText("6\nHours")
		elif(self.trendIntervalMode == 4):
			self.pushButton_17.setText("8\nHours")
		elif(self.trendIntervalMode == 5):
			self.pushButton_17.setText("12\nHours")
		elif(self.trendIntervalMode == 6):
			self.pushButton_17.setText("24\nHours")
		elif(self.trendIntervalMode == 7):
			self.pushButton_17.setText("48\nHours")
		elif(self.trendIntervalMode == 8):
			self.pushButton_17.setText("72\nHours")
		else:
			self.pushButton_17.setText("1\nWeek")
			
		if(self.trendMode == False):
			self.pushButton_19.setText("Skin")
			self.groupBox.setTitle("  Skin Temperature (°C)")
		else:
			self.pushButton_19.setText("Heat")
			self.groupBox.setTitle("  Heater Performance (%)")
		
		self.dateTimeWindow.label_4.setText("Hour")
		self.dateTimeWindow.label_5.setText("Min")
		self.dateTimeWindow.label_6.setText("Day")
		self.dateTimeWindow.label_7.setText("Month")
		self.dateTimeWindow.label_8.setText("Year")
		self.dateTimeWindow.label_11.setText("0 KG\nCalibration")
		self.dateTimeWindow.label_12.setText("5 KG\nCalibration")
		self.dateTimeWindow.label_13.setText("Tare")
		self.dateTimeWindow.pushButton_11.setText("Set")
		self.dateTimeWindow.pushButton_12.setText("Exit")
		if(self.heaterMode == 0):
			self.pushButton_3.setText("Prewarm")
		if(self.heaterMode == 1):
			self.pushButton_3.setText("Manual")
		if(self.heaterMode == 2):
			self.pushButton_3.setText("Servo")
			
	def russianLanguage(self):
		self.radioButton_2.setText("Лампа1")
		self.radioButton_3.setText("Лампа2")
		self.label_8.setText("Уст. (°C)")
		self.pushButton_12.setText("Апгар")
		self.pushButton_16.setText("Без звука")
		if(self.trendIntervalMode == 0):
			self.pushButton_17.setText("1\nЧас")
		elif(self.trendIntervalMode == 1):
			self.pushButton_17.setText("2\nЧас")
		elif(self.trendIntervalMode == 2):
			self.pushButton_17.setText("4\nЧас")
		elif(self.trendIntervalMode == 3):
			self.pushButton_17.setText("6\nЧас")
		elif(self.trendIntervalMode == 4):
			self.pushButton_17.setText("8\nЧас")
		elif(self.trendIntervalMode == 5):
			self.pushButton_17.setText("12\nЧас")
		elif(self.trendIntervalMode == 6):
			self.pushButton_17.setText("24\nЧас")
		elif(self.trendIntervalMode == 7):
			self.pushButton_17.setText("48\nЧас")
		elif(self.trendIntervalMode == 8):
			self.pushButton_17.setText("72\nЧас")
		else:
			self.pushButton_17.setText("1\nНед.")
			
		if(self.trendMode == False):
			self.pushButton_19.setText("Кожа")
			self.groupBox.setTitle("  Температура кожи (°C)")
		else:
			self.pushButton_19.setText("Тепло")
			self.groupBox.setTitle("  Производительность нагревателя (%)")
		
		self.dateTimeWindow.label_4.setText("Час")
		self.dateTimeWindow.label_5.setText("Минута")
		self.dateTimeWindow.label_6.setText("День")
		self.dateTimeWindow.label_7.setText("Месяц")
		self.dateTimeWindow.label_8.setText("Год")
		self.dateTimeWindow.label_11.setText("Калибровка\n0 КГ")
		self.dateTimeWindow.label_12.setText("Калибровка\n5 КГ")
		self.dateTimeWindow.label_13.setText("Тара")
		self.dateTimeWindow.pushButton_11.setText("Уст.")
		self.dateTimeWindow.pushButton_12.setText("Выход")
		if(self.heaterMode == 0):
			self.pushButton_3.setText("Пред.\nнагрев")
		if(self.heaterMode == 1):
			self.pushButton_3.setText("Ручной")
		if(self.heaterMode == 2):
			self.pushButton_3.setText("Серво")
			
		
	def turkishLanguage(self):
		self.radioButton_2.setText("Lamba1")
		self.radioButton_3.setText("Lamba2")
		self.label_8.setText("Set (°C)")
		self.pushButton_12.setText("Apgar")
		self.pushButton_16.setText("Sustur")
		if(self.trendIntervalMode == 0):
			self.pushButton_17.setText("1\nSaat")
		elif(self.trendIntervalMode == 1):
			self.pushButton_17.setText("2\nSaat")
		elif(self.trendIntervalMode == 2):
			self.pushButton_17.setText("4\nSaat")
		elif(self.trendIntervalMode == 3):
			self.pushButton_17.setText("6\nSaat")
		elif(self.trendIntervalMode == 4):
			self.pushButton_17.setText("8\nSaat")
		elif(self.trendIntervalMode == 5):
			self.pushButton_17.setText("12\nSaat")
		elif(self.trendIntervalMode == 6):
			self.pushButton_17.setText("24\nSaat")
		elif(self.trendIntervalMode == 7):
			self.pushButton_17.setText("48\nSaat")
		elif(self.trendIntervalMode == 8):
			self.pushButton_17.setText("72\nSaat")
		else:
			self.pushButton_17.setText("1\nHafta")
			
		if(self.trendMode == False):
			self.pushButton_19.setText("Cilt")
			self.groupBox.setTitle("  Cilt Sıcaklığı (°C)")
		else:
			self.pushButton_19.setText("Isı")
			self.groupBox.setTitle("  Isıtıcı Performansı (%)")

		self.dateTimeWindow.label_4.setText("Saat")
		self.dateTimeWindow.label_5.setText("Dakika")
		self.dateTimeWindow.label_6.setText("Gün")
		self.dateTimeWindow.label_7.setText("Ay")
		self.dateTimeWindow.label_8.setText("Yıl")
		self.dateTimeWindow.label_11.setText("0 KG\nKalibrasyonu")
		self.dateTimeWindow.label_12.setText("5 KG\nKalibrasyonu")
		self.dateTimeWindow.label_13.setText("Dara")
		self.dateTimeWindow.pushButton_11.setText("Ayarla")
		self.dateTimeWindow.pushButton_12.setText("Çıkış")
		if(self.heaterMode == 0):
			self.pushButton_3.setText("Ön Isıtma")
		if(self.heaterMode == 1):
			self.pushButton_3.setText("Manuel")
		if(self.heaterMode == 2):
			self.pushButton_3.setText("Servo")
		
	def settings(self):
		self.dateTimeWindow.showFullScreen()
			
	def keylockStatus(self):
		if(self.keylockValue == 0 and self.horizontalSlider.value()>=80):
			self.lockAll()
			self.keylockValue = 100
			self.horizontalSlider.setValue(self.keylockValue)
		if(self.keylockValue == 0 and self.horizontalSlider.value()<80):
			self.unlockAll()
			self.keylockValue = 0
			self.horizontalSlider.setValue(self.keylockValue)
		if(self.keylockValue == 100 and self.horizontalSlider.value()<=20):
			self.unlockAll()
			self.keylockValue = 0
			self.horizontalSlider.setValue(self.keylockValue)
		if(self.keylockValue == 100 and self.horizontalSlider.value()>20):
			self.lockAll()
			self.keylockValue = 100
			self.horizontalSlider.setValue(self.keylockValue)
				
	def unlockAll(self):
		self.pushButton.setEnabled(True)
		self.pushButton_2.setEnabled(True)
		self.pushButton_3.setEnabled(True)
		self.pushButton_4.setEnabled(True)
		self.pushButton_5.setEnabled(True)
		self.pushButton_6.setEnabled(True)
		if(self.timerMinutes == 0 and self.timerSeconds == 0):
			self.pushButton_7.setEnabled(True)
			self.pushButton_8.setEnabled(True)
			self.pushButton_9.setEnabled(True)
			self.pushButton_10.setEnabled(True)
			self.pushButton_11.setEnabled(True)
			self.pushButton_12.setEnabled(True)
		else:
			self.pushButton_7.setEnabled(False)
			self.pushButton_8.setEnabled(False)
			self.pushButton_9.setEnabled(True)
			self.pushButton_10.setEnabled(True)
			self.pushButton_11.setEnabled(True)
			self.pushButton_12.setEnabled(False)
		self.pushButton_13.setEnabled(True)
		self.pushButton_14.setEnabled(True)
		self.pushButton_16.setEnabled(True)
		self.pushButton_17.setEnabled(True)
		self.pushButton_18.setEnabled(True)
		self.pushButton_19.setEnabled(True)
		self.radioButton_2.setEnabled(True)
		self.radioButton_3.setEnabled(True)
		self.label_9.setPixmap(self.unlockPixmap)
		
	def lockAll(self):
		self.pushButton.setEnabled(False)
		self.pushButton_2.setEnabled(False)
		self.pushButton_3.setEnabled(False)
		self.pushButton_4.setEnabled(False)
		self.pushButton_5.setEnabled(False)
		self.pushButton_6.setEnabled(False)
		self.pushButton_7.setEnabled(False)
		self.pushButton_8.setEnabled(False)
		self.pushButton_9.setEnabled(False)
		self.pushButton_10.setEnabled(False)
		self.pushButton_11.setEnabled(False)
		self.pushButton_12.setEnabled(False)
		self.pushButton_13.setEnabled(False)
		self.pushButton_14.setEnabled(False)
		self.pushButton_16.setEnabled(False)
		self.pushButton_17.setEnabled(False)
		self.pushButton_18.setEnabled(False)
		self.pushButton_19.setEnabled(False)
		self.radioButton_2.setEnabled(False)
		self.radioButton_3.setEnabled(False)
		self.label_9.setPixmap(self.lockPixmap)
		
	def trendInterval(self):
		self.trendIntervalMode = (self.trendIntervalMode+1)%10
		
		def lastN(n):
			listLastN = self.allTempData[len(self.allTempData)-n:len(self.allTempData)]
			return listLastN
			
		def heatLastN(n):
			listLastN = self.allHeatData[len(self.allHeatData)-n:len(self.allHeatData)]
			return listLastN
		
		if(self.trendMode == False):
			if(self.trendIntervalMode == 0):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("1\nHour")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("1\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("1\nSaat")
				self.y = lastN(60)
			elif(self.trendIntervalMode == 1):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("2\nHours")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("2\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("2\nSaat")
				self.y = lastN(120)[1::2]
			elif(self.trendIntervalMode == 2):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("4\nHours")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("4\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("4\nSaat")
				self.y = lastN(240)[3::4]
			elif(self.trendIntervalMode == 3):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("6\nHours")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("6\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("6\nSaat")
				self.y = lastN(360)[5::6]
			elif(self.trendIntervalMode == 4):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("8\nHours")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("8\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("8\nSaat")
				self.y = lastN(480)[7::8]
			elif(self.trendIntervalMode == 5):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("12\nHours")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("12\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("12\nSaat")
				self.y = lastN(720)[11::12]
			elif(self.trendIntervalMode == 6):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("24\nHours")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("24\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("24\nSaat")
				self.y = lastN(1440)[23::24]
			elif(self.trendIntervalMode == 7):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("48\nHours")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("48\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("48\nSaat")
				self.y = lastN(2880)[47::48]
			elif(self.trendIntervalMode == 8):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("72\nHours")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("72\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("72\nSaat")
				self.y = lastN(4320)[71::72]
			else:
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("1\nWeek")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("1\nНед.")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("1\nHafta")
				self.y = lastN(10080)[167::168]
		else:
			if(self.trendIntervalMode == 0):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("1\nHour")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("1\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("1\nSaat")
				self.y = heatLastN(60)
			elif(self.trendIntervalMode == 1):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("2\nHour")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("2\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("2\nSaat")
				self.y = heatLastN(120)[1::2]
			elif(self.trendIntervalMode == 2):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("4\nHour")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("4\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("4\nSaat")
				self.y = heatLastN(240)[3::4]
			elif(self.trendIntervalMode == 3):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("6\nHour")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("6\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("6\nSaat")
				self.y = heatLastN(360)[5::6]
			elif(self.trendIntervalMode == 4):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("8\nHour")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("8\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("8\nSaat")
				self.y = heatLastN(480)[7::8]
			elif(self.trendIntervalMode == 5):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("12\nHour")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("12\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("12\nSaat")
				self.y = heatLastN(720)[11::12]
			elif(self.trendIntervalMode == 6):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("24\nHour")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("24\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("24\nSaat")
				self.y = heatLastN(1440)[23::24]
			elif(self.trendIntervalMode == 7):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("48\nHour")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("48\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("48\nSaat")
				self.y = heatLastN(2880)[47::48]
			elif(self.trendIntervalMode == 8):
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("72\nHour")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("72\nЧас")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("72\nSaat")
				self.y = heatLastN(4320)[71::72]
			else:
				if(self.currentLanguage == 0):
					self.pushButton_17.setText("1\nWeek")
				elif(self.currentLanguage == 1):
					self.pushButton_17.setText("1\nНед.")
				elif(self.currentLanguage == 2):
					self.pushButton_17.setText("1\nHafta")
				self.y = heatLastN(10080)[167::168]
			
		self.dataLine.setData(self.x, self.y)
	
	def updatePlotData(self):
		self.x = self.x[1:]
		self.x.append(self.x[-1] + 1)
		
		self.allTempData = self.allTempData[1:]
		self.allTempData.append(self.skinTempData)
		
		self.allHeatData = self.allHeatData[1:]
		self.allHeatData.append(self.pwmValue)
		
		def lastN(n):
			listLastN = self.allTempData[len(self.allTempData)-n:len(self.allTempData)]
			return listLastN
			
		def heatLastN(n):
			listLastN = self.allHeatData[len(self.allHeatData)-n:len(self.allHeatData)]
			return listLastN
		
		if(self.trendMode == False):
			if(self.trendIntervalMode == 0):
				self.y = lastN(60)
			elif(self.trendIntervalMode == 1):
				self.y = lastN(120)[1::2]
			elif(self.trendIntervalMode == 2):
				self.y = lastN(240)[3::4]
			elif(self.trendIntervalMode == 3):
				self.y = lastN(360)[5::6]
			elif(self.trendIntervalMode == 4):
				self.y = lastN(480)[7::8]
			elif(self.trendIntervalMode == 5):
				self.y = lastN(720)[11::12]
			elif(self.trendIntervalMode == 6):
				self.y = lastN(1440)[23::24]
			elif(self.trendIntervalMode == 7):
				self.y = lastN(2880)[47::48]
			elif(self.trendIntervalMode == 8):
				self.y = lastN(4320)[71::72]
			else:
				self.y = lastN(10080)[167::168]
		else:
			if(self.trendIntervalMode == 0):
				self.y = heatLastN(60)
			elif(self.trendIntervalMode == 1):
				self.y = heatLastN(120)[1::2]
			elif(self.trendIntervalMode == 2):
				self.y = heatLastN(240)[3::4]
			elif(self.trendIntervalMode == 3):
				self.y = heatLastN(360)[5::6]
			elif(self.trendIntervalMode == 4):
				self.y = heatLastN(480)[7::8]
			elif(self.trendIntervalMode == 5):
				self.y = heatLastN(720)[11::12]
			elif(self.trendIntervalMode == 6):
				self.y = heatLastN(1440)[23::24]
			elif(self.trendIntervalMode == 7):
				self.y = heatLastN(2880)[47::48]
			elif(self.trendIntervalMode == 8):
				self.y = heatLastN(4320)[71::72]
			else:
				self.y = heatLastN(10080)[167::168]
		
		self.dataLine.setData(self.x, self.y)
		
	def zoomIn(self):
		self.zoomStatus = not self.zoomStatus
		if(self.trendMode == False):
			if(self.zoomStatus == False):
				self.pushButton_18.setText("+")
				self.graphWidget.setYRange(0, 50, padding=0)
			else:
				self.pushButton_18.setText("-")
				self.graphWidget.setYRange(30, 40, padding=0)
		else:
			if(self.zoomStatus == False):
				self.pushButton_18.setText("+")
				self.graphWidget.setYRange(0, 100, padding=0)
			else:
				self.pushButton_18.setText("-")
				self.graphWidget.setYRange(20, 80, padding=0)
		
	def trendChange(self):
		self.trendMode = not self.trendMode
		
		def lastN(n):
			listLastN = self.allTempData[len(self.allTempData)-n:len(self.allTempData)]
			return listLastN
			
		def heatLastN(n):
			listLastN = self.allHeatData[len(self.allHeatData)-n:len(self.allHeatData)]
			return listLastN
			
		if(self.trendMode == False):
			if(self.currentLanguage == 0):
				self.pushButton_19.setText("Skin")
				self.groupBox.setTitle("  Skin Temperature (°C)")
			elif(self.currentLanguage == 1):
				self.pushButton_19.setText("Кожа")
				self.groupBox.setTitle("  Температура кожи (°C)")
			elif(self.currentLanguage == 2):
				self.pushButton_19.setText("Cilt")
				self.groupBox.setTitle("  Cilt Sıcaklığı (°C)")
				
			if(self.pushButton_18.text()=="+"):
				self.graphWidget.setYRange(0, 50, padding=0)
			else:
				self.graphWidget.setYRange(30, 40, padding=0)
				
			if(self.trendIntervalMode == 0):
				self.y = lastN(60)
			elif(self.trendIntervalMode == 1):
				self.y = lastN(120)[1::2]
			elif(self.trendIntervalMode == 2):
				self.y = lastN(240)[3::4]
			elif(self.trendIntervalMode == 3):
				self.y = lastN(360)[5::6]
			elif(self.trendIntervalMode == 4):
				self.y = lastN(480)[7::8]
			elif(self.trendIntervalMode == 5):
				self.y = lastN(720)[11::12]
			elif(self.trendIntervalMode == 6):
				self.y = lastN(1440)[23::24]
			elif(self.trendIntervalMode == 7):
				self.y = lastN(2880)[47::48]
			elif(self.trendIntervalMode == 8):
				self.y = lastN(4320)[71::72]
			else:
				self.y = lastN(10080)[167::168]
		else:
			if(self.currentLanguage == 0):
				self.pushButton_19.setText("Heat")
				self.groupBox.setTitle("  Heater Performance (%)")
			elif(self.currentLanguage == 1):
				self.pushButton_19.setText("Тепло")
				self.groupBox.setTitle("  Производительность нагревателя (%)")
			elif(self.currentLanguage == 2):
				self.pushButton_19.setText("Isı")
				self.groupBox.setTitle("  Isıtıcı Performansı (%)")
				
			if(self.pushButton_18.text()=="+"):
				self.graphWidget.setYRange(0, 110, padding=0)
			else:
				self.graphWidget.setYRange(20, 80, padding=0)
				
			if(self.trendIntervalMode == 0):
				self.y = heatLastN(60)
			elif(self.trendIntervalMode == 1):
				self.y = heatLastN(120)[1::2]
			elif(self.trendIntervalMode == 2):
				self.y = heatLastN(240)[3::4]
			elif(self.trendIntervalMode == 3):
				self.y = heatLastN(360)[5::6]
			elif(self.trendIntervalMode == 4):
				self.y = heatLastN(480)[7::8]
			elif(self.trendIntervalMode == 5):
				self.y = heatLastN(720)[11::12]
			elif(self.trendIntervalMode == 6):
				self.y = heatLastN(1440)[23::24]
			elif(self.trendIntervalMode == 7):
				self.y = heatLastN(2880)[47::48]
			elif(self.trendIntervalMode == 8):
				self.y = heatLastN(4320)[71::72]
			else:
				self.y = heatLastN(10080)[167::168]
			
		self.dataLine.setData(self.x, self.y)
		
	def checkAlarms(self):
		if(self.skinTempData >= 40):
			self.alarmList[0] = True
		else:
			self.alarmList[0] = False
			
		if(self.heaterMode == 2 and self.skinTempData >= self.servoSet + 1):
			self.alarmList[1] = True
		else:
			self.alarmList[1] = False
			
		if(self.heaterMode == 2 and self.skinTempData <= self.servoSet - 1):
			self.alarmList[2] = True
		else:
			self.alarmList[2] = False
			
		if(self.powerStatus == False):
			self.alarmList[3] = True
			if(self.batteryVoltage < 3500):
				self.alarmList[4] = True
			if(self.batteryVoltage > 3520):
				self.alarmList[4] = False
		else:
			self.alarmList[3] = False
			self.alarmList[4] = False
		
		if(self.skinData == 'Not Plugged' and self.heaterMode == 2):
			self.alarmList[5] = True
			
		if(self.skinData == 'Skin Error'):
			self.alarmList[6] = True
		else:
			self.alarmList[6] = False
			
		self.decideAlarms()
		
	def decideAlarms(self):
		if(self.alarmList[0] or self.alarmList[3] or self.alarmList[4] or self.alarmList[6]):
			if(not self.alarmMode):
				self.alarmMode = True
				self.timerAlarmMode.start()
		elif((self.alarmList[1] or self.alarmList[2] or self.alarmList[5] or self.alarmList[7]) and self.isMuted):
			self.muteAlarmMode()
		elif((self.alarmList[1] or self.alarmList[2] or self.alarmList[5] or self.alarmList[7]) and (not self.isMuted)):
			if(not self.alarmMode):
				self.alarmMode = True
				self.timerAlarmMode.start()
		else:
			self.isMuted = False
			self.stopAlarmMode()
		
		self.listWidget.clear()
		if(self.alarmList[0]):
			if(self.currentLanguage == 0):
				self.listWidget.insertItem(0, "Critical Temperature")
			elif(self.currentLanguage == 1):
				self.listWidget.insertItem(0, "Критическая температура")
			elif(self.currentLanguage == 2):
				self.listWidget.insertItem(0, "Kritik Sıcaklık")
		if(self.alarmList[1]):
			if(self.currentLanguage == 0):
				self.listWidget.insertItem(1, "High Temperature")
			elif(self.currentLanguage == 1):
				self.listWidget.insertItem(1, "Высокая температура")
			elif(self.currentLanguage == 2):
				self.listWidget.insertItem(1, "Yüksek Sıcaklık")
			if(self.isMuted):
				if(self.currentLanguage == 0):
					row = self.findRowList('High Temperature')
				elif(self.currentLanguage == 1):
					row = self.findRowList('Высокая температура')
				elif(self.currentLanguage == 2):
					row = self.findRowList('Yüksek Sıcaklık')
				
				self.listWidget.item(row).setForeground(QtGui.QColor('#00a2e8'))
		if(self.alarmList[2]):
			if(self.currentLanguage == 0):
				self.listWidget.insertItem(2, "Low Temperature")
			elif(self.currentLanguage == 1):
				self.listWidget.insertItem(2, "Низкая температура")
			elif(self.currentLanguage == 2):
				self.listWidget.insertItem(2, "Düşük Sıcaklık")
			if(self.isMuted):
				if(self.currentLanguage == 0):
					row = self.findRowList('Low Temperature')
				elif(self.currentLanguage == 1):
					row = self.findRowList('Низкая температура')
				elif(self.currentLanguage == 2):
					row = self.findRowList('Düşük Sıcaklık')
				self.listWidget.item(row).setForeground(QtGui.QColor('#00a2e8'))
		if(self.alarmList[3]):
			if(self.currentLanguage == 0):
				self.listWidget.insertItem(3, "Power Fail")
			elif(self.currentLanguage == 1):
				self.listWidget.insertItem(3, "Отсутствует питание")
			elif(self.currentLanguage == 2):
				self.listWidget.insertItem(3, "Güç Yok")
				
		if(self.alarmList[4]):
			if(self.currentLanguage == 0):
				self.listWidget.insertItem(4, "Low Battery")
			elif(self.currentLanguage == 1):
				self.listWidget.insertItem(4, "Низкий заряд батареи")
			elif(self.currentLanguage == 2):
				self.listWidget.insertItem(4, "Düşük Batarya")
		
		if(self.alarmList[5]):
			if(self.currentLanguage == 0):
				self.listWidget.insertItem(5, "Skin unplugged")
			elif(self.currentLanguage == 1):
				self.listWidget.insertItem(5, "Кожный датчик отключен")
			elif(self.currentLanguage == 2):
				self.listWidget.insertItem(5, "Cilt Yok")
			if(self.isMuted and (self.alarmListOld[5]==False)):
				if(self.currentLanguage == 0):
					row = self.findRowList('Skin Unplugged')
				elif(self.currentLanguage == 1):
					row = self.findRowList('Кожный датчик отключен')
				elif(self.currentLanguage == 2):
					row = self.findRowList('Cilt Yok')
				self.listWidget.item(row).setForeground(QtGui.QColor('#00a2e8'))
			else:
				if(not self.alarmMode):
					self.isMuted = False
			if(self.heaterMode == 2):
				self.setHeater(0, 25, False)	# Prewarm
				
		if(self.alarmList[6]):
			if(self.currentLanguage == 0):
				self.listWidget.insertItem(6, "Skin Error")
			elif(self.currentLanguage == 1):
				self.listWidget.insertItem(6, "Ошибка датчика кожи")
			elif(self.currentLanguage == 2):
				self.listWidget.insertItem(6, "Cilt Arızalı")
			self.setHeater(0, 25, False)	# Prewarm
			
		if(self.alarmList[7]):
			if(self.currentLanguage == 0):
				self.listWidget.insertItem(7, "Manual Mode")
			elif(self.currentLanguage == 1):
				self.listWidget.insertItem(7, "Ручной режим")
			elif(self.currentLanguage == 2):
				self.listWidget.insertItem(7, "Manuel Mod")
			self.setHeater(1, 30, True)
			if(self.isMuted):
				if(self.currentLanguage == 0):
					row = self.findRowList('Manual Mode')
				elif(self.currentLanguage == 1):
					row = self.findRowList('Ручной режим')
				elif(self.currentLanguage == 2):
					row = self.findRowList('Manuel Mod')
				self.listWidget.item(row).setForeground(QtGui.QColor('#00a2e8'))
				
		self.alarmListOld = self.alarmList

	def muteAlarmFunction(self):
		if(self.listWidget.count() > 0):
			if(self.skinValidFlag == 1 or self.heaterMode == 0 or self.heaterMode == 1):
				self.alarmList[5] = False
			self.isMuted = True
			self.timerMute.start()
	
	def findRowList(self, alarmMsg):
		for index in range(self.listWidget.count()):
			if(self.listWidget.item(index).text() == alarmMsg):
				return index
			
		
	def muteTimeout(self):
		self.isMuted = False
		
	def updateSkinWorker(self):
		self.thread[1] = SkinThreadClass(parent=None)
		self.thread[1].start()
		self.thread[1].any_signal.connect(self.updateSkinFunction)
		
	def updateDateWorker(self):
		self.thread[2] = DateThreadClass(parent=None)
		self.thread[2].start()
		self.thread[2].any_signal.connect(self.updateDateFunction)
		
	def updateSkinFunction(self, data):
		self.skinData = data
		if(self.skinData == 'Skin Error'):
			self.label_2.setText("--.--")
			self.skinValidFlag = 0
			self.skinTempData=0

		elif(self.skinData == 'Not Plugged'):
			self.label_2.setText("--.--")
			self.skinValidFlag = 0
			self.skinTempData = 0
			
		else:
			self.skinValidFlag = 1
			self.label_2.setText(self.skinData)
			self.skinTempData= float(self.skinData)
			if(self.heaterMode == 2):
				if(self.servoSet == self.skinTempData):
					self.pwmValue = 50
				if(self.servoSet > self.skinTempData):
					self.pwmValue = round(50 + (self.servoSet-self.skinTempData)*49)
					if(self.pwmValue >= 100):
						self.pwmValue = 100
				if(self.servoSet < self.skinTempData):
					self.pwmValue = round(50 - (self.skinTempData-self.servoSet)*49)
					if(self.pwmValue <= 0):
						self.pwmValue = 0
				self.label_5.setText(str(self.pwmValue)+"%")
				self.heaterPWM.ChangeDutyCycle(self.pwmValue)
				
	def updateDateFunction(self, date_data):
		dateData = date_data
		self.label_4.setText(dateData)
		
	def updateWeight(self):
		if(self.dateTimeWindow.weight1raw == 0 and self.dateTimeWindow.weight2raw == 0):
			self.label_6.setText("----")
		else:
			self.label_6.setText(str(self.dateTimeWindow.weight))
			
	def updateAngle(self):
		if(round(float(weightDb.get("roll"))) == 999):
			self.label_13.setText("----")
		else:
			self.label_13.setText(str(round(float(weightDb.get("roll")))))
			
class SkinThreadClass(QtCore.QThread):
	any_signal = QtCore.pyqtSignal(str)
	
	def __init__(self, parent=None):
		super(SkinThreadClass, self).__init__(parent)
		self.is_running = True
		self.adc = AD7171(20, 21)
		self.skin_sensor = SkinSensor(self.adc)
		
	def run(self):
		print("Starting Update Skin Thread ...")
		threadSkinData = 0
		while(True):
			threadSkinData = round((self.skin_sensor.read()/100.0), 1)
			self.skinValid = self.skin_sensor.is_valid()
			if self.skinValid:
				self.any_signal.emit(str(threadSkinData))
			else:
				if self.skin_sensor.resistor<100:
					self.any_signal.emit("Skin Error")
				else:
					self.any_signal.emit("Not Plugged")
			time.sleep(1)
			
				
	def stop(self):
		self.is_running = False
		print("Stopping Thread ...")
		self.terminate()
		
class DateThreadClass(QtCore.QThread):
	any_signal = QtCore.pyqtSignal(str)
	
	def __init__(self, parent=None):
		super(DateThreadClass, self).__init__(parent)
		self.is_running = True
		
	def run(self):
		print("Starting Date Skin Thread ...")
		threadDateData = 0
		while(True):
			threadDateData = datetime.now().strftime("  %H:%M:%S  %d/%m/%Y")
			self.any_signal.emit(str(threadDateData))
			time.sleep(1)
			
				
	def stop(self):
		self.is_running = False
		print("Stopping Thread ...")
		self.terminate()
		

app = QtWidgets.QApplication(sys.argv)
mainWindow = OPENBED_APP()
mainWindow.showFullScreen()
sys.exit(app.exec_())
