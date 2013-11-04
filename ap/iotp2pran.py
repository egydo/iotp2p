#
# iotp2p Radio Access Networ
#
# Provides the control layer to give radio access to iotp2p using NRF24L01 chipsets.
#
# Nicola Cimmino 03.11.2013 First draft
#

from nrf24 import NRF24
import time
from threading import Thread

class iotp2pran:

  # Pipes in use.
  # P0 is the TX pipe, others are RX
  pipes = []
  
  # The radio, supports NRF24L01P
  radio = NRF24()

  # Signal the network to go down
  SHUTDOWN_SIGNAL = False

  def __init__(self):
   pipes = [[0x70, 0x70, 0x70, 0x70, 0x71], [0x70, 0x70, 0x70, 0x70, 0x70]]

   # We have CE on GPIO 22 (pin 15) and IRQ on GPIO 24 (pin 18)
   self.radio.begin(0, 0, 15, 18) 

   # Default iotp2p RAN parameters
   self.radio.setCRCLength(NRF24.CRC_8)
   self.radio.setRetries(15,15)
   self.radio.setPayloadSize(4)
   self.radio.setChannel(0x0A)
   self.radio.setDataRate(NRF24.BR_250KBPS)
   self.radio.setPALevel(NRF24.PA_MAX)
   self.radio.setAutoAck(1) 
   
   self.radio.openWritingPipe(pipes[0])
   self.radio.openReadingPipe(1, pipes[1])

   self.radio.startListening()


  # 
  # Reads one command from the specified pipe
  # TODO: timeout missing, if someone sends one block and drops off net
  #   that stuff will stick to the next caller start of message.
  #
  def readMessage(self, pipe):
      recv_str=""
      self.radio.startListening()
      while(not recv_str.endswith('\n')):
        recv_buf = []
        while not self.radio.available(pipe, False):
          time.sleep(1000/1000000.0)
        self.radio.read(recv_buf)
        for c in recv_buf:
          if(c != 0):
            recv_str += str(unichr(c))
      return recv_str[0:-1]

  def sendMessage(self, command):
   send_buf = [0] * self.radio.payload_size
   command += "\n"
   # We must align the string to payload size boundary, so we pad with nulls
   for cx in range(0, len(command) + (self.radio.payload_size - (len(command) % self.radio.payload_size))):
     send_buf[cx%self.radio.payload_size] = command[cx] if cx<len(command) else 0
     if((cx%self.radio.payload_size) == self.radio.payload_size - 1):
       self.radio.stopListening()
       self.radio.write(send_buf)
       self.radio.startListening()
       bx = 0


  def broadcastBCH(self):
   while not self.SHUTDOWN_SIGNAL:
     self.radio.stopListening()
     self.sendMessage("BCH:IOT0.0")
     self.radio.startListening()
     time.sleep(1)

  def startNetwork(self):
   self.SHUTDOWN_SIGNAL = False
   thread = Thread(target = self.broadcastBCH)
   thread.start()
   
  def stopNetwork(self):
   self.SHUTDOWN_SIGNAL = True
