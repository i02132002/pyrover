



def setServoAngle(servo, pwm, start_angle, end_angle):
    start_dC = start_angle / 18. + 3.
    end_dC = end_angle / 18. + 3.
    pwm.start(start_dC)
    current_angle = start_angle
    if end_angle > start_angle:
        while current_angle < end_angle:
            current_angle += 0.1
            current_dC = current_angle/18. + 3.
            pwm.ChangeDutyCycle(current_dC)
            sleep(0.01)
    else:
        while current_angle > end_angle:
            current_angle -= 0.1
            current_dC = current_angle/18. + 3.
            pwm.ChangeDutyCycle(current_dC)
            sleep(0.01)
    #ramp_angle(pwm, start_angle, angle)
    sleep(0.3)
    
servo = 17
GPIO.setup(servo, GPIO.OUT)
pwm = GPIO.PWM(servo, 50)
setServoAngle(servo, pwm, 100, 180)
setServoAngle(servo, pwm, 180, 100)
pwm.stop()
GPIO.cleanup()
#def ramp_angle(pwm, start_angle, end_angle):
        
#    pwm.ChangeDutyCycle(dutyCycle)


