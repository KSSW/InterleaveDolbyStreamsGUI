#InterleaveDolbyStreamsGUI by@KSSW
from PyQt5.QtWidgets import QApplication, QDialog, QWidget, QPushButton, QLabel, QLineEdit, QFileDialog, QGroupBox, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys
import os

class ProcessingThread(QThread):
    update_status = pyqtSignal(str)

    def __init__(self, ac3_file, thd_file, output_file):
        super().__init__()
        self.ac3_file = ac3_file
        self.thd_file = thd_file
        self.output_file = output_file

    def run(self):
        try:
            getStream = getBitStreams(self.ac3_file, self.thd_file, self.output_file)
            splitFrames = splitDolbyDigitalFrames(getStream)
            splitMLP = splitAccessHeaders(getStream)
            interleaveStreams = interleaveBitStreams(splitFrames, splitMLP) 
            writeBitStream(interleaveStreams.interleavedBitStream, getOutputFileName(getStream.out))
            self.update_status.emit('Completed Successfully!')
        except Exception as e:
            self.update_status.emit(f"{str(e)}")


class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Interleave-AC3-TrueHD-Streams-GUI v1.0.1 by@KSSW')
        self.setGeometry(100, 100, 800, 191)
        self.setFixedSize(800, 191)
        self.setWindowIcon(QIcon('C:/Users/48716/Desktop/InterleaveDolbyStreamsGUI-python/source/other/48.ico'))
        self.center()

        
        self.THD_File_btn = QPushButton('Open THD File', self)
        self.THD_File_btn.setGeometry(12, 12, 130, 23)
        self.THD_File_btn.clicked.connect(self.open_thd_file)

        self.AC3_File_btn = QPushButton('Open AC3 File', self)
        self.AC3_File_btn.setGeometry(12, 41, 130, 23)
        self.AC3_File_btn.clicked.connect(self.open_ac3_file)

        self.Text_THD = QLineEdit(self)
        self.Text_THD.setGeometry(148, 12, 640, 23)

        self.Text_AC3 = QLineEdit(self)
        self.Text_AC3.setGeometry(148, 41, 640, 23)

        self.Output_THD_AC3_btn = QPushButton('Output AC3+THD File', self)
        self.Output_THD_AC3_btn.setGeometry(12, 70, 130, 23)
        self.Output_THD_AC3_btn.clicked.connect(self.output_file)

        self.Text_Output = QLineEdit(self)
        self.Text_Output.setGeometry(148, 70, 640, 23)

        self.Start_btn = QPushButton('Start', self)
        self.Start_btn.setGeometry(13, 99, 776, 23)
        self.Start_btn.clicked.connect(self.start_process)

        
        self.groupBox = QGroupBox('Status Bar', self)
        self.groupBox.setGeometry(13, 128, 776, 57)
        self.groupBox.setStyleSheet('color: blue; font-family: "SimSun"; font-size: 12pt;')

        self.label_Status = QLabel('', self.groupBox)
        self.label_Status.setStyleSheet('color: red; font-family: Arial; font-size: 14.25pt;')
        self.label_Status.setAlignment(Qt.AlignCenter)
        
        groupBox_width = self.groupBox.width()
        label_width = 500  
        label_x = (groupBox_width - label_width) // 2
        self.label_Status.setGeometry(label_x, 10, label_width, 44)

        self.show()

    def open_thd_file(self):
        thd_file, _ = QFileDialog.getOpenFileName(self, "Open THD File", "", "Dolby Lossless (THD) (*.thd)")
        if thd_file:
            self.Text_THD.setText(thd_file)

    def open_ac3_file(self):
        ac3_file, _ = QFileDialog.getOpenFileName(self, "Open AC3 File", "", "Dolby Digital (AC3) (*.ac3)")
        if ac3_file:
            self.Text_AC3.setText(ac3_file)

    def output_file(self):
        output_file, _ = QFileDialog.getSaveFileName(self, "Save AC3+THD File", "", "THD+AC3 File (*.thd+ac3)")
        if output_file:
            self.Text_Output.setText(output_file)

    def start_process(self):
        ac3_file = self.Text_AC3.text()
        thd_file = self.Text_THD.text()
        output_file = self.Text_Output.text()

        if not ac3_file or not thd_file or not output_file:            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)    
            msg_box.setWindowTitle("Error")
            msg_box.setWindowIcon(QIcon('C:/Users/48716/Desktop/InterleaveDolbyStreamsGUI-python/source/other/48.ico'))
            msg_box.setText("Please Select All Files Before Starting.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
            return
        
        self.Start_btn.setEnabled(False)
        self.label_Status.setText("Processing...")
        
        self.thread = ProcessingThread(ac3_file, thd_file, output_file)
        self.thread.update_status.connect(self.update_status)
        self.thread.start()

    def update_status(self, status):
        self.label_Status.setText(status)
        
    def on_finished(self):
        self.Start_btn.setEnabled(True)

    def center(self):
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
#InterleaveDolbyStreams source code logic
#!/usr/bin/env python3 by@digitalaudionerd
class getBitStreams:
    def __init__(self, ac3_file, thd_file, output_file):
        self.fileName = [ac3_file, thd_file]
        self.out = output_file
        self.checkFileExtensions()
        self.readAC3()
        self.readMLP()

    def checkFileExtensions(self):
        if not os.path.basename(self.fileName[0]).lower().endswith(".ac3"):
            raise Exception("Error: The AC3 file doesn't have a .ac3 extension.")
        if not os.path.basename(self.fileName[1]).lower().endswith(".thd"):
            raise Exception("Error: The MLP file doesn't have a .thd extension.")

    def readAC3(self):
        syncWordAC3 = bytearray.fromhex('0b77')
        try:
            with open(self.fileName[0], 'rb') as stream:
                self.bitStreamAC3 = bytearray(stream.read())
        except IOError as e:
            raise Exception(f"Error: {e.strerror}: {e.filename}")
        if self.bitStreamAC3[0:2] != syncWordAC3:
            raise Exception("Error: The .ac3 file doesn't start with the AC3 sync word.")

    def readMLP(self):
        formatSyncMLP = bytearray.fromhex('f8726fba')
        try:
            with open(self.fileName[1], 'rb') as stream:
                self.bitStreamMLP = bytearray(stream.read())
        except IOError as e:
            raise Exception(f"Error: {e.strerror}: {e.filename}")
        if self.bitStreamMLP[4:8] != formatSyncMLP:
            raise Exception("Error: The .thd file doesn't have the major format sync.")


class splitDolbyDigitalFrames:
    def __init__(self, bitStreams):
        self.bitStreams = bitStreams
        self.checkSamplingFrequency()
        self.getFrameSize()
        self.splitFrames()

    def checkSamplingFrequency(self):
        twoMSBOperand = bytearray.fromhex('c0')
        self.codeByte = self.bitStreams.bitStreamAC3[4:5]
        if self.codeByte[0] & twoMSBOperand[0] != 0:
            raise Exception("Error: The AC3 bit stream has an unsupported sampling frequency.")

    def getFrameSize(self):
        words = [64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, 448, 512, 640, 768, 896, 1024, 1152, 1280]
        sixLSBOperand = bytearray.fromhex('3f')
        frameSizeCode = (self.codeByte[0] & sixLSBOperand[0]) >> 1
        self.frameSize = words[frameSizeCode] * 2

    def splitFrames(self):
        if len(self.bitStreams.bitStreamAC3) % self.frameSize != 0:
            raise Exception("Error: There's a problem with the AC3 frames.")
        numberOfFrames = int(len(self.bitStreams.bitStreamAC3) / self.frameSize)
        self.frameList = [self.bitStreams.bitStreamAC3[i:i + self.frameSize] for i in range(0, len(self.bitStreams.bitStreamAC3), self.frameSize)]


class splitAccessHeaders:
    def __init__(self, bitStreams):
        self.bitStreams = bitStreams
        self.formattedAccessHeaders = []
        self.accessHeaderList = []
        self.startByte = 0
        self.fourLSBOperand = bytearray.fromhex('0f')
        self.splitAccessHeaderLoop()
        self.formatAccessHeaders()
        if len(self.accessHeaderList) % 192 != 0:
            self.formatLeftOverAccessHeaders()

    def getAccessUnitLength(self):
        accessUnitWordLength = self.bitStreams.bitStreamMLP[self.startByte:self.startByte + 2]
        accessUnitByteLength = bytearray(2)
        accessUnitByteLength[0] = (accessUnitWordLength[0] & self.fourLSBOperand[0]) >> 4
        accessUnitByteLength[0] |= (accessUnitWordLength[0] & self.fourLSBOperand[0]) << 4
        accessUnitByteLength[1] = (accessUnitWordLength[1] & self.fourLSBOperand[0]) >> 4
        return int.from_bytes(accessUnitByteLength, byteorder='big')

    def splitAccessHeaderLoop(self):
        while self.startByte < len(self.bitStreams.bitStreamMLP):
            accessUnitLength = self.getAccessUnitLength()
            if accessUnitLength > 0:
                self.accessHeaderList.append(self.bitStreams.bitStreamMLP[self.startByte:self.startByte + accessUnitLength])
                self.startByte += accessUnitLength
            else:
                break

    def formatAccessHeaders(self):
        for i in range(0, len(self.accessHeaderList), 192):
            temp = self.accessHeaderList[i:i + 192]
            if len(temp) == 192:
                self.formattedAccessHeaders.append(b''.join(temp[0:39]))
                self.formattedAccessHeaders.append(b''.join(temp[39:77]))
                self.formattedAccessHeaders.append(b''.join(temp[77:116]))
                self.formattedAccessHeaders.append(b''.join(temp[116:154]))
                self.formattedAccessHeaders.append(b''.join(temp[154:192]))

    def formatLeftOverAccessHeaders(self):
        fullLength = len(self.accessHeaderList)
        startIndex = (fullLength // 192) * 192
        temp = self.accessHeaderList[startIndex:fullLength]
        tempLength = len(temp)
        if tempLength <= 39:
            self.formattedAccessHeaders.append(b''.join(temp[0:tempLength]))
        elif tempLength <= 77:
            self.formattedAccessHeaders.append(b''.join(temp[0:39]))
            self.formattedAccessHeaders.append(b''.join(temp[39:tempLength]))
        elif tempLength <= 116:
            self.formattedAccessHeaders.append(b''.join(temp[0:39]))
            self.formattedAccessHeaders.append(b''.join(temp[39:77]))
            self.formattedAccessHeaders.append(b''.join(temp[77:tempLength]))
        elif tempLength <= 154:
            self.formattedAccessHeaders.append(b''.join(temp[0:39]))
            self.formattedAccessHeaders.append(b''.join(temp[39:77]))
            self.formattedAccessHeaders.append(b''.join(temp[77:116]))
            self.formattedAccessHeaders.append(b''.join(temp[116:tempLength]))
        else:
            self.formattedAccessHeaders.append(b''.join(temp[0:39]))
            self.formattedAccessHeaders.append(b''.join(temp[39:77]))
            self.formattedAccessHeaders.append(b''.join(temp[77:116]))
            self.formattedAccessHeaders.append(b''.join(temp[116:154]))
            self.formattedAccessHeaders.append(b''.join(temp[154:tempLength]))


class interleaveBitStreams:
    def __init__(self, splitFrames, splitMLP):
        self.splitFrames = splitFrames
        self.splitMLP = splitMLP
        self.findMinMaxLengths()
        self.createInterleavedList()
        self.interleavedBitStream = b''.join(self.interleavedList)

    def findMinMaxLengths(self):
        self.lenDD = len(self.splitFrames.frameList)
        self.lenMLP = len(self.splitMLP.formattedAccessHeaders)
        self.minimum = min(self.lenDD, self.lenMLP)
        self.maximum = max(self.lenDD, self.lenMLP)

    def createInterleavedList(self):
        self.interleavedList = []
        for i in range(self.minimum):
            self.interleavedList.append(self.splitFrames.frameList[i])
            self.interleavedList.append(self.splitMLP.formattedAccessHeaders[i])
        if self.lenDD != self.lenMLP:
            for i in range(self.minimum, self.maximum):
                if i < self.lenDD:
                    self.interleavedList.append(self.splitFrames.frameList[i])
                if i < self.lenMLP:
                    self.interleavedList.append(self.splitMLP.formattedAccessHeaders[i])

def writeBitStream(bitStream, fileName):
    with open(fileName, 'wb') as outputFile:
        outputFile.write(bitStream)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    sys.exit(app.exec_())
