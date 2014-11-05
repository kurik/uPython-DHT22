import pyb
from pyb import Pin
from pyb import ExtInt

# We need to use global properties here as any allocation of a memory (aka declaration of a variable)
# during the read cycle causes non-acceptable delay and we are loosing data than
nc = None
gnd = None
vcc = None
data = None
timer = None
micros = None

FALL_EDGES = 42 # we have 42 falling edges during data receive

times = list(range(FALL_EDGES))
index = 0

# The interrupt handler
def edge(line):
    global index
    global times
    global micros
    times[index] = micros.counter()
    if index < (FALL_EDGES - 1): # Avoid overflow of the buffer in case of any noise on the line
        index += 1

def init(timer_id = 2, nc_pin = 'Y3', gnd_pin = 'Y4', vcc_pin = 'Y1', data_pin = 'Y2'):
    global nc
    global gnd
    global vcc
    global data
    global micros
    global timer
    # Leave the pin unconnected
    if nc_pin is not None:
        nc = Pin(nc_pin)
        nc.init(Pin.OUT_OD)
        nc.high()
    # Make the pin work as GND
    if gnd_pin is not None:
        gnd = Pin(gnd_pin)
        gnd.init(Pin.OUT_PP)
        gnd.low()
    # Make the pin work as power supply
    if vcc_pin is not None:
        vcc = Pin(vcc_pin)
        vcc.init(Pin.OUT_PP)
        vcc.high()
    # Configure the pid for data communication
    data = Pin(data_pin)
    # Save the ID of the timer we are going to use
    timer = timer_id
    # setup the 1uS timer
    micros = pyb.Timer(timer, prescaler=83, period=0x3fffffff) # 1MHz ~ 1uS
    # Prepare interrupt handler
    ExtInt(data, ExtInt.IRQ_FALLING, Pin.PULL_UP, None)
    ExtInt(data, ExtInt.IRQ_FALLING, Pin.PULL_UP, edge)

# Start signal
def do_measurement():
    global nc
    global gnd
    global vcc
    global data
    global micros
    global timer
    global index
    # Send the START signal
    data.init(Pin.OUT_PP)
    data.low()
    micros.counter(0)
    while micros.counter() < 25000:
        pass
    data.high()
    micros.counter(0)
    while micros.counter() < 20:
        pass
    # Activate reading on the data pin
    index = 0
    data.init(Pin.IN, Pin.PULL_UP)
    # Till 5mS the measurement must be over
    pyb.delay(5)

# Parse the data read from the sensor
def process_data():
    global times
    i = 2 # We ignore the first two falling edges as it is a respomse on the start signal
    result_i = 0
    result = list([0, 0, 0, 0, 0])
    while i < FALL_EDGES:
        result[result_i] <<= 1
        if times[i] - times[i - 1] > 100:
            result[result_i] += 1
        if (i % 8) == 1:
            result_i += 1
        i += 1
    [int_rh, dec_rh, int_t, dec_t, csum] = result
    humidity = ((int_rh * 256) + dec_rh)/10
    temperature = (((int_t & 0x7F) * 256) + dec_t)/10
    if (int_t & 0x80) > 0:
        temperature *= -1
    comp_sum = int_rh + dec_rh + int_t + dec_t
    if (comp_sum & 0xFF) != csum:
        raise ValueError('Checksum does not match')
    return (humidity, temperature)

def measure():
    do_measurement()
    if index != (FALL_EDGES -1):
        raise ValueError('Data transfer failed: %s falling edges only' % str(index))
    return process_data()

