from kivy.config import Config
Config.set('graphics', 'width', '600')
Config.set('graphics', 'height', '500')


from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from kivy.uix.label import Label
from kivy.network.urlrequest import UrlRequest
from kivy_garden.mapview import MapView
from kivy_garden.mapview import MapMarker, MapMarkerPopup, MapLayer, MarkerMapLayer
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window


from plyer import tts

import speech_recognition as sr

import socket
import sys
import requests
import pandas as pd
from scipy.spatial import distance
import numpy as np
from sodapy import Socrata
import json
import pathlib as pl
import time




# import coordinates for sample sites
site_coords = pd.read_csv("water_sample_coordinates.csv")
site_coords["coordinates"] = list(zip(site_coords["Latitude"], site_coords["Longitude"]))

# location 
response = requests.get("http://ip-api.com/json/")
#print(response.json())
city = response.json()["city"]
state = response.json()["region"]
lat = response.json()["lat"]
lon = response.json()["lon"]
coordinates = (lat, lon)


# Level of lead/copper in water, location of water treatment facility, type of water
#response = requests.get("https://enviro.epa.gov/enviro/efservice/counties_served/Otsego/JSON")
#print(response.json())


# Drinking water tested at certain sites for flouride level, turbidity, chlorine,
# coliform, and e coli

response_2 = requests.get("https://data.cityofnewyork.us/resource/bkwf-xfky.json?sample_date=2021-10-01T00:00:00.000", stream=True)
results_df = pd.DataFrame.from_records(response_2.json())
print(results_df)
# =============================================================================
# client = Socrata("data.cityofnewyork.us", None)
# results = client.get("bkwf-xfky", limit=5000)
# results_df = pd.DataFrame.from_records(results)
# print(results_df.columns)
# =============================================================================
 #location of water fountain
response3 = requests.get("https://data.cityofnewyork.us/resource/bevm-apmm.json", stream=True)
water_fountain = pd.DataFrame(response3.json())
water_fountain["coordinates"] = water_fountain["the_geom"].apply(
                                    lambda x: (x["coordinates"][1]
                                    ,x["coordinates"][0]))


# finds the closest fountain to coordinate
def closest_ftn(coord, ftn_df, x):
    # get indices of x nearest ftns
    ftn_locs = list(ftn_df["coordinates"].values)
    closest_ftns = np.array(np.argpartition(distance.cdist([coord], ftn_locs), x))[0][:x]
    ftn_coords = [ftn_locs[i] for i in closest_ftns]
    ftn_names= [ftn_df[ftn_df["coordinates"] == i]["signname"].values[0] for i in ftn_coords]
    return ftn_names, ftn_coords

# finds closest site to the give coordinate
def closest_site(coord, ftn_df, x):
    # get indices of x nearest ftns
    ftn_locs = list(ftn_df["coordinates"].values)
    closest_ftns = np.array(np.argpartition(distance.cdist([coord], ftn_locs), x))[0][:x]
    ftn_coords = [ftn_locs[i] for i in closest_ftns]
    ftn_names= [ftn_df[ftn_df["coordinates"] == i]["ID"].values[0] for i in ftn_coords]
    return ftn_names, ftn_coords

# gets the water quality for the given coordinate
def get_water_qual(coord, results_df):
    # gets water quality info from nearest tested fountain
    sites_new = site_coords[site_coords["ID"].isin(results_df["sample_site"].values)]
    ftn_locs = list(sites_new["coordinates"].values)
    closest_ftn = np.array(np.argpartition(distance.cdist([coord], ftn_locs), 1))[0][0]
    ftn_coords = ftn_locs[closest_ftn]
    #print(ftn_coords)
    ftn_name = site_coords[site_coords["coordinates"] == ftn_coords]["ID"].values[0]
    #print(ftn_name)
    ftn_info = results_df[results_df["sample_site"] == ftn_name]
    print(ftn_info)
    return ftn_info
    


r = sr.Recognizer()
m = sr.Microphone()

ip = "209.2.222.11"

# detect if bottle is connected
conn = False

# class for the labels of the fountains
class MyLabel(Label):
    def on_size(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 1, 1, 0.25)
            Rectangle(pos=(-60,0), size=(250, 100))

# =============================================================================
# def send_message(value, label):
#     # send message to huzzah to change the specified label
#     label = label
#     try:
#         
#         # Send data
#         message = value + '\n'
#                     
#         sock.send(message.encode())
#                     #if "tweet" in old_value:
#                     #    status = "Status update: {0}".format(value.replace("tweet ", ""))
#                     #    tweet = requests.post("https://api.thingspeak.com/apps/thingtweet/1/statuses/update?apikey=ZV57S1TFIHVN1VKC&status={0}".format(
#                     #                            status))
#     
#         response = sock.recv(2048)
#         print(response.decode())
#         label = response.decode()
#     
#     except:
#         label = "error"
#         print("error")
# =============================================================================
        
# class that handles the movement between screens
class WindowManager(ScreenManager):
    pass

# the screen with all the water information
class WaterScreen(Screen):
    
    # connects bottle to app
    def connect_bottle(self):
        # connects and disconnects bottle
        print(self.ids.bottle_conn.text)
        self.ids.conn.color = (1,1,1,1)
        # finds bottle if not connected
        if self.ids.bottle_conn.text == "Connect Bottle":
            
            self.ids.bottle_conn.text = "Finding Bottle.."
            time.sleep(1)
            #global sock
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (ip, 80)
            sock.connect(server_address)
            
            try:
                
                message = "connect" + "\n"
                sock.send(message.encode())
                
                response = sock.recv(2048)
                print(response.decode())
                self.ids.bottle_conn.text = "Disconnect Bottle"
                self.ids.conn.text = "Bottle Connected"
                global conn
                conn = True
                
            except:
                print("error")
                self.ids.bottle_conn.text = "No Bottle Found"
                time.sleep(1)
                self.ids.bottle_conn.text = "Connect Bottle"
        
        # disconnects connected bottle  
        elif self.ids.bottle_conn.text == "Disconnect Bottle":
            conn = False
            self.ids.bottle_conn.text = "Connect Bottle"
            self.ids.conn.text = "No Bottle Connected"
            self.ids.hyd.text = "Calibrate"
            self.ids.pH.text = ""
            self.ids.tbd.text = ""
            self.ids.chl.text = ""
            self.ids.bottle_tbd.text= ""
            
            

    # gets the turbidity of both the bottle and the nearest water source
    def get_tbd(self):
        
        if conn != True:
            self.ids.conn.color = (1,1,1,1)
            self.ids.conn.text = "Please Connect Bottle"
        # get the turbidity of the bottle water and outside water
        
        # change into function
        #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.ids.bottle_tbd.text = "Calb."
            #Connect the socket to the port where the server is listening
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (ip, 80)
            sock.connect(server_address)
            
            
            try:
            
                # Send data
                message = "turbidity" + '\n'
                        
                sock.send(message.encode())
                        #if "tweet" in old_value:
                        #    status = "Status update: {0}".format(value.replace("tweet ", ""))
                        #    tweet = requests.post("https://api.thingspeak.com/apps/thingtweet/1/statuses/update?apikey=ZV57S1TFIHVN1VKC&status={0}".format(
                        #                            status))
        
                response = sock.recv(2048)
                print(response.decode())
                bottle_tbd = response.decode()
                self.ids.bottle_tbd.text = str(response.decode())
                
                
        
            except:
                self.ids.bottle_tbd.text = "error"
                print("error")
            tbd = round(float(get_water_qual(coordinates, 
                                                results_df).iloc[:, 6].values[0])/3, 2)*1000
            self.ids.tbd.text = str(round(float(get_water_qual(coordinates, 
                                                    results_df).iloc[:, 6].values[0])/3, 2)*1000)
                
            diff = round(abs(tbd - float(bottle_tbd)), 2)
            self.ids.conn.color = (1,1,1,1)
            # returns comparison
            if float(tbd) > float(bottle_tbd):
                self.ids.conn.text = "Your water is clearer than the surrounding water by {0} ppm".format(diff)
            elif float(tbd) < float(bottle_tbd):
                self.ids.conn.text = "The surrounding water is clearer than your water by {0} ppm. \n Go to the nearest fountain".format(diff)
            else:
                self.ids.conn.text = "Your water is comparable to the surrounding water"
            
           
        
    def get_ph(self):
        # get pH level of bottle water
        self.ids.conn.color = (1,1,1,1)

        if conn != True:
            self.ids.conn.text = "Please Connect Bottle"
        else:
            self.ids.pH.text = "Calibrating"
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (ip, 80)
            sock.connect(server_address)
            
            
            try:
            
                # Send data
                message = "ph" + '\n'
                        
                sock.send(message.encode())
                        #if "tweet" in old_value:
                        #    status = "Status update: {0}".format(value.replace("tweet ", ""))
                        #    tweet = requests.post("https://api.thingspeak.com/apps/thingtweet/1/statuses/update?apikey=ZV57S1TFIHVN1VKC&status={0}".format(
                        #                            status))
        
                response = sock.recv(2048)
                print(response.decode())
                self.ids.pH.text = str(response.decode())
                ph = str(response.decode())
                if float(ph) < 3:
                    self.ids.conn.text = "Your water has a pH of " + ph + ". Don't drink that!"
                else:
                     self.ids.conn.text = "Your water has a pH of " + ph
        
            except:
                self.ids.pH.text = "error"
                print("error")
                
    
    def get_chl(self):
        # get chl level of nearest water source
        
        self.ids.chl.text = str(get_water_qual(coordinates, 
                                results_df).iloc[:, 5].values[0])
        chl = str(get_water_qual(coordinates, 
                                results_df).iloc[:, 5].values[0])
        
        self.ids.conn.text = "The nearest water source has a chlorine level of " + chl + "mgL"
        
    
    def get_hydration(self):
        # get hydration level of the user
        self.ids.conn.color = (1,1,1,1)
        if conn != True:
            self.ids.conn.text = "Please Connect Bottle"
        else:
            self.ids.hyd.text = "Calibrating"
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (ip, 80)
            sock.connect(server_address)
            
            
            try:
            
                # Send data
                message = "hydration" + '\n'
                        
                sock.send(message.encode())
                        #if "tweet" in old_value:
                        #    status = "Status update: {0}".format(value.replace("tweet ", ""))
                        #    tweet = requests.post("https://api.thingspeak.com/apps/thingtweet/1/statuses/update?apikey=ZV57S1TFIHVN1VKC&status={0}".format(
                        #                            status))
        
                response = sock.recv(2048)
                
                # returns hydration level
                self.ids.hyd.text = str(response.decode())
                if str(response.decode()) == "Calibrated":
                    self.ids.conn.text = "Hydration Sensor Calibrated"
                elif str(response.decode()) == "Hydrated":
                    self.ids.conn.text = "You are hydrated!"
                    self.ids.conn.color = (0, 1, 1, 1)
                elif str(response.decode()) == "Semi-Dehydrated":
                    self.ids.conn.text = "Drink more water"
                    self.ids.conn.color = (1, 1, 0, 1)
                elif str(response.decode()) == "Dehydrated":
                    self.ids.conn.text = "Drink a lot more water"
                    self.ids.conn.color = (1, 0, 0, 1)
                print(response.decode())
                
        
            except:
                self.ids.hyd.text = "error"
                print("error")
        
    
    def record(self):
        # GUI Blocking Audio Capture
        self.ids.conn.color = (1,1,1,1)
        if conn != True:
            self.ids.conn.text = "Please Connect Bottle"
        else:
            with m as source:
                tts.speak("Recording")
                audio = r.record(source, duration=4)
                tts.speak("Got it")
                    
            try:
                # recognize speech using Google Speech Recognition
                def got_json(req, result):
                    for key, value in req.resp_headers.items():
                        print('{}: {}'.format(key, value))
                    
                value = r.recognize_google(audio)
                self.output = "You said \"{}\"".format(value)
                tts.speak("You said \"{}\"".format(value))
                print(value)
                    
                #does chlorine and turbidity check and speaks the result
                
                if "chlorine" in value:
                    chl = str(get_water_qual(coordinates, 
                                            results_df).iloc[:, 5].values[0])
                    self.ids.chl.text = chl
                    tts.speak("The nearest water source has a chlorine level of " + chl + "milligrams per liter")
                
                elif "turbidity" in value:
                    
                    tbd = round(float(get_water_qual(coordinates, 
                                                    results_df).iloc[:, 6].values[0])/3, 2)*1000
                    
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_address = (ip, 80)
                    sock.connect(server_address)
            
            
                    try:
            
                        # Send data
                        message = "turbidity" + '\n'
                                
                        sock.send(message.encode())
                                #if "tweet" in old_value:
                                #    status = "Status update: {0}".format(value.replace("tweet ", ""))
                                #    tweet = requests.post("https://api.thingspeak.com/apps/thingtweet/1/statuses/update?apikey=ZV57S1TFIHVN1VKC&status={0}".format(
                                #                            status))
                
                        response = sock.recv(2048)
                        print(response.decode())
                        bottle_tbd = float(response.decode())
        
                    except:
                        self.ids.bottle_tbd.text = "error"
                        print("error")
                    
                    self.ids.tbd.text = str(tbd)
                    self.ids.bottle_tbd.text = str(bottle_tbd)
                    
                    diff = round(abs(tbd - bottle_tbd), 2)
                    if float(tbd) > float(bottle_tbd):
                        self.ids.conn.text = "Your water is clearer than the surrounding water by {0} ppm".format(diff)
                        tts.speak("Your water is clearer than the surrounding water by {0} ppm".format(diff))
                        

                    elif float(tbd) < float(bottle_tbd):
                        self.ids.conn.text = "The surrounding water is clearer than your water by {0} ppm. \n Go to the nearest fountain".format(diff)
                        tts.speak("The surrounding water is clearer than your water by {0} ppm. \n Go to the nearest fountain".format(diff))
                        
                    else:
                        self.ids.conn.text = "Your water is comparable to the surrounding water"
                        tts.speak("Your water is comparable to the surrounding water")
                        
                
    # =============================================================================
                elif "PH" in value:
                     
                     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                     server_address = (ip, 80)
                     sock.connect(server_address)
             
                     try:
             
                         # Send data
                         message = "ph" + '\n'
                                 
                         sock.send(message.encode())
                                 #if "tweet" in old_value:
#                                     status = "Status update: {0}".format(value.replace("tweet ", ""))
#                                     tweet = requests.post("https://api.thingspeak.com/apps/thingtweet/1/statuses/update?apikey=ZV57S1TFIHVN1VKC&status={0}".format(
#                                                             status))
                 
                         response = sock.recv(2048)
                         print(response.decode())
                         self.ids.pH.text = str(response.decode())
                         ph = str(response.decode())
                         
         
                     except:
                         self.ids.pH.text = "error"
                         print("error")
                     
                     tts.speak("Your water has a pH of " + ph + ". Don't drink that!")
    # =============================================================================
                          
                    
                    
            except sr.UnknownValueError:
                self.output = ("Didn't quite catch that")
                tts.speak("Didn't quite catch that")
                    
            except sr.RequestError as e:
                self.output = ("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
                tts.speak("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
            
          
cur_lat = lat
cur_lon = lon
        

class MapScreen(Screen):
    
    # current latitude and longitude
    cur_lat = lat
    cur_lon = lon
    
    # adds the fountains to the map
    def get_water_ftns(self):
        ftns = closest_ftn(coordinates, water_fountain, 20)
        loc = ftns[0]
        coords = ftns[1]
        ind = 0
        for i in range(len(coords)):
            #print(coord)
            marker = MapMarkerPopup(lat=coords[i][0], lon=coords[i][1], source="water_marker.png")
            tbd = str(round(float(get_water_qual(coords[i], results_df).iloc[:, 6].values[0])/3, 2)*1000)
            chl = get_water_qual(coords[i], results_df).iloc[:, 5].values[0]
            label = MyLabel(
                    text = loc[i] + "\nTBD: " + tbd + "ppm" + "\nChl: " + chl + "mg/l",
                    color = [0,0,0,1]
                    #pos = (20,20),
                    #size_hint=(0.5, 0.5),
                    )
            marker.add_widget(label)
            self.ids.mapview.add_marker(marker)
            ind += 1
        
        
        
# =============================================================================
#     def clear_water_ftns(self):
#         self.parent.current = "water_screen"
# =============================================================================
            
    
# =============================================================================
#     def record(self):
#         # GUI Blocking Audio Capture
#         with m as source:
#             tts.speak("Recording")
#             audio = r.record(source, duration=4)
#             tts.speak("Got it")
#                 
#         try:
#             # recognize speech using Google Speech Recognition
#             def got_json(req, result):
#                 for key, value in req.resp_headers.items():
#                     print('{}: {}'.format(key, value))
#                 
#             value = r.recognize_google(audio)
#             self.output = "You said \"{}\"".format(value)
#             tts.speak("You said \"{}\"".format(value))
#             print(value)
#                 
#             # makes the url post with req_body
#             # Create a TCP/IP socket
#             
#             if "chlorine" in value:
#                 chl = str(get_water_qual(coordinates, 
#                                         results_df).iloc[:, 5].values[0])
#                 self.ids.chl.text = chl
#                 tts.speak("The nearest water source has a chlorine level of " + chl + "milligrams per liter")
#             
#             elif "turbidity" in value:
#                 
#                 self.ids.tbd.text = str(get_water_qual(coordinates, 
#                                         results_df).iloc[:, 6].values[0])
#                 
#                 send_message("tbd", self.ids.bottle_tbd.text)
#                 tts.speak("The nearest water source has a chlorine level of " + chl + "milligrams per liter")
#             
#             elif "ph" in value:
#                 
#                 send_message("ph", self.ids.pH.text)
#                 
#             elif "hydration" in value:
#                 
#                 send_message("hydration", self.ids.hyd.text)
#         
#         except:
#             print("error")
# =============================================================================
            
    
    

    

Builder.unload_file("main.kv")
Builder.load_file("main.kv")



class Hydro_Homie(App):

    def build(self):
        # Calibrate the Microphone to Silent Levels
        print("A moment of silence, please...")
        with m as source:
            r.adjust_for_ambient_noise(source)
            print("Set minimum energy threshold to {}".format(r.energy_threshold))
        # Create a root widget object and return as root
            
# =============================================================================
#         tb = TabbedPanel()
#         tb.default_tab_text = "Water Bottle"
#         #tb.add_widget(self.sub_label)
#         tb.content= (Label(text = "Command Status"),
#                      Button(text="Record", background_color=[0,1,0,1]))
#         #tb.add_widget(self.record_button)
#         #tb.record_button.bind(on_press=self.record)
#         
#         th = TabbedPanelHeader(text = "Map")
#         
#         th.content = MapView(zoom=11, lat=50.6394, lon=3.057)
#         
#         tb.add_widget(th)
# =============================================================================
    
# =============================================================================
#         
#         def record(self, event):
#     
#             output = StringProperty('')
#             # GUI Blocking Audio Capture
#             with m as source:
#                 tts.speak("Recording for 5 seconds")
#                 audio = r.record(source, duration=5)
#                 
#             try:
#                     # recognize speech using Google Speech Recognition
#                 def got_json(req, result):
#                     for key, value in req.resp_headers.items():
#                         print('{}: {}'.format(key, value))
#                 
#                 value = r.recognize_google(audio)
#                 self.output = "You said \"{}\"".format(value)
#                 tts.speak("You said \"{}\"".format(value))
#                 self.main_label.text = value
#                 print(value)
#                 headers = {'Content-Type': "application/json;charset-UTF-8"}
#                 # makes the url post with req_body
#                 # Create a TCP/IP socket
#                 sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     
#                 # Connect the socket to the port where the server is listening
#                 server_address = ('209.2.223.203', 80)
#                 sock.connect(server_address)
#                 if "fountain" in value:
#                     coords = str(closest_ftn(coordinates, water_fountain, 1)[1][0])
#                     value = value + "," + coords
#                 elif "quality" in value:
#                     chl = str(get_water_qual(coordinates,
#                             results_df).iloc[:, 5:8].values[0][0])
#                     turb = str(get_water_qual(coordinates,
#                             results_df).iloc[:, 5:8].values[0][1])
#                     value = value + "," + chl + "," + turb
#     
#                 try:
#         
#                         # Send data
#                     message = value + '\n'
#                     
#                         
#                     sock.send(message.encode())
#                     #if "tweet" in old_value:
#                     #    status = "Status update: {0}".format(value.replace("tweet ", ""))
#                     #    tweet = requests.post("https://api.thingspeak.com/apps/thingtweet/1/statuses/update?apikey=ZV57S1TFIHVN1VKC&status={0}".format(
#                     #                            status))
#     
#                     response = sock.recv(2048)
#                     print(response.decode())
#                     self.sub_label.text = response.decode()
#     
#                 except:
#                     print("error")
#                     self.sub_label.text = "error"
#                 
#                 
#                 self.record_button.text = "Record"
#                 self.record_button.background_color = [0,1,0,1]
#                 
#                 
#             except sr.UnknownValueError:
#                 self.output = ("Didn't quite catch that")
#                 tts.speak("Didn't quite catch that")
#                 
#             except sr.RequestError as e:
#                 self.output = ("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
#                 tts.speak("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
# =============================================================================
                

        return WindowManager()



# Run the kivy app

if __name__ == '__main__':

     Hydro_Homie().run()
