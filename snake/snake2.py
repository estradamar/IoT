from ev3dev2.motor import LargeMotor, OUTPUT_B, OUTPUT_D, SpeedPercent, MediumMotor, OUTPUT_A
from ev3dev2.sensor.lego import InfraredSensor
from ev3dev2.sensor import INPUT_1
import time
import paho.mqtt.client as mqtt

# MQTT Configuration
# BROKER_ADDRESS = "broker.hivemq.com"  # Public broker for testing, replace with your own if needed
# BROKER_PORT = 8883  # Default secure MQTT port
BROKER_ADDRESS = "192.168.68.101"  # or your PC's LAN IP
BROKER_PORT = 1883
TOPIC_BUTTON_PRESS = "ev3dev/button_press"
TOPIC_HEAD_SEQUENCE = "ev3dev/in"

# Initialize MQTT client
client = mqtt.Client()

# Enable SSL/TLS
#client.tls_set()  # Use default certificates for secure connection

client.connect(BROKER_ADDRESS, BROKER_PORT)

# Initialize the motors
motor_a = LargeMotor(OUTPUT_B)  # Large motor (not the head)
motor_b = MediumMotor(OUTPUT_A)  # Medium motor (duckies)
motor_d = LargeMotor(OUTPUT_D)  # Large motor to move the head

# Initialize the infrared sensor on port 1
ir = InfraredSensor(INPUT_1)

# State variables
head_position = 'right'  # Initial head position is 'right'
beacon_active = False  # Initial beacon state

# Activity timeout settings
TIMEOUT = 60  # 1 minute of inactivity
last_activity_time = time.time()

# Functions to smoothly control motors
def mover_motor_a_suave(velocidad):
    motor_a.on(SpeedPercent(velocidad))


def detener_motor_suave():
    motor_a.off(brake=False)  # Coast to stop instead of abrupt brake


def mover_motor_b_suave(velocidad, grados):
    motor_b.on_for_degrees(SpeedPercent(velocidad), grados, brake=False)


def mover_motor_d_suave(velocidad, grados):
    motor_d.on_for_degrees(SpeedPercent(velocidad), grados, brake=True)


def mover_cabeza_secuencia():
    # Move head left and back to right twice as a sequence
    mover_motor_d_suave(50, 90)  # Move head left
    time.sleep(0.5)
    mover_motor_d_suave(50, -90)  # Move head back right
    time.sleep(0.5)
    mover_motor_d_suave(50, 90)  # Move head left again
    time.sleep(0.5)
    mover_motor_d_suave(50, -90)  # Move head back right again

# MQTT message handler
def on_message(client, userdata, msg):
    if msg.topic == TOPIC_HEAD_SEQUENCE:
        print("Received head movement sequence command")
        mover_cabeza_secuencia()

client.on_message = on_message
client.subscribe(TOPIC_HEAD_SEQUENCE)

print('ready')
client.loop_start()  # Start MQTT listener loop

while True:
    buttons = ir.buttons_pressed()
    current_time = time.time()

    # Check for inactivity timeout
    if current_time - last_activity_time > TIMEOUT:
        print("Exiting due to inactivity.")
        break

    if buttons:
        last_activity_time = current_time  # Reset activity timer
        print("button:", buttons)

        # Send MQTT message if any button is pressed
        client.publish(TOPIC_BUTTON_PRESS, f"Button pressed: {buttons}")

    # Smooth motor control for large motor (motor_a)
    if 'top_right' in buttons:
        mover_motor_a_suave(50)
    elif 'bottom_right' in buttons:
        mover_motor_a_suave(-50)
    else:
        detener_motor_suave()

    # Smooth motor control for medium motor (motor_b)
    if 'top_left' in buttons:
        mover_motor_b_suave(50, 20)
    elif 'bottom_left' in buttons:
        mover_motor_b_suave(50, -20)

    # Independent head control with the beacon button
    if 'beacon' in buttons:
        mover_motor_d_suave(50, 10)  # Slight head movement when beacon is pressed

    # Handle button release for instant stop
    if not buttons:
        detener_motor_suave()

    time.sleep(0.30)  # Reduced delay for smoother operation
