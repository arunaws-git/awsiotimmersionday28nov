import time as t
import datetime
import json
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
import board
import adafruit_dht
import config

# Define ENDPOINT, CLIENT_ID, PATH_TO_CERTIFICATE, PATH_TO_PRIVATE_KEY, PATH_TO_AMAZON_ROOT_CA_1, MESSAGE, TOPIC, and RANGE
ENDPOINT = config.MQTT_HOST
CLIENT_ID = config.THING_ID
PATH_TO_CERTIFICATE = config.THING_CLIENT_CERT
PATH_TO_PRIVATE_KEY = config.THING_PRIVATE_KEY
PATH_TO_AMAZON_ROOT_CA_1 = config.THING_ROOT_CA
TOPIC = "clients/" + CLIENT_ID + "/temp_humid"

dhtDevice = adafruit_dht.DHT22(board.D4, use_pulseio=False)
class dht22reading:
    temprature_c=0.0
    humidity=0.0

def read_dht22sensorvalues():
    try:
       
        dht22reading.temperature_c = dhtDevice.temperature        
        dht22reading.humidity = dhtDevice.humidity
        return dht22reading
    
    except RuntimeError as error:
        # dht is delicate often drops the port, but will pick up on its own in less than a second; so suppress and move on with it
        print(error.args[0])
        t.sleep(2.0)
    
    except Exception as error:
        dhtDevice.exit()
        raise error
    except KeyboardInterrupt:
        dhtDevice.exit()
        print('exiting script')


myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(CLIENT_ID)
myAWSIoTMQTTClient.configureEndpoint(ENDPOINT, 8883)
myAWSIoTMQTTClient.configureCredentials(PATH_TO_AMAZON_ROOT_CA_1, PATH_TO_PRIVATE_KEY, PATH_TO_CERTIFICATE)

myAWSIoTMQTTClient.connect()
print('Begin Publish')
while True:
    try:
        readings=read_dht22sensorvalues()
        
        temp = readings.temprature_c
        hum = readings.humidity
            
        message = json.dumps({
                "client": CLIENT_ID,
                "timestamp": str(datetime.datetime.utcnow())
                "sensors": {
                    "temperature": temp,
                    "humidity": hum,
                },
                "status": "online"
            })
        
        myAWSIoTMQTTClient.publish(TOPIC, json.dumps(message), 1) 
        print("Published: '" + json.dumps(message) + "' to the topic: " + TOPIC)
    
        t.sleep(1)
    except AttributeError:
        continue
    except RuntimeError:
        t.sleep(2.0)
    except OSError as e:
        print("RECONNECT TO MQTT BROKER")
        break

print('Publish End')
myAWSIoTMQTTClient.disconnect()