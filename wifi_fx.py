import network

print("in wifi_fx")

ip = ''

def do_connect():
    global ip
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('Columbia University', '')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    ip += wlan.ifconfig()[0]
    print(ip)
