from PyQt5 import QtCore, QtGui, QtWidgets
from test6 import Ui_MainWindow
from skin_module import AD7171, SkinSensor
from datetime import datetime
import threading
import RPi.GPIO as GPIO

heaterPin = 12
lamp1Pin = 23
lamp2Pin = 24
buzzerPin = 25
alarmLedPin = 6

adc = AD7171(20, 21)
skin_sensor = SkinSensor(adc)

class mainProgram(QtWidgets.QMainWindow, Ui_MainWindow):
	def __init__(self, parent=None):
		super(mainProgram, self).__init__(parent)
		self.setupUi(self)
		self.pushButton.clicked.connect(self.heatUp)
		self.pushButton_2.clicked.connect(self.heatDown)
		self.pushButton_3.clicked.connect(self.heaterTest)
		self.pushButton_4.clicked.connect(self.setSkinUp)
		self.pushButton_5.clicked.connect(self.setSkinDown)
		self.radioButton_2.clicked.connect(self.lamp1Test)
		self.radioButton_3.clicked.connect(self.lamp2Test)
		self.radioButton_4.clicked.connect(self.buzzerTest)
		self.radioButton_5.clicked.connect(self.alarmLedTest)
		
		self.showFullScreen()
		
		self.heaterStatus = False;
		self.lamp1Status = False;
		self.lamp2Status = False;
		self.buzzerStatus = False;
		self.alarmLedStatus = True;
		
		GPIO.setwarnings(False)
		
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(heaterPin, GPIO.OUT)
		GPIO.setup(lamp1Pin, GPIO.OUT)
		GPIO.setup(lamp2Pin, GPIO.OUT)
		GPIO.setup(buzzerPin, GPIO.OUT)
		GPIO.setup(alarmLedPin, GPIO.OUT)
		
		self.heaterMode = 0		# Prewarm mode 
		self.heaterPWM = GPIO.PWM(heaterPin, 1)
		self.heaterPWM.start(0)
		self.pwmValue = 0
		self.setHeater()
		
		self.skinValid = 0
		self.skinTemp = 0
		self.servoSet = 36.0
				
		GPIO.output(heaterPin, self.heaterStatus)
		GPIO.output(lamp1Pin, self.lamp1Status)
		GPIO.output(lamp2Pin, self.lamp2Status)
		GPIO.output(buzzerPin, self.buzzerStatus)
		GPIO.output(alarmLedPin, self.alarmLedStatus)
		
		threading.Timer(0.1, self.updateSkin).start()
		threading.Timer(0.11, self.updateDatetime).start()
		
		
	def heaterTest(self):
		if(self.skinValid):
			self.heaterMode = (self.heaterMode+1)%3
		else:
			self.heaterMode = (self.heaterMode+1)%2
		self.setHeater()
		print("Heater Mode : " + str(self.heaterMode))
		print("Skin Valid  : " + str(self.skinValid))
		
		
	def heatUp(self):
		self.pwmValue = self.pwmValue + 5
		if(self.pwmValue>=100):
			self.pwmValue = 100
		self.heaterPWM.ChangeDutyCycle(self.pwmValue)
		self.label_5.setText(str(self.pwmValue)+"%")
		
	def heatDown(self):
		self.pwmValue = self.pwmValue - 5
		if(self.pwmValue<=0):
			self.pwmValue = 0
		self.heaterPWM.ChangeDutyCycle(self.pwmValue)
		self.label_5.setText(str(self.pwmValue)+"%")
		
	def setSkinUp(self):
		print("SET Up")
		self.servoSet = self.servoSet + 0.1
		if(self.servoSet >= 37):
			self.servoSet = 37.0
		self.label_7.setText(str(round(self.servoSet, 1)))
		
	def setSkinDown(self):
		print("SET Down")
		self.servoSet = self.servoSet - 0.1
		if(self.servoSet <= 30):
			self.servoSet = 30.0
		self.label_7.setText(str(round(self.servoSet, 1)))
		
	def lamp1Test(self):
		print("Lamp 1")
		self.lamp1Status = not(self.lamp1Status)
		GPIO.output(lamp1Pin, self.lamp1Status)
		
	def lamp2Test(self):
		print("Lamp 2")
		self.lamp2Status = not(self.lamp2Status)
		GPIO.output(lamp2Pin, self.lamp2Status)
		
	def buzzerTest(self):
		print("Buzzer")
		self.buzzerStatus = not(self.buzzerStatus)
		GPIO.output(buzzerPin, self.buzzerStatus)
		
	def alarmLedTest(self):
		print("Alarm Led")
		self.alarmLedStatus = not(self.alarmLedStatus)
		GPIO.output(alarmLedPin, self.alarmLedStatus)
		
	def updateSkin(self):
		#print("Skin Temp: " + str(skin_sensor.read()/100.0))
		self.skinTemp = skin_sensor.read()/100.0
		self.skinValid = skin_sensor.is_valid()
		if self.skinValid:
			print(str(round(self.skinTemp, 1)))
			textSkin = str(round(self.skinTemp, 1))
			self.label_2.setText(textSkin)
			if(self.heaterMode == 2):
				if(self.servoSet == self.skinTemp):
					self.pwmValue = 50
				if(self.servoSet > self.skinTemp):
					#print(self.servoSet-self.skinTemp)
					self.pwmValue = round(50 + (self.servoSet-self.skinTemp)*49)
				if(self.servoSet < self.skinTemp):
					#print(self.servoSet-self.skinTemp)
					self.pwmValue = round(50 - (self.skinTemp-self.servoSet)*49)
				if(self.pwmValue >= 100):
					self.pwmValue = 100
				if(self.pwmValue <= 0):
					self.pwmValue = 0
				self.label_5.setText(str(self.pwmValue)+"%")
				self.heaterPWM.ChangeDutyCycle(self.pwmValue)
		else:
			if skin_sensor.resistor<100:
				textSkin = "Skin Probe Error"
				self.label_2.setText(textSkin)
				if(self.heaterMode == 2):
					self.heaterMode = 0
					self.setHeater()
			else:
				textSkin = "Not Plugged"
				self.label_2.setText(textSkin)
				if(self.heaterMode == 2):
					self.heaterMode = 0
					self.setHeater()

				

		threading.Timer(1, self.updateSkin).start()
		
	def updateDatetime(self):
		dtString = datetime.now().strftime("  %H:%M:%S  %d/%m/%Y")
		self.label_3.setText(dtString)
		threading.Timer(1, self.updateDatetime).start()
		
	def setHeater(self):
		if(self.heaterMode == 0):	# Prewarm Mode
			self.pwmValue = 25
			self.label_5.setText(str(self.pwmValue)+"%")
			self.heaterPWM.ChangeDutyCycle(self.pwmValue)
			self.pushButton_3.setText("Prewarm")
			self.pushButton.setVisible(False)
			self.pushButton_2.setVisible(False)
			self.pushButton_4.setVisible(False)
			self.pushButton_5.setVisible(False)
			self.label_7.setVisible(False)
			self.label_8.setVisible(False)
		if(self.heaterMode == 1):
			self.pwmValue = 50
			self.label_5.setText(str(self.pwmValue)+"%")
			self.heaterPWM.ChangeDutyCycle(self.pwmValue)
			self.pushButton_3.setText("Manual")
			self.pushButton.setVisible(True)
			self.pushButton_2.setVisible(True)
			self.pushButton_4.setVisible(False)
			self.pushButton_5.setVisible(False)
			self.label_7.setVisible(False)
			self.label_8.setVisible(False)
		if(self.heaterMode == 2):
			self.servoSet = 36.0
			self.label_7.setText(str(round(self.servoSet, 1)))
			self.pushButton_3.setText("Servo")
			self.pushButton.setVisible(False)
			self.pushButton_2.setVisible(False)
			self.pushButton_4.setVisible(True)
			self.pushButton_5.setVisible(True)
			self.label_7.setVisible(True)
			self.label_8.setVisible(True)
		

if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication(sys.argv)
	MainWindow = mainProgram()
	MainWindow.show()
	sys.exit(app.exec_())
