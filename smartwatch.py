# Microcontroller Flash HUZZAH
# Using MicroPython

from machine import Pin, PWM, ADC, RTC, I2C
import network
import utime, time
import ssd1306
import ntptime # synchronize with ntp
import urequests, ujson
import uasyncio

# Initialize LED
led = Pin(2, Pin.OUT) # built-in LED
led.value(0) # reset

# Initialize ADC
adc = ADC(0)

# Initialize RTC
rtc = RTC()
dttuple = (2017, 8, 23, 1, 12, 48, 8, 138) # default date and time
rtc.datetime(dttuple)

# Initialize I2C
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
display = ssd1306.SSD1306_I2C(128, 32, i2c)
display.contrast(10)

# Initialize Buttons
buttonA = Pin(12, Pin.IN, Pin.PULL_UP)  # 1 for NOT pressed
buttonB = Pin(13, Pin.IN, Pin.PULL_UP)  # 1 for NOT pressed
buttonC = Pin(14, Pin.IN, Pin.PULL_UP)  # 1 for NOT pressed

pos = [6, 5, 4]
pos_name = ["seconds", "minutes", "hours"]
current = 0
mode = 0
alarm = [1,30,0]
led_true = 0
led_count = 0

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        #wlan.connect('Columbia University', '')
        wlan.connect('ihnyc-guest', 'morningside')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

def current_location():
	ip_geo_data = urequests.get('http://ip-api.com/json/?fields=city,region,lat,lon')
	return ip_geo_data.json()

def current_weather(lat, lon):
	api_key = "a99d5ef0819b018dd6bdd2b23e53f736"
	url = "https://api.openweathermap.org/data/2.5/weather?lat={0}&lon={1}&appid={2}&units=imperial".format(lat, lon, api_key)
	current_weather_data = urequests.get(url)
	return current_weather_data.json()

def post_tweet():
	api_key = "b5VkNvqa5E_odX5UIEah9j"
	url = "https://maker.ifttt.com/trigger/Watch_Tweeted/with/key/{0}?value1={1}&value2={2}&value3={3}".format(api_key, str(weather_data), weather_string, city_data.replace(" ", "_"))
	urequests.post(url)

display.fill(1)
display.text("Welcome World", 0, 10, 0)
display.show()

utime.sleep(1)
display.fill(0)
display.text("Connecting to", 0, 5, 1)
display.text("WiFi ...", 0, 15, 1)
display.show()

# Connect to WiFi
do_connect()
display.text("SUCCESS!", 0, 25, 1)

utime.sleep(1)
display.fill(0)
display.text("Getting Time,", 0, 0, 1)
display.show()

# Get Time
ntptime.settime() # set the rtc datetime from the remote server in UTC
current_time_list = list(rtc.datetime())
if current_time_list[4] >= 4:
	current_time_list[4] = current_time_list[4] - 4
else:
	current_time_list[4] = 24 + current_time_list[4] - 4
rtc.datetime(tuple(current_time_list))
time_string = str(current_time_list[4]) + " : " + str(current_time_list[5]) + " : " + str(current_time_list[6])
print("Time: " + time_string)

display.text("Location,", 0, 10, 1)
display.show()

# Get Location
ip_geo_data = current_location()
lat_string = ("Lat: " + str(ip_geo_data['lat']))
lon_string = ("Lon: " + str(ip_geo_data['lon']))
city_data = str(ip_geo_data['city'])
city_string = (city_data + ", " + str(ip_geo_data['region']))
print("Location: " + city_string)

display.text("& Weather", 0, 20, 1)
display.show()

# Get Weather
current_weather_data = current_weather(ip_geo_data['lat'], ip_geo_data['lon'])
weather_data = current_weather_data['main']['temp']
weather_string = current_weather_data['weather'][0]['main']
weather_description = current_weather_data['weather'][0]['description']
print("Current Weather: " + str(weather_data) + " °F - " + weather_string)

# Post Tweet
tweet_string = ("It is " + str(weather_data) + " *F and " + weather_description + " in " + city_data + " at " + time_string)
print(tweet_string)
post_tweet()

display.fill(0)
display.text(city_string, 0, 0, 1)
display.text(time_string, 0, 10, 1)
display.text(str(weather_data), 0, 20, 1)
display.text("*F", 50, 20, 1)
display.text(weather_string, 70, 20, 1)
display.show()

utime.sleep(7)

def debouncing(current_button_value, button_value_num):
	i=0
	while i<5:
		if button_value_num == 'A':
			if(current_button_value == (not buttonA.value())):
				i=i+1
			else:
				i=0
		elif button_value_num == 'B':
			if(current_button_value != (not buttonB.value())):
				i=i+1
			else:
				i=0
		elif button_value_num == 'C':
			if(current_button_value != (not buttonC.value())):
				i=i+1
			else:
				i=0
		utime.sleep_ms(10)

def interrupt_handlerA(buttonA):
	current_button_value = (not buttonA.value())
	debouncing(current_button_value, 'A')
	
	global current_time_list, pos_name, current, mode, pos # access global variable to update globally

	if mode == 0:
		current = (current + 1) % 3 # values stay 0, 1, 2
		display.text(pos_name[current], 80, 0)
		display.show()
	elif mode == 1:
		current = (current + 1) % 3
		display.text(pos_name[current], 80, 0)
		display.show()

def interrupt_handlerB(buttonB):
	current_button_value = (not buttonB.value())
	debouncing(current_button_value, 'B')

	global current_time_list, pos_name, current, mode, pos # access global variable to update globally
	
	if mode == 0:
		current_time_list = list(rtc.datetime())
		current_time_list[pos[current]] += 1
		rtc.datetime(tuple(current_time_list))
		print(current_time_list)
	elif mode == 1:
		alarm[current] += 1

def interrupt_handlerC(buttonC):
	current_button_value = (not buttonC.value())
	debouncing(current_button_value, 'C')

	global current_time_list, mode # access global variable to update globally

	mode = 1 - mode # If 0, becomes 1. If 1, becomes 0
	mode_name = ['clock', 'alarm']
	display.text(mode_name[mode], 80, 20)
	display.show()

while True:
	# OLED Brightness
	brightness = adc.read() # Brightness scale is 0 to 1023
	contr = (int)(brightness/4) # Contrast scale is 255 (roughly one-fourth)
	display.contrast(contr)

	current_time_list = list(rtc.datetime())

	buttonA.irq(trigger=Pin.IRQ_FALLING, handler=interrupt_handlerA)
	buttonB.irq(trigger=Pin.IRQ_FALLING, handler=interrupt_handlerB)
	buttonC.irq(trigger=Pin.IRQ_FALLING, handler=interrupt_handlerC)

	rtc_string = str(current_time_list[4]) + " " + str(current_time_list[5]) + " " + str(current_time_list[6])
	alarm_string = str(alarm[2]) + " " + str(alarm[1]) + " " + str(alarm[0])
	display.fill(0)
	display.text(rtc_string, 0, 0, 1)
	display.text(alarm_string, 0, 15, 1)
	display.show()

	if current_time_list[4] == alarm[2] and current_time_list[5] == alarm[1] and current_time_list[6] == alarm[0]:
		led_true = 1
		led_count = 0
	
	if led_true == 1:
		print("Alarm ring")
		bright = PWM(led, freq=1000, duty=900)
		led_count += 1
		print(led_count)

	if led_count >= 10:
		print('off')
		dim = PWM(led, freq=1, duty=0)
		led_true = 0
		led_count = 0
		print(led_count)

	utime.sleep(0.5)