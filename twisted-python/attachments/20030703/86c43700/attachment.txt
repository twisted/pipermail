Index: twisted/internet/serialport/win32serialport.py
===================================================================
RCS file: /cvs/Twisted/twisted/internet/serialport/win32serialport.py,v
retrieving revision 1.2
diff -u -r1.2 win32serialport.py
--- twisted/internet/serialport/win32serialport.py	5 Apr 2003 00:50:37 -0000	1.2
+++ twisted/internet/serialport/win32serialport.py	3 Jul 2003 00:42:59 -0000
@@ -64,7 +64,7 @@
         self.protocol = protocol
         self.protocol.makeConnection(self)
         self._overlappedRead = win32file.OVERLAPPED()
-        self._overlappedRead.hEvent = win32event.CreateEvent(None, 0, 0, None)
+        self._overlappedRead.hEvent = win32event.CreateEvent(None, 1, 0, None)
         self._overlappedWrite = win32file.OVERLAPPED()
         self._overlappedWrite.hEvent = win32event.CreateEvent(None, 0, 0, None)
         
@@ -83,24 +83,31 @@
             first = str(self.read_buf[:n])
             #now we should get everything that is already in the buffer
             flags, comstat = win32file.ClearCommError(self._serial.hComPort)
-            rc, buf = win32file.ReadFile(self._serial.hComPort,
-                                         win32file.AllocateReadBuffer(comstat.cbInQue),
-                                         self._overlappedRead)
-            n = win32file.GetOverlappedResult(self._serial.hComPort, self._overlappedRead, 1)
-            #handle all the received data:
-            self.protocol.dataReceived(first + str(buf[:n]))
+            if comstat.cbInQue:
+                win32event.ResetEvent(self._overlappedRead.hEvent)
+                rc, buf = win32file.ReadFile(self._serial.hComPort,
+                                             win32file.AllocateReadBuffer(comstat.cbInQue),
+                                             self._overlappedRead)
+                n = win32file.GetOverlappedResult(self._serial.hComPort, self._overlappedRead, 1)
+                #handle all the received data:
+                self.protocol.dataReceived(first + str(buf[:n]))
+            else:
+                #handle all the received data:
+                self.protocol.dataReceived(first)
 
         #set up next one
+        win32event.ResetEvent(self._overlappedRead.hEvent)
         rc, self.read_buf = win32file.ReadFile(self._serial.hComPort,
                                                win32file.AllocateReadBuffer(1),
                                                self._overlappedRead)
 
     def write(self, data):
-        if self.writeInProgress:
-            self.outQueue.append(data)
-        else:
-            self.writeInProgress = 1
-            win32file.WriteFile(self._serial.hComPort, data, self._overlappedWrite)
+        if data:
+            if self.writeInProgress:
+                self.outQueue.append(data)
+            else:
+                self.writeInProgress = 1
+                win32file.WriteFile(self._serial.hComPort, data, self._overlappedWrite)
 
     def serialWriteEvent(self):
         try:
