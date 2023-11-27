print('Main.py -> Start')
import config
import sys
import os
import time
import random
import ujson
import machine
import board
import adafruit_dht
from umqtt.simple import MQTTClient

dhtDevice = adafruit_dht.DHT22(board.D4, use_pulseio=False)
class dht22reading:
    temprature_c=0.0
    humidity=0.0

def read_dht22sensorvalues():
    try:
        # Print the values to the serial port
        dht22reading.temperature_c = dhtDevice.temperature        
        dht22reading.humidity = dhtDevice.humidity
        return dht22reading
    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        time.sleep(2.0)
    except Exception as error:
        dhtDevice.exit()
        raise error
    except KeyboardInterrupt:
        dhtDevice.exit()
        print('exiting script')

print('Main.py -> Init')
info = os.uname()
with open("/flash/" + config.THING_PRIVATE_KEY, 'r') as f:
    key = f.read()
with open("/flash/" + config.THING_CLIENT_CERT, 'r') as f:
    cert = f.read()
client_id = config.THING_ID
topic_pub = "clients/" + client_id + "/hello/world"
topic_sub = "clients/" + client_id + "/hello/world"
aws_endpoint = config.MQTT_HOST
ssl_params = {"key":key, "cert":cert, "server_side":False}

def mqtt_connect(client=client_id, endpoint=aws_endpoint, sslp=ssl_params):
    print("CONNECTING TO MQTT BROKER...")
    mqtt = MQTTClient(
        client_id=client,
        server=endpoint,
        port=8883,
        keepalive=4000,
        ssl=True,
        ssl_params=sslp)
    try:
        mqtt.connect()
        print("MQTT BROKER CONNECTION SUCCESSFUL")
    except Exception as e:
        print("MQTT CONNECTION FAILED: {}".format(e))
        sys.exit()
    return mqtt

def mqtt_publish(client, topic=topic_pub, message='{"message": "dht22"}'):
    client.publish(topic, message)
    print("PUBLISHING MESSAGE: {} TO TOPIC: {}".format(message, topic))

def mqtt_subscribe(topic, message):
    message = ujson.loads(message)
    print("RECEIVING MESSAGE: {} FROM TOPIC: {}".format(message, topic))

print('Main.py -> Setup')
mqtt = mqtt_connect()
mqtt.set_callback(mqtt_subscribe)
mqtt.subscribe(topic_sub)

print('Main.py -> Loop')
while True:
    try:
        mqtt.check_msg()
        readings=read_dht22sensorvalues()
        
        temp = readings.temprature_c
        hum = readings.humidity
        temp_f = temp * (9/5) + 32.0
        msg = ujson.dumps({
            "client": client_id,
            "device": {
                "uptime": time.ticks_ms(),
                "hardware": info[0],
                "firmware": info[2]
            },
            "sensors": {
                "temperature": temp_f,
                "humidity": hum,
            },
            "status": "online",
        })
        mqtt_publish(client=mqtt, message=msg)
        time.sleep(2)
    except OSError as e:
        print("RECONNECT TO MQTT BROKER")
        mqtt = mqtt_connect()
        mqtt.set_callback(mqtt_subscribe)
        mqtt.subscribe(topic_sub)
    except Exception as e:
        print("A GENERAL ERROR HAS OCCURRED: {}".format(e))
        sys.exit()
