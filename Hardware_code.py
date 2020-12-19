import requests
import numpy as np
import cv2
import pytesseract
import matplotlib.pyplot as plt
from PIL import Image
from time import sleep
from picamera import PiCamera
import RPi.GPIO as GPIO
camera = PiCamera()

URL_CHECK_CAR_OUT = 'https://api-smartparking.com/check-car-out'
URL_CHECK_CAR_IN = 'https://api-smartparking.com/check-car-in'
URL_CROP_IMAGE = 'http://40.114.78.122:5000/models/plate/predict'

def rasp_image():
    image = camera.capture('image.jpg')
    return image
def fomatstring(str):
  removeSpecialChars = str.translate ({ord(c): "" for c in " '!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
  return removeSpecialChars

def servo(pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin,GPIO.OUT)
    servo1 = GPIO.PWM(pin,50)
    servo1.start(2)
    servo1.ChangeDutyCycle(5)
    sleep(3)
    servo1.ChangeDutyCycle(2)
    sleep(0.5)
    servo1.ChangeDutyCycle(0)
    servo1.stop()
    GPIO.cleanup()
    
    
def sensor(pin):
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(pin, GPIO.IN)
  sensor = GPIO.input(pin)
  return sensor


def plate_to_text(imge_path):
  url = URL_CROP_IMAGE
  files = {'input_data': open(imge_path, 'rb')}
  r = requests.post(url, files=files)
  print("request success")
  left = r.json()['data']['bounding-boxes'][0]['coordinates']['left']
  right = r.json()['data']['bounding-boxes'][0]['coordinates']['right']
  top = r.json()['data']['bounding-boxes'][0]['coordinates']['top']
  bottom = r.json()['data']['bounding-boxes'][0]['coordinates']['bottom']
  img = cv2.imread(imge_path)
  crop_img = img[top:bottom, left:right]
  gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
  blur = cv2.GaussianBlur(gray, (3,3), 0)
  thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
  opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
  invert = 255 - opening

  return pytesseract.image_to_string(invert, lang='eng', config='--psm 6').strip()

def check_plate_in(plate_input):
  plate = {'plate': plate_input}
  r = requests.get(url = URL_CHECK_CAR_IN, json = plate)
  response = r.json()
  return response

def check_plate_out(plate_input):
  plate = {'plate': plate_input}
  r = requests.get(url = URL_CHECK_CAR_OUT, json = plate)
  response = r.json()
  return response
while True:
  try:
    if sensor(25) == 0:
      rasp_image()
      text = plate_to_text('image.jpg')
      text = fomatstring(text)
      print(text)
      if check_plate_in(text)['data']:
        servo(16)

    if sensor(22) == 0:
      rasp_image()
      text1 = plate_to_text('image.jpg')
      text1 = fomatstring(text1)
      print(text1)
      if check_plate_out(text1)['data']:
        servo(23)
  except:
    print("exception")




