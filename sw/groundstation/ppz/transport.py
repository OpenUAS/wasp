import array
import serial
import libserial.SerialSender

class SerialTransport(libserial.SerialSender.SerialSender):
    """
    Reads data from the serial port 
    """
    def read(self, nbytes=5):
        if self.is_open():
            try:
                return self._serial.read(nbytes)
            except  serial.SerialTimeoutException:
                print "Timeout"
        return ""
    
    def write(self, data):
        if self.is_open():
            self._serial.write(data)

class TransportHeaderFooter:

    STX = 0x99

    def __init__(self, stx=STX, length=6, acid=0, msgid=0, ck_a=0, ck_b=0):
        self.stx = stx
        self.length = length
        self.acid = acid
        self.msgid = msgid
        self.ck_a = ck_a
        self.ck_b = ck_b

class Transport:
    """
    Class that extracts a paparazzi payload from a string or 
    sequence of characters from the transport layer
    
    Data is expected in the following form

    There are 6 non payload bytes in a packet

    Transport
    |STX|length|AC_ID|MESSAGE_ID|... payload=(length-6) bytes ...|Checksum A|Checksum B|
    
    Payload
    |... MESSAGE DATA ...|
    
    Data sent in little endian byte order
    """

    STATE_UNINIT,       \
    STATE_GOT_STX,      \
    STATE_GOT_LENGTH,   \
    STATE_GOT_ACID,     \
    STATE_GOT_MSGID,    \
    STATE_GOT_PAYLOAD,  \
    STATE_GOT_CRC1 =    range(0,7)

    #6 non payload bytes
    NUM_NON_PAYLOAD_BYTES = STATE_GOT_CRC1

    def __init__(self, check_crc=True, debug=False):
        self._check_crc = check_crc
        self._dbg = debug
        self._buf = array.array('c','\0'*256)
        self._state = self.STATE_UNINIT
        self._total_len = 0
        self._payload_len = 0
        self._payload_idx = 0
        self._ck_a = 0
        self._ck_b = 0
        self._error = 0
        self._acid = 0
        self._msgid = 0

    def _debug(self, msg):
        if self._dbg:
            print msg

    def pack_message_with_values(self, header, message, *values):
        return self.pack_one(
                        header,
                        message,
                        message.pack_values(*values))

    def pack_one(self, header, message, payload):
        payload_len = len(payload)
        total_len = payload_len + self.NUM_NON_PAYLOAD_BYTES

        #create an array big enough to hold data before the payload,
        #i.e. exclude the checksum
        buf = array.array('c','\0'*(self.NUM_NON_PAYLOAD_BYTES - 2))

        buf[0] = chr(header.stx)
        buf[1] = chr(total_len)
        buf[2] = chr(header.acid)
        buf[3] = chr(message.get_id())
    
        buf.fromstring(payload)


        first = True
        for d in buf:
            if first:
                ck_a = header.stx
                ck_b = header.stx
                first = False
            else:
                ck_a = (ck_a + ord(d)) % 256
                ck_b = (ck_b + ck_a) % 256

        buf.append(chr(ck_a))
        buf.append(chr(ck_b))

        #for b in buf:
        #    print "%x" % ord(b)

        #self._debug("SIZE: %s %s" % (payload_len, total_len))

        return buf

    def parse_many(self, string):
        """
        Similar to parse_one, but operates on a string, returning 
        multiple payloads if successful

        @returns: A list payloads
        """
        payloads = []
        for c in string:
            ok,h,p = self.parse_one(c)
            if ok:
                payloads.append((h,p))
        return payloads

    def parse_one(self, c):
        """
        Attempts to parse one character. Returns just the payload, and
        not the data in the transport layer, i.e. it does not return
        STX, the length, or the checksums

        @returns: The payload, or an empty string if insuficcient data
        is available
        """

        def update_checksum(d):
            #wrap to 8bit (simulate 8 bit addition)
            self._ck_a = (self._ck_a + d) % 256
            self._ck_b = (self._ck_b + self._ck_a) % 256

        def add_to_buf(char, uint8):
            self._buf[self._payload_idx] = char
            self._payload_idx += 1
            update_checksum(uint8)

        payload = ""
        error = False
        received = False
        #convert to 8bit int
        d = ord(c)

        if self._state == self.STATE_UNINIT:
            if d == TransportHeaderFooter.STX:
                self._state += 1
                self._ck_a = TransportHeaderFooter.STX
                self._ck_b = TransportHeaderFooter.STX
                self._debug("-- STX")
        elif self._state == self.STATE_GOT_STX:
            self._total_len = d
            self._payload_len = d - self.NUM_NON_PAYLOAD_BYTES
            self._payload_idx = 0
            update_checksum(d)
            self._state += 1
            self._debug("-- SIZE: PL (%s) TOT (%s)" % (self._payload_len, self._total_len))
        elif self._state == self.STATE_GOT_LENGTH:
            self._debug("-- ACID: %x" % d)
            self._acid = d
            update_checksum(d)
            self._state += 1
        elif self._state == self.STATE_GOT_ACID:
            self._debug("-- MSGID: %x" % d)
            self._msgid = d
            update_checksum(d)
            if self._payload_len == 0:
                self._state = self.STATE_GOT_PAYLOAD
            else:
                self._state += 1
        elif self._state == self.STATE_GOT_MSGID:
            add_to_buf(c, d)
            if self._payload_idx == self._payload_len:
                self._state += 1
                self._debug("-- PL")
        elif self._state == self.STATE_GOT_PAYLOAD:
            if d != self._ck_a and self._check_crc:
                error = True
                self._debug("-- CRC_A ERROR %x v %x" % (d, self._ck_a))
            else:
                self._state += 1
                self._debug("-- CRC_A OK")
        elif self._state == self.STATE_GOT_CRC1:
            if d != self._ck_b and self._check_crc:
                error = True
                self._debug("-- CRC_B ERROR")
            else:
                payload = self._buf[:self._payload_len].tostring()
                received = True
                self._state = self.STATE_UNINIT
                self._debug("-- CRC_B OK")

        if error:
            self._error += 1
            self._state = self.STATE_UNINIT
        elif received:
            header = TransportHeaderFooter(
                length=self._total_len,
                acid=self._acid,
                msgid=self._msgid,
                ck_a=self._ck_a,
                ck_b=self._ck_b)
            return True, header, payload

        return False, None, None


