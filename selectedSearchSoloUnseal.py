# -*- coding: utf-8 -*-
"""
Created on Sun Mar 25 22:52:31 2018

@author: Loon
"""

import sys

#from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import (QApplication, QWidget, QComboBox,
                             QLabel, QSpinBox, QLineEdit,
                             QPushButton, QGridLayout, QMessageBox,
                             QDesktopWidget)
from PyQt5.QtGui import QIcon

from PyQt5.QtSerialPort import QSerialPortInfo
import serialtransaction as st

import os, pickle, time, random

import winsound
duration = 1000  # millisecond
freq = 440  # Hz

class Dialog(QWidget):  
    #codeFound = pyqtSignal()
    words=''
    lastwords=''
    canSend = False
    requestToSend=''
    m_waitTimeout=100
    m_attemp=0
    stockf021=b''
    
    def __init__(self):
        super().__init__()
        self.m_transaction = 0
        self.haveRightCode = False
        self.stop = True
        self.m_serialt = st.SerialTransaction()
        self.initUI()
        #self.longdelay = 0.8
        self.shortdelay=0.05
    
    def initUI(self):
        
        self.m_serialPortLabel = QLabel("Serial port:")
        self.m_serialPortComboBox = QComboBox()
        self.m_waitResponseLabel = QLabel("Wait response, msec:")
        self.m_waitResponseSpinBox = QSpinBox()
        self.m_longDelayLabel = QLabel("transaction delay, msec:")
        self.m_longDelaySpinBox = QSpinBox()
        self.m_runTimeoutSpinBox = QSpinBox()
        self.m_runTimeoutLabel = QLabel("run timeout in min:")
        
        self.m_randomGroupButton = QPushButton("Random group")
        self.m_defaultGroupButton = QPushButton("Default group")
        
        self.m_indexListLabel = QLabel("Warp multiplicators:")
        self.m_p0SpinBox = QSpinBox()
        self.m_p1SpinBox = QSpinBox()
        self.m_p2SpinBox = QSpinBox()
        self.m_p3SpinBox = QSpinBox()
        
        self.m_autoFindUnsealCodeButton = QPushButton("autoFindUnsealCode")
        #self.m_stopButton = QPushButton("Stop")
        
        
        self.m_runButton = QPushButton("Send request")
        self.m_requestLineEdit = QLineEdit("F020")
        self.m_requestLabel = QLabel("Request (hex without 0x):")
        self.m_trafficLabel = QLabel("No traffic.")
        self.m_statusLabel = QLabel("Status: Not running.")
        
        available_ports = QSerialPortInfo.availablePorts()
        for port in available_ports:
            self.m_serialPortComboBox.addItem(port.portName())
        
        self.m_waitResponseSpinBox.setRange(0,10000)
        self.m_waitResponseSpinBox.setValue(1500)
        
        self.m_longDelaySpinBox.setRange(0,10000)
        self.m_longDelaySpinBox.setValue(100)
        self.longdelay = 0.1
        
        self.m_runTimeoutSpinBox.setRange(0,10000)
        self.m_runTimeoutSpinBox.setValue(5)
        
        self.m_p0SpinBox.setRange(0,2)
        self.m_p0SpinBox.setValue(0)
        self.m_p1SpinBox.setRange(0,4)
        self.m_p1SpinBox.setValue(0)
        self.m_p2SpinBox.setRange(0,16)
        self.m_p2SpinBox.setValue(4)
        self.m_p3SpinBox.setRange(0,256)
        self.m_p3SpinBox.setValue(16)
        
        mainLayout = QGridLayout()
                
        mainLayout.addWidget(self.m_serialPortLabel,0,0)
        mainLayout.addWidget(self.m_serialPortComboBox,0,1)
        
        mainLayout.addWidget(self.m_waitResponseLabel,1,0)
        mainLayout.addWidget(self.m_waitResponseSpinBox,1,1)
        
        mainLayout.addWidget(self.m_longDelayLabel,2,0)
        mainLayout.addWidget(self.m_longDelaySpinBox,2,1)
        
        mainLayout.addWidget(self.m_runTimeoutLabel,3,0)
        mainLayout.addWidget(self.m_runTimeoutSpinBox,3,1)
        mainLayout.addWidget(self.m_randomGroupButton,3,2)
        mainLayout.addWidget(self.m_defaultGroupButton,3,3)
        
        mainLayout.addWidget(self.m_indexListLabel,4,0)
        mainLayout.addWidget(self.m_p0SpinBox,4,1)
        mainLayout.addWidget(self.m_p1SpinBox,4,2)
        mainLayout.addWidget(self.m_p2SpinBox,4,3)
        mainLayout.addWidget(self.m_p3SpinBox,4,4)
        
        #mainLayout.addWidget(self.m_stopButton,1,2,2,1)
        mainLayout.addWidget(self.m_requestLabel,5,0)
        mainLayout.addWidget(self.m_requestLineEdit,5,1,1,2)
        
        mainLayout.addWidget(self.m_runButton,6,1)
        mainLayout.addWidget(self.m_autoFindUnsealCodeButton,6,2)
        
        mainLayout.addWidget(self.m_trafficLabel,7,0,1,4)
        
        mainLayout.addWidget(self.m_statusLabel,8,0,1,5)
        
        self.setLayout(mainLayout)
        
        self.setWindowTitle("Solo Search Unseal Code")
        self.setWindowIcon(QIcon('pinion-icon.png'))
        self.m_serialPortComboBox.setFocus()
        
        #connection
        #self.codeFound.connect(self.showResult)
        self.m_runButton.clicked.connect(self.transactionUI)
        self.m_autoFindUnsealCodeButton.clicked.connect(self.autoFindUnsealCode)
        #☺self.m_stopButton.clicked.connect(self.stopSearching)
        self.m_serialt.responseSignal.connect(self.showResponse)
        self.m_serialt.errorSignal.connect(self.processError)
        self.m_serialt.timeoutSignal.connect(self.processTimeout)
        self.m_longDelaySpinBox.valueChanged.connect(self.updLongDelay)
        self.m_waitResponseSpinBox.valueChanged.connect(self.updwaitTimeout)
        self.m_randomGroupButton.clicked.connect(self.selectRandomGroup)
        self.m_defaultGroupButton.clicked.connect(self.selectDefaultGroup)
        
        self.center()
        
        self.show()
    
    def selectRandomGroup(self):
        random.seed()
        self.m_p0SpinBox.setValue(random.sample(range(3),1)[0])
        self.m_p1SpinBox.setValue(random.sample(range(5),1)[0])
        self.m_p2SpinBox.setValue(random.sample(range(17),1)[0])
        self.m_p3SpinBox.setValue(random.sample(range(257),1)[0])
        return
    
    def selectDefaultGroup(self):
        self.m_p0SpinBox.setValue(0)
        self.m_p1SpinBox.setValue(0)
        self.m_p2SpinBox.setValue(4)
        self.m_p3SpinBox.setValue(16)
        return
    
    def autoFindUnsealCode(self):
        self.m_transaction = 0
        self.m_attemp = 0
        self.stop = False
        self.haveRightCode = False
        
        self.requestToSend = 'f021'
        self.stockf021 = self.transaction()
        print("stockf021:{}".format(self.stockf021))
        
        filename_remain, remaining2Words = self.selectGroup()
        
        random.seed()
        
        t0 = time.time()
        print(time.strftime(" start at %H:%M:%S", time.gmtime()))
        while not self.haveRightCode and not self.stop:
            self.lastwords = self.words
            self.words=random.sample(remaining2Words,1)[0]
            self.sendUnsealCode(self.words[:4], self.words[-4:])
            #time.sleep(self.longdelay) #wait 10 ms
            #self.longdelay=1
            if self.checkErrorStatus():
                self.haveRightCode = True
                self.stop = True
                QMessageBox.information(self,"Pwd found!","Youpi! Found unseal password {} in {} attemps".format(self.words,self.m_attemp))
            #self.longdelay=0.1
            #time.sleep(self.longdelay)
            remaining2Words.remove(self.words)
            if len(remaining2Words) == 0 or \
            time.time()-t0 >  60*self.m_runTimeoutSpinBox.value():
                self.stop = True
            #self.mutex.unlock()
            #print("fin: {}".format(self.canSend))
            #if self.words == '04143672':
                #print("Traffic, attemp #{}: {} is in.".format(self.m_attemp,self.words))
                #self.stop = True
                #print("début: {}".format(self.canSend))
                #winsound.Beep(2*freq, duration)
                #QMessageBox.information(self,"is In","No! known unseal password {} in {} transactions".format(self.words,self.m_transaction))
        elapsed = (time.time()-t0)/60
        print("duration {} minutes with {} attemps.".format(elapsed,self.m_attemp))
        with open(filename_remain, 'wb') as fichier:
            mon_pickler = pickle.Pickler(fichier,2)
            for w in remaining2Words:
                mon_pickler.dump(w)
                
        #if self.haveRightCode:
            #winsound.Beep(freq, 2*duration)
            #QMessageBox.information(self,"Pwd found!","Youpi! Found unseal password {} in {} transactions".format(self.words,self.m_transaction))
            #print(time.strftime(" found at %H:%M:%S", time.gmtime()))
            #print(self.words)
        
        return
    
    def selectGroup(self):
        lp=[self.m_p0SpinBox.value(),self.m_p1SpinBox.value(),
            self.m_p2SpinBox.value(),self.m_p3SpinBox.value()]
        
        filename=''
        for i in lp:
            filename += str(i) + 'x'
        filename_full = filename + 'Warp'
        filename_remain = filename + 'WarpRemain'
        
        if not os.path.isfile(filename_full):
            filename_full = warpGenerator(lp)
            remaining2Words = copyFileToList(filename_full)[0]
        else:
            if os.path.isfile(filename_remain):
                remaining2Words = copyFileToList(filename_remain)[0]
            else:
                remaining2Words = copyFileToList(filename_full)[0]
        return (filename_remain, remaining2Words)
        
    def stopSearching(self):
        self.stop = True
        return
    
    def sendUnsealCode(self, word1, word2):
        self.m_attemp += 1
        self.m_statusLabel.setText("Status: Running, connected to port {}.".format(self.m_serialPortComboBox.currentText()))
        self.requestToSend = '1f00' + word1
        #time.sleep(self.longdelay)
        self.transaction()
        #time.sleep(1.1)
        self.requestToSend = '1f00' + word2
        self.transaction()
        return
    
    def checkErrorStatus(self):
        #self.m_waitTimeout = 200
         # read unseal code:
        self.requestToSend = 'f060'
        #time.sleep(self.longdelay)
        self.transaction()
        #time.sleep(self.longdelay)
         # check error status:¶
        self.requestToSend = '1016'
        ba=self.transaction()
        b=bin(int(ba))
        #print(b[-4:])
        if b[-4:] != '0000':
            return True
        #self.m_waitTimeout = self.m_waitResponseSpinBox.value()
        return False

    
    def testWrite(self):
        #self.m_waitTimeout = 200
         # read unseal code:
        self.requestToSend = 'ff2103303037' #'007'=0x303037
        #time.sleep(self.longdelay)
        self.transaction()
        #time.sleep(self.longdelay)
         # check error status:¶
        self.requestToSend = 'f021'
        ba=self.transaction()
        if ba == b'007':
            s=hex(ba.size()).split('x')[-1]
            while len(s) < 2:
                s = '0' + s
            strhex = ba.toHex()
            self.requestToSend = 'ff21' + s + str(strhex,'utf-8')
            self.transaction()
            return True
        else:
            return False
    
    def transaction(self):
        #self.canSend = False
        #self.setControlsEnabled(False)
        self.m_statusLabel.setText("Status: Running, connected to port {}.".format(self.m_serialPortComboBox.currentText()))
        response=self.m_serialt.transaction(self.m_serialPortComboBox.currentText(),\
                                  self.m_waitTimeout,\
                                  self.requestToSend)
        
         #wait_until(self.readyToSend,self.longdelay,self.shortdelay)
        return response
    
    def transactionUI(self):
        self.m_waitTimeout = 200
        #self.canSend = False
        #self.setControlsEnabled(False)
        self.m_statusLabel.setText("Status: Running, connected to port {}.".format(self.m_serialPortComboBox.currentText()))
        #wait_until(self.readyToSend,self.longdelay,self.shortdelay)
        response = self.m_serialt.transaction(self.m_serialPortComboBox.currentText(),\
                                  self.m_waitTimeout,\
                                  self.m_requestLineEdit.text())
        #wait_until(self.readyToSend,self.longdelay,self.shortdelay)
        self.m_waitTimeout = self.m_waitResponseSpinBox.value()
        return response
    
    def showResponse(self, ba):
        #print("receive at {}".format(QTime.currentTime().toString()))
        #self.setControlsEnabled(True)
        self.m_transaction += 1
        self.m_trafficLabel.setText("response (bytes):{}".format(ba))
        #ok = False
        #print(ba.toInt(ok))
        #print(ba)
        #self.canSend=True
        return
    
    def readyToSend(self):
        return self.canSend
    
    def showResult(self):
        winsound.Beep(freq, 2*duration)
        QMessageBox.information(self,"Pwd found!","Youpi! Found unseal password {} in {} transactions".format(self.words,self.m_transaction))
        print(time.strftime(" found at %H:%M:%S", time.gmtime()))
        print(self.words)
    
    def processError(self, s):
        self.setControlsEnabled(True)
        self.m_statusLabel.setText("Status: Not running, {}.".format(s))
        self.m_trafficLabel.setText("No traffic.")
        return
    
    def processTimeout(self, s):
        self.setControlsEnabled(True)
        self.m_statusLabel.setText("Status: Running, {}.".format(s))
        self.m_trafficLabel.setText("No traffic.")
        return
    
    def updLongDelay(self,val):
        #self.longdelay = self.m_longDelaySpinBox.value()/1000
        self.londelay = val/1000
        print("Long delay = {} s".format(self.londelay))
        return
    
    def updwaitTimeout(self,val):
        #self.longdelay = self.m_longDelaySpinBox.value()/1000
        self.m_waitTimeout = val
        print("Long delay = {} s".format(self.m_waitTimeout))
        return
    
    def setControlsEnabled(self, enable):
        self.m_runButton.setEnabled(enable)
        self.m_serialPortComboBox.setEnabled(enable)
        self.m_waitResponseSpinBox.setEnabled(enable)
        self.m_requestLineEdit.setEnabled(enable)
        return
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def closeEvent(self,event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes | 
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore() 

def saveFromTo(filename,start=0x00000000, quantity=0x10000):
    with open (filename,'wb') as fichier:
        mon_pickler = pickle.Pickler(fichier,2)
        hexmaxi=start+quantity;lenmaxi=8
        for h in range(start,hexmaxi+1):
            s=hex(h).split('x')[-1]
            while len(s) < lenmaxi:
                s = '0' + s
            mon_pickler.dump(s)
    return

def copyFileToList(filename):
    """copy les données depuis un fichier vers une liste."""
    #t0 = time.time()
    with open(filename, 'rb') as fichier:
        mon_depickler = pickle.Unpickler(fichier)
        data=[];dim = 0
        while 1:
            try:
                data.append(mon_depickler.load())
                dim += 1
            except EOFError:
                print("fin de lecture.")
                break
    #print("durée : {} s.".format(time.time() - t0))
    return (data, dim)

def warpGenerator(list_premiers):
    filename = ''
    for i in list_premiers:
        filename += str(i) + 'x'
    filename += 'Warp'
    begin = (list_premiers[0]*5*17*257*65537 +
             list_premiers[1]*17*257*65537 +
             list_premiers[2]*257*65537 +
             list_premiers[3]*65537)
    
    saveFromTo(filename,begin)
    return filename

def wait_until(somepredicate, timeout, period=0.01, *args, **kwargs):
    mustend = time.time() + timeout
    while time.time() < mustend:
        if somepredicate(*args, **kwargs): return True
        time.sleep(period)
    return False

# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    w = Dialog()
    #w.show()
    
    sys.exit(app.exec_())
