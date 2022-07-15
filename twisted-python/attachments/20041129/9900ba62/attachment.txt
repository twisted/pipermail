import time, sys, urlparse, tkFileDialog
import Tkinter as Tk

import pymedia.audio.sound as sound
import pymedia.audio.acodec as acodec

from twisted.internet import task
from twisted.internet import reactor, tksupport

# constants
STOPPED   = 0
RECORDING = 1

# input params
insrc = "VIA AC'97 Audio (WAVE)"
format = sound.AFMT_U16_LE

# encoder parameters
params = {
         'id': acodec.getCodecId("mp3"),
         'bitrate': 64000,
         'sample_rate': 22050,
         'channels': 1
}


class Recorder:
   
   def __init__(self, params=params):
      
      self.task = task.LoopingCall(self.process)
      self.status = STOPPED
      self.encoder= acodec.Encoder(params)

      # determine input source
      inputid=None
      for d in sound.getIDevices():
         if d['name'] == insrc:
            inputid = d['id']
      
      if not inputid:
         raise Exception("Invalid or no input source")

      self.snd= sound.Input(22050, 1, format, inputid)
      
   def process(self):
      #while 1: # snd.getPosition()<= secs:
      s= self.snd.getData()
      if s and len(s):
         for fr in self.encoder.encode(s):
           # We definitely should use mux first, but for
           # simplicity reasons this way it'll work also
           self.outfile.write(fr)
      #else:
      #   time.sleep( .001 )
      
   def start(self, file):
      self.outfile= file
      self.snd.start()      
      self.task.start(.0000001)
      
   def stop(self):
      # Stop listening the incoming sound from the microphone or line in
      self.task.stop()
      self.snd.stop()
      self.outfile.close()
   
   
class RecorderGUI:
    
   def __init__(self, root):
      frame = Tk.Frame(root)
      self.frame=frame
      self.startB = Tk.Button(frame, padx=20, pady=2, text="Start", command=self.startRecording)
      self.stopB = Tk.Button(frame, padx=20, pady=2, text="Stop", command=self.stopRecording, state=Tk.DISABLED)
      self.quitB = Tk.Button(frame, padx=20, pady=2, text="Quit", command=self.quitApplication)
      self.startB.pack(side=Tk.LEFT)
      self.stopB.pack(side=Tk.LEFT)
      self.quitB.pack(side=Tk.RIGHT)
      frame.pack()      
   
   def setRecorder(self,recorder):      
      self.recorder = recorder
      
   def startRecording(self):
      file = tkFileDialog.asksaveasfile(title="Enter file to save to")
      self.stopB['state'] = Tk.NORMAL
      self.startB['state'] =Tk.DISABLED
      self.recorder.start(file)
      
   def stopRecording(self):
      self.recorder.stop()
      self.stopB['state'] = Tk.DISABLED
      self.startB['state'] = Tk.NORMAL

   def quitApplication(self):
      if self.recorder.status == RECORDING:
         self.recorder.stop()
      reactor.stop()

   
def run():

   import psyco
   psyco.full()

   guiroot = Tk.Tk()
   guiroot.protocol("WM_DELETE_WINDOW", reactor.stop)
   guiroot.title("Sound recorder")
   tksupport.install(guiroot)
   
   gui=RecorderGUI(guiroot)
   gui.recorder = Recorder()

   reactor.run()


if __name__ == '__main__':
    run()
