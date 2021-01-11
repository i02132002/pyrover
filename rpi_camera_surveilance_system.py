# Web streaming example
# Source code from the official PiCamera package
# http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming

import io
import picamera
import logging
import socketserver
import pigpio
from threading import Condition
from http import server
from time import sleep
import RPi.GPIO as GPIO
import sys

PAGE="""\
<!DOCTYPE html>
<html>
<head>

    <script>
        function send(theUrl)
        {
            var xmlHttp = new XMLHttpRequest();
            xmlHttp.open( "GET", theUrl, false);
            xmlHttp.send( null );
            
            return xmlHttp.responseText;
            
        }

    </script>
    
    <style>
        body {
            background-color: lightblue;
        }

        h1 {
            color: navy;
            margin-left: 20px;
        }

        button {
            width: 40px;
            height: 40px;
        }
    </style>
</head>

<body>
    <center><img src="stream.mjpg" width="640" height="480"></center>
    <center>
        <div id = "container" style="width:600px">
            <div id ="camera_control" style="width:300px; float:left;" >
                <center><h3>Camera rotation</h3></center>
                <center>
                    <div>
                        <button type="button" id="up" onclick="send('http://127.0.0.1:8000/up')">&uarr;</button>
                    </div>
                    <div>
                        <center>
                            <button type="button" id="left" onclick="send('http://127.0.0.1:8000/left')">&larr;</button>
                            <button type="button" id="center" onclick="send('http://127.0.0.1:8000/center')">&squ;</button>
                            <button type="button" id="right" onclick="send('http://127.0.0.1:8000/right')">&rarr;</button>
                        </center>
                    </div>
                    <div>
                        <button type="button" id="down" onclick="send('http://127.0.0.1:8000/down')">&darr;</button>
                    </div>
                </center>
            </div>
            <div id ="motor_control" style="width:300px; float:right;">
                <center><h3>Motor control</h3></center>
                <center>
                    <div>
                        <button type="button" id="motor_fw" onclick="send('http://127.0.0.1:8000/motor_fw')">&uarr;</button>
                    </div>
                    <div>
                        <center>
                            <button type="button" id="motor_left" onclick="send('http://127.0.0.1:8000/motor_left')">&larr;</button>
                            <button type="button" id="motor_stop" onclick="send('http://127.0.0.1:8000/motor_stop')">&squ;</button>
                            <button type="button" id="motor_right" onclick="send('http://127.0.0.1:8000/motor_right')">&rarr;</button>
                        </center>
                    </div>
                    <div>
                        <button type="button" id="motor_bk" onclick="send('http://127.0.0.1:8000/motor_bk')">&darr;</button>
                    </div>
                </center>
            </div>
        </div>
    </center>
</body>

</html>
"""

class servo:
    def __init__(self, pin, angle = 90):
        self.pin = pin
        self.angle = angle
        


class ServoHandler:
    __instance = None
    @staticmethod 
    def getInstance():
        """ Static access method. """
        if ServoHandler.__instance == None:
            ServoHandler()
        return ServoHandler.__instance
    
    def __init__(self):
        """ Virtually private constructor. """
        if ServoHandler.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            ServoHandler.__instance = self
        print("servohandler initialized")
        self.pwm = pigpio.pi()
        self.s1, self.s2 = servo(17), servo(27) #create tilt and pan servos
        self.pwm.set_mode(self.s1.pin, pigpio.OUTPUT)
        self.pwm.set_mode(self.s2.pin, pigpio.OUTPUT)
        self.set_servo_angle(self.s1, 90)
        self.set_servo_angle(self.s2, 90)
    
    def set_servo_angle(self, s: servo, angle):
        self.pwm.set_PWM_frequency( s.pin , 50 )
        self.pwm.set_servo_pulsewidth( s.pin , self.angle_to_f(angle) )
        sleep( 0.5 )
        self.pwm.set_PWM_dutycycle( s.pin , 0)
        self.pwm.set_PWM_frequency( s.pin , 0)
        s.angle = angle

    def close(self):
        self.pwm.stop()
        GPIO.cleanup()
        
    def angle_to_f(self, angle):
        if angle > 180:
            angle = 180
        if angle < 0:
            angle = 0
        return angle/180.*(2500.-750.) + 750.
    
    def left(self):
        self.incrementServoAngle(self.s2, 30)
        
    def right(self):
        self.incrementServoAngle(self.s2, -30)
    
    def up(self):
        self.incrementServoAngle(self.s1, 30)

    def down(self):
        self.incrementServoAngle(self.s1, -30)
    
    def center(self):
        self.set_servo_angle(self.s1, 90)
        self.set_servo_angle(self.s2, 90)
               
    def incrementServoAngle(self, s: servo, angle):
        end_angle = s.angle + angle   
        s.angle = end_angle
        if s.angle > 180:
            s.angle = 180
        if s.angle < 0:
            s.angle = 0
        self.set_servo_angle(s, s.angle)

class Motor:
    def __init__(self, in1, in2, en):
        self.in1 = in1 #24
        self.in2 = in2 #23
        self.en = en#25
        #temp1=1
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.in1,GPIO.OUT)
        GPIO.setup(self.in2,GPIO.OUT)
        GPIO.setup(self.en,GPIO.OUT)
        GPIO.output(self.in1,GPIO.LOW)
        GPIO.output(self.in2,GPIO.LOW)
        self.p=GPIO.PWM(self.en,1000)
        self.p.start(75)
    
    def forward(self):
        GPIO.output(self.in1,GPIO.HIGH)
        GPIO.output(self.in2,GPIO.LOW)

    def backward(self):
        GPIO.output(self.in1,GPIO.LOW)
        GPIO.output(self.in2,GPIO.HIGH)
    
    def stop(self):
        GPIO.output(self.in1,GPIO.LOW)
        GPIO.output(self.in2,GPIO.LOW)

        
    

class MotorHandler:
    __instance = None
    @staticmethod 
    def getInstance():
        """ Static access method. """
        if MotorHandler.__instance == None:
            MotorHandler()
        return MotorHandler.__instance
    
    def __init__(self):
        """ Virtually private constructor. """
        if MotorHandler.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            MotorHandler.__instance = self
        self.mr, self.ml = Motor(24, 23, 25), Motor(6, 5, 26)
        
    def motor_fw(self):
        self.mr.forward()
        self.ml.forward()

    def motor_bk(self):
        self.mr.backward()
        self.ml.backward()

    def motor_left(self):
        self.mr.backward()
        self.ml.forward()  

    def motor_right(self):
        self.mr.forward()
        self.ml.backward()

    def motor_stop(self):
        self.mr.stop()
        self.ml.stop()



class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.s = ServoHandler.getInstance()
        self.m = MotorHandler.getInstance()
        #print("streaming handler initialized")
        super().__init__(*args, **kwargs)
    #s.incrementServoAngle(10)
    #s.close()
    
    def _send_webpage(self):
        content = PAGE.encode('utf-8')
        self.send_response(200)
        self.send_header('Location', '/index.html')
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)
        
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/motor_stop':
            self._send_webpage()
            self.m.motor_stop()
        elif self.path == '/motor_fw':
            self._send_webpage()
            self.m.motor_fw()
        elif self.path == '/motor_right':
            self._send_webpage()
            self.m.motor_right()
        elif self.path == '/motor_left':
            self._send_webpage()
            self.m.motor_left()
        elif self.path == '/motor_bk':
            self._send_webpage()
            self.m.motor_bk()
        elif self.path == '/up':
            self._send_webpage()
            self.s.up()
        elif self.path == '/down':
            self._send_webpage()
            self.s.down()
        elif self.path == '/left':
            self._send_webpage()
            self.s.left()
        elif self.path == '/right':
            self._send_webpage()
            self.s.right()
        elif self.path == '/center':
            self._send_webpage()
            self.s.center()  
        elif self.path == '/index.html':
            self._send_webpage()
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    
        


with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    #camera.rotation = 90
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
