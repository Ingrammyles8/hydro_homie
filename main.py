from machine import Pin, PWM, ADC, I2C
import ssd1306
import utime
import socket
import sys
import urequests
import wifi_fx
import json
import sht31

# initialize hydration sensor
i2c = I2C(sda=Pin(4), scl=Pin(5), freq = 100000)
sensor = sht31.SHT31(i2c, addr=0x44)

# initialize adc
adc = ADC(0)


Pin_TDS = machine.Pin(15, machine.Pin.OUT)
Pin_pH = machine.Pin(13, machine.Pin.OUT)
Pin_TDS.off()
Pin_pH.off()

def readTDS():
    Pin_pH.off()
    Pin_TDS.on()
    adcVal = adc.read()
    while adcVal == 0:
        adcVal = adc.read()
    print(adcVal)
    Voltage = adcVal * 5/1024
    tdsVal = (133.42/Voltage*Voltage*Voltage - 255.86*Voltage*Voltage + 857.39*Voltage)*0.5
    return tdsVal

def readpH():
    Pin_TDS.off()
    Pin_pH.on()
    adcVal = adc.read()
    while adcVal == 0:
        adcVal = adc.read()
    Voltage = adcVal * 5/1024
    return Voltage

wifi_fx.do_connect()

global message
message = ''
pre_rec = ''


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setblocking(False)
# adr = socket.getaddrinfo('127.0.0.1', 80)[0][-1]
adr = ('0.0.0.0', 80)
s.bind(adr)
s.listen(5)
s.settimeout(.5)

# location of bottle
response = urequests.get("http://ip-api.com/json/")
#print(response.json())
city = response.json()["city"]
state = response.json()["region"]
lat = response.json()["lat"]
lon = response.json()["lon"]
coordinates = (lat, lon)


baseline = ''
# from Mansour et al
stdev = 7.2

while True:
    try:
        (conn, address) = s.accept()
        print("successful connection")
        rec = conn.recv(4096).decode()
        print(rec)

        # connects bottle
        if "connect" in rec:
            conn.send('bottle connected\n'.encode())
            conn.close()

        utime.sleep(.5)
        #vals = sensor.get_temp_humi()
          #print("Temp = " + str(vals[0]) + ", Humidity = " + str(vals[1]))
          #print("TDS Value = " + str(readTDS()) + " ppm")
        #print("Voltage = " + str(readpH()))
        # gets turbidity
        if "turbidity" in rec:
            # calibrates
            for i in range(10):
                rec = readTDS()
                utime.sleep(.1)
            print(rec)
            #utime.sleep(.5)
            pre_rec = rec
            send = str(rec)
            conn.send(send.encode())
            conn.close()

        # get hydration
        elif "hydration" in rec:
            # calibrates
            prev = [0, 0]
            vals = sensor.get_temp_humi()
            while abs(prev[1] - vals[1]) > .01:
                print(abs(prev[1] - vals[1]))
                prev = vals
                vals = sensor.get_temp_humi()
            print(vals)
            temp = str(vals[0])
            humi = str(vals[1])
            # gets baseline hydration
            #print(baseline)
            if baseline == '':
                baseline = vals[1]
                send = "Calibrated"
                conn.send(send.encode())
                conn.close()
            # if greater than 1 stdev of baseline hydrated, if less semi-dehyrdrated,
            # if 2 less dehydrated
            if vals[1] >= (baseline - stdev):
                send = "Hydrated"
            elif vals[1] >= (baseline - 2*stdev) and vals[1] < (baseline - stdev):
                send = "Semi-Dehydrated"
            elif vals[1] < (baseline - 2*stdev):
                send = "Dehydrated"
            conn.send(send.encode())
            conn.close()

        # ph sensor
        elif "ph" in rec:
            for i in range(10):
                rec = readpH()
                utime.sleep(.5)
            pre_rec = rec
            send = str(rec)
            conn.send(send.encode())
            conn.close()

        else:
            utime.sleep(0.5)
            pre_rec = rec
            conn.send('Try again\n'.encode())
            conn.close()

    except OSError:
        pass
