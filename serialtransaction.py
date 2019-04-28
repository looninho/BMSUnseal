# -*- coding: utf-8 -*-
"""
Created on Sun Mar 25 11:20:26 2018

@author: Loon
"""

from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtCore import (pyqtSignal, QIODevice,
                          QByteArray,
                          QTime)

class SerialTransaction(QSerialPort):
    #Signals
    responseSignal = pyqtSignal(['QByteArray'])
    errorSignal = pyqtSignal(['QString'])
    timeoutSignal = pyqtSignal(['QString'])
    
    #members
    m_quit = False

    def __init__(self):
        super(SerialTransaction,self).__init__()
        self.clear()
    
    def transaction(self,portName,waitTimeout, request):
        self.setPortName(portName)
        self.setBaudRate(QSerialPort.Baud115200)
        
        #1) write request then read response:
        
        if not self.open(QIODevice.ReadWrite):
            self.errorSignal.emit("Can't open {}, error code {}".format(portName,self.error()))
            self.close()
            return
        
        txtstr = '\n' + request + '\r\n'
        #txtstr = request+'\n'
        requestToSend = QByteArray(txtstr.encode())
        
        self.clear()
        bytesWritten = self.write(requestToSend)
        if bytesWritten == -1:
            self.errorSignal.emit("Failed to write the data to port {}, error: {}".format(portName, self.error()))
            self.close()
            return
        elif bytesWritten != requestToSend.size():
            self.errorSignal.emit("Failed to write all the data to port {}, error: {}".format(portName, self.error()))
            self.close()
            return
        elif self.waitForBytesWritten(waitTimeout):
            #print("Send at {}.".format(QTime.currentTime().toString()))
            if self.waitForReadyRead(waitTimeout):
                responseData = self.readAll()
                while self.waitForReadyRead(waitTimeout):
                    responseData.append(self.readAll())
                self.responseSignal.emit(responseData)
                self.close()
                #print("Receive at {}.".format(QTime.currentTime().toString()))
                return responseData
            else:
                self.timeoutSignal.emit("Wait read response timeout {}".format(QTime.currentTime().toString()))
                self.close()
                return
        else:
            self.timeoutSignal.emit("{} Operation timed out or an error occurred for port {}, error: {}".format(QTime.currentTime().toString(), portName, self.error()))
            self.close()
            return