import serial
import minimalmodbus as mm


class Device():
    def __init__(self, config):
        self.status = 0  # Device not detected
        self.reading = 0  # default size of measurement
        self.opened = 0
        self.readingB = 0
        self.readingA = 0
        self.conf = config
        if self.conf.dev == "wo":
            try:
                self.inst = mm.Instrument(self.conf.port, 1)
                self.inst.serial.baudrate = 38400
                self.inst.serial.bytesize = 8
                self.inst.serial.parity = serial.PARITY_NONE
                self.inst.serial.stopbits = 1
                self.inst.serial.timeout = 1.0
                self.inst.address = 1
                self.inst.mode = mm.MODE_RTU
                self.status = 1
            except Exception:
                self.status = 0
        elif self.conf.dev == "pi":
            try:
                self.ser = serial.Serial(self.conf.port)
                self.ser.baudrate = 57600
                self.ser.timeout = 0.08
                self.ser.close()
                self.status = 1
                self.ser.open()
                self.comm = str.encode('<c>')
                self.ser.write(self.comm)
                a = self.ser.readline()
                if (a[5:12]).isdigit():
                    print("counter port: ", self.conf.port)
                    self.readingB = int(a[5:12])
                self.ser.close()
            except Exception:
                self.status = 0

        # testing, comment in production
        # self.status = 1

    def read_measurement(self):
        self.reading = 0

        if self.conf.dev == "wo":
            self.a = self.inst.read_register(0, 0, 3, False)
            self.b = self.inst.read_register(1, 0, 3, False)
            self.readingA = int((self.a)+((self.b << 16)))
            # watchout for minus values, counter change scale
            if abs(self.readingA - self.readingB) > 250000 and (
                    self.readingA > 2500000):
                self.readingB += 4294967292
            elif abs(self.readingA - self.readingB) > 250000 and (
                    self.readingA < 2500000):
                self.readingB -= 4294967292

        if self.conf.dev == "pi":
            if self.opened == 0:
                self.ser.open()
                self.opened = 1
            self.ser.write(self.comm)
            self.a = str(self.ser.readline())
            self.readingA = int(self.a[5:12])

        if abs(self.readingA - self.readingB) > 0:
            self.reading = int(round(abs(
                float(self.readingA - self.readingB) /
                float(self.conf.impulses)), 2) * 100)

        self.readingB = self.readingA
        return self.reading

    def set_zeros(self):
        self.readingB = 0
        self.readingA = 0
        if self.conf.dev == "wo":
            self.inst.write_bit(5000, 1, 5)
        if self.conf.dev == "pi":
            self.reading = 0
            if self.opened == 0:
                self.ser.open()
                self.opened = 1
            zcomm = str.encode('<d>')
            self.ser.write(zcomm)
            self.ser.readline()

    def zamknij(self):
        if self.conf.dev == "pi":
            self.ser.close()
            self.opened = 0
