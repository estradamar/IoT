from ev3dev2.motor import LargeMotor, OUTPUT_B, OUTPUT_D, SpeedPercent, MediumMotor, OUTPUT_A
from ev3dev2.sensor.lego import InfraredSensor
from ev3dev2.sensor import INPUT_1
import time
import paho.mqtt.client as mqtt

# MQTT Configuration
BROKER_ADDRESS = "192.168.68.101"
BROKER_PORT = 1883
TOPIC_BUTTON_PRESS = "ev3dev/button_press"
TOPIC_HEAD_SEQUENCE = "ev3dev/in"

# Initialize MQTT client
client = mqtt.Client()
client.connect(BROKER_ADDRESS, BROKER_PORT)

# Initialize motors and sensors (unchanged)
motor_a = LargeMotor(OUTPUT_B)
motor_b = MediumMotor(OUTPUT_A)
motor_d = LargeMotor(OUTPUT_D)
ir = InfraredSensor(INPUT_1)

# State variables
head_position = 'right'
beacon_active = False
last_activity_time = time.time()
TIMEOUT = 60  # 1 minute timeout

# Motor control functions (unchanged)
def mover_motor_a_suave(velocidad):
    motor_a.on(SpeedPercent(velocidad))

def detener_motor_suave():
    motor_a.off(brake=False)

def mover_motor_b_suave(velocidad, grados):
    motor_b.on_for_degrees(SpeedPercent(velocidad), grados, brake=False)

def mover_motor_d_suave(velocidad, grados):
    motor_d.on_for_degrees(SpeedPercent(velocidad), grados, brake=True)

def mover_cabeza_derecha():
    global head_position
    if head_position != 'right':
        motor_d.on_for_degrees(SpeedPercent(50), -90)
        head_position = 'right'

def mover_cabeza_izquierda():
    global head_position
    if head_position != 'left':
        motor_d.on_for_degrees(SpeedPercent(50), 90)
        head_position = 'left'

def mover_cabeza_secuencia():
    mover_motor_d_suave(50, 90)  # Left
    time.sleep(0.5)
    mover_motor_d_suave(50, -90)  # Right
    time.sleep(0.5)
    mover_motor_d_suave(50, 90)  # Left
    time.sleep(0.5)
    mover_motor_d_suave(50, -90)  # Right

# MQTT message handler (unchanged)
def on_message(client, userdata, msg):
    command = msg.payload.decode()
    print(f"Received a: {command}")
    if command == "head_sequence":
        mover_cabeza_secuencia()
    elif command == "forward":
        mover_motor_a_suave(50)
    elif command == "backward":
        mover_motor_a_suave(-50)
    elif command == "stop":
        detener_motor_suave()

client.on_message = on_message
client.subscribe(TOPIC_HEAD_SEQUENCE)

print('Ready. Listening for MQTT messages...')

try:
    while True:
        # Process MQTT messages (replaces client.loop_start())
        client.loop(timeout=0.01)  # Non-blocking, checks for new messages

        # Infrared sensor logic (unchanged)
        buttons = ir.buttons_pressed()
        current_time = time.time()

        if buttons:
            last_activity_time = current_time
            print("Button:", buttons)
            client.publish(TOPIC_BUTTON_PRESS, f"Button pressed: {buttons}")

        # Motor control logic (unchanged)
        if 'top_right' in buttons:
            mover_motor_a_suave(50)
        elif 'bottom_right' in buttons:
            mover_motor_a_suave(-50)
        else:
            detener_motor_suave()

        if 'top_left' in buttons:
            mover_motor_b_suave(50, 20)
        elif 'bottom_left' in buttons:
            mover_motor_b_suave(50, -20)

        if 'beacon' in buttons and not beacon_active:
            beacon_active = True
            mover_cabeza_izquierda()
        elif 'beacon' not in buttons and beacon_active:
            beacon_active = False
            mover_cabeza_derecha()

        time.sleep(0.30)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    client.disconnect()