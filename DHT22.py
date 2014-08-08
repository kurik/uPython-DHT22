import pyb
from pyb import Pin
from pyb import ExtInt

nc = None
gnd = None
vcc = None
data = None
timer = None
micros = None

FALL_EDGES = 41 # we have 41 falling edges during data receive

times = list(range(FALL_EDGES))
index = 0

def init(timer_id = 2, nc_pin = 'Y3', gnd_pin = 'Y4', vcc_pin = 'Y1', data_pin = 'Y2'):
    global nc
    global gnd
    global vcc
    global data
    global micros
    global timer
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

# Start signal
def start_signal():
    global nc
    global gnd
    global vcc
    global data
    global micros
    global timer
    # setup the 1uS timer
    micros = pyb.Timer(timer, prescaler=83, period=0x3fffffff) # 1MHz ~ 1uS
    data.init(data.OUT_PP)
    data.low()
    micros.counter(0)
    while micros.counter() < 25000:
        pass
    data.high()
    while micros.counter() < 20:
        pass

# The interrupt handler
def edge(line):
    global index
    global times
    global micros
    times[index] = micros.counter()
    if index < (FALL_EDGES - 1):
        index += 1

# Parse the data read from the sensor
def process_data():
    global times
    # Check the length of init response
    #if (times[0] < 150) or (times[0] > 200):
    #    print('Initial response from sensor failed:', times[0], 'uS')
    #    raise ValueError('Initial response from sensor failed: %s uS' % times)
    i = 1
    result_i = 0
    result = list([0, 0, 0, 0, 0])
    while i < FALL_EDGES:
        result[result_i] <<= 1
        if times[i] - times[i - 1] > 100:
            result[result_i] += 1
        if (i % 8) == 0:
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
    global index
    global micros
    start_signal()
    index = 0
    micros.counter(0)
    extint = ExtInt(data, ExtInt.IRQ_FALLING, Pin.PULL_UP, edge)
    pyb.delay(5)
    extint = ExtInt(data, ExtInt.IRQ_FALLING, Pin.PULL_UP, None)
    if index != (FALL_EDGES -1):
        raise ValueError('Data transfer failed ' + str(index))
    return process_data()

