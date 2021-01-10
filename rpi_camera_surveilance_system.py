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
    <div>
        <center>
            <div>
                <button type="button" id="up">&uarr;</button>
            </div>
            <div>
                <center>
                    <button type="button" id="left" onclick="send('http://192.168.2.17:8000/left')">&larr;</button>
                    <button type="button" id="center" onclick="send('http://192.168.2.17:8000/center')">&squ;</button>
                    <button type="button" id="right" onclick="send('http://192.168.2.17:8000/right')">&rarr;</button>
                </center>
            </div>
            <div>
                <button type="button" id="down">&darr;</button>
            </div>
        </center>
    </div>
</body>

</html>
"""

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
        self.current_angle = 90   
        self.servo = 27
        self.pwm = pigpio.pi()
        self.pwm.set_mode(self.servo, pigpio.OUTPUT)
        self.pwm.set_PWM_frequency( self.servo, 50 )
        self.pwm.set_servo_pulsewidth( self.servo, self.angle_to_f(self.current_angle) ) ;
        sleep( 3 )
        self.pwm.set_PWM_dutycycle(self.servo, 0)
        self.pwm.set_PWM_frequency(self.servo, 0 )

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
        #self.pwm.start(13)
        self.incrementServoAngle(30)
        
    def right(self):
        #self.pwm.start(0)
        self.incrementServoAngle(-30)
    
    def center(self):
        self.pwm.set_PWM_frequency( self.servo, 50 )
        self.current_angle = 90 
        self.pwm.set_servo_pulsewidth( self.servo, self.angle_to_f(self.current_angle) ) ;
        sleep(0.5)
        self.pwm.set_PWM_dutycycle(self.servo, 0)
        self.pwm.set_PWM_frequency(self.servo, 0 )
        
        
    def incrementServoAngle(self, angle):
        self.pwm.set_PWM_frequency( self.servo, 50 )
        self.pwm.set_servo_pulsewidth( self.servo, self.angle_to_f(self.current_angle) ) ;
        sleep(0.1)
        end_angle = self.current_angle + angle
        self.current_angle = end_angle
        if self.current_angle > 180:
            self.current_angle = 180
        if self.current_angle < 0:
            self.current_angle = 0
        self.pwm.set_servo_pulsewidth( self.servo, self.angle_to_f(self.current_angle) ) ;
        sleep(0.5)
        self.pwm.set_PWM_dutycycle(self.servo, 0)
        self.pwm.set_PWM_frequency(self.servo, 0 )
        



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
