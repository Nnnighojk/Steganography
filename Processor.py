import Steganography
import numpy as np
import scipy
import zlib
import base64
import re
import os.path
import sys
import re
from PySide.QtGui import *
from PySide.QtCore import *
from SteganographyGUI import *
from scipy.misc import *


class DandD (QGraphicsView):
    newpic = Signal(str)
    def __init_(self, title, parent):
        super(DandD, self).__init__(title,parent)
        self.setAcceptDrops(True)
        self.imgArr = None
        self.name = None

    def dropEvent(self, e):
        if (e.mimeData().text()[-5:-2] == "png"):
            scn = QtGui.QGraphicsScene()
            pixmap = QtGui.QPixmap(e.mimeData().text()[7:-2])
            gfxPixItem = scn.addPixmap(pixmap)
            self.setScene(scn)
            self.fitInView(gfxPixItem,  Qt.KeepAspectRatio)
            self.show()
            self.imgArr = imread(e.mimeData().text()[7:-2])
            self.newpic.emit('hello')
            self.name = e.mimeData().text()[7:-2]
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def dragMoveEvent(self, event):
        event.accept()
    def dragEnterEvent(self, event):
        if not event.mimeData().hasFormat('text/plain'):
            event.ignore()
        else:
            event.accept()


class Processor(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(Processor,self).__init__(parent)
        self.setupUi(self)
        self.viewPayload1 = DandD(self.grpPayload1, self)
        self.viewPayload1.setGeometry(QtCore.QRect(10, 40, 361, 281))
        self.viewPayload1.setObjectName("viewPayload1")
        self.viewPayload1.newpic.connect(self.npayload)
        self.viewCarrier1 = DandD(self.grpCarrier1, self)
        self.viewCarrier1.setGeometry(QtCore.QRect(10, 40, 361, 281))
        self.viewCarrier1.setObjectName("viewCarrier1")
        self.viewCarrier1.newpic.connect(self.ncarrier)
        self.viewCarrier2 = DandD(self.grpCarrier2, self)
        self.viewCarrier2.setGeometry(QtCore.QRect(10, 40, 361, 281))
        self.viewCarrier2.setObjectName("viewCarrier2")
        self.viewCarrier2.newpic.connect(self.ncarrier2)
        self.compression = -1
        self.payload = None
        self.payloadsize = 0
        self.pimg = None
        self.cimg = None
        self.carriersize = 0
        self.carrier = None
        self.override = True
        self.carrier2 = None
        self.btnSave.clicked.connect(self.eands)
        self.chkApplyCompression.stateChanged.connect(self.npayload)
        self.slideCompression.valueChanged.connect(self.npayload)
        self.chkOverride.stateChanged.connect(self.ncarrier)
        self.btnSave.clicked.connect(self.eands)
        self.btnClean.clicked.connect(self.cleanpic)
        self.btnExtract.clicked.connect(self.extract_img)

    def npayload(self):
        self.pimg = self.viewPayload1.imgArr
        if self.chkApplyCompression.isChecked():
            self.slideCompression.setEnabled(True)
            self.lblLevel.setEnabled(True)
            self.txtCompression.setEnabled(True)
            self.txtCompression.setText(str(self.slideCompression.value()))
            self.compression = int(self.txtCompression.text())
            self.payload = Steganography.Payload(self.pimg,self.compression)
            self.payloadsize = len(self.payload.json)
            self.txtPayloadSize.setText(str(self.payloadsize))
        else:
            self.compression = -1
            self.slideCompression.setEnabled(False)
            self.lblLevel.setEnabled(False)
            self.txtCompression.setEnabled(False)
            #self.txtCompression.setText("")
            self.payload = Steganography.Payload(self.pimg,self.compression)
            self.payloadsize = len(self.payload.json)
            self.txtPayloadSize.setText(str(self.payloadsize))
        self.validate()

    def ncarrier(self):
        self.cimg = self.viewCarrier1.imgArr
        self.carriersize = self.viewCarrier1.imgArr.size
        s = len(self.cimg.flatten())
        self.txtCarrierSize.setText(str(s))
        self.carrier = Steganography.Carrier(self.cimg)
        if self.carrier.payloadExists():
             self.lblPayloadFound.setText(">>>> Payload Found<<<<")
             self.chkOverride.setEnabled(True)
             if self.chkOverride.isChecked():
                 self.override = True
             else:
                 self.override = False
        else:
            self.lblPayloadFound.setText("")
            self.chkOverride.setChecked(False)
            self.chkOverride.setEnabled(False)
            self.override = True
        self.validate()

    def validate(self):
        if ((self.chkOverride.isChecked() or (self.carrier and self.carrier.payloadExists() == False)) and (self.payloadsize > 0 and self.payloadsize < self.carriersize)):
            self.btnSave.setEnabled(True)
        else:
            self.btnSave.setEnabled(False)

    def eands(self):
        pic = Steganography.Carrier.embedPayload(self.carrier, self.payload,self.override)
        name = QtGui.QFileDialog.getSaveFileName(self, 'Save File')
        imsave(name[0], pic)

    def ncarrier2(self):
        self.carrier2 = Steganography.Carrier (self.viewCarrier2.imgArr)
        scn =QtGui.QGraphicsScene()
        scn.clear()
        self.viewPayload2.setScene(scn)
        self.viewPayload2.show()
        if(self.carrier2.payloadExists()):
            self.btnExtract.setEnabled(True)
            self.btnClean.setEnabled(True)
            self.lblCarrierEmpty.setText("")
        else:
            self.btnExtract.setEnabled(False)
            self.btnClean.setEnabled(False)
            self.lblCarrierEmpty.setText(">>>>Carrier Empty<<<<")

    def cleanpic(self):
        self.btnExtract.setEnabled(False)
        self.btnClean.setEnabled(False)
        temp = self.carrier2.clean()
        scn =QtGui.QGraphicsScene()
        scn.clear()
        self.viewPayload2.setScene(scn)
        self.viewPayload2.show()
        imsave(self.viewCarrier2.name,temp)
        self.lblCarrierEmpty.setText(">>>>Carrier Empty<<<<")

    def extract_img(self):
        extracted = Steganography.Carrier.extractPayload(self.carrier2)
        #new_pay = Steganography.Payload(None,-1,extracted)
        imsave('temp.png', extracted.rawData)
        scn = QtGui.QGraphicsScene()
        pixmap = QtGui.QPixmap('temp.png')
        gfxPixItem = scn.addPixmap(pixmap)
        self.viewPayload2.setScene(scn)
        self.viewPayload2.fitInView(gfxPixItem,  Qt.KeepAspectRatio)
        self.viewPayload2.show()
        try:
            self.viewPayload2.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.viewPayload2.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        except:
            pass


if __name__ == "__main__":
    currentApp = QApplication(sys.argv)
    currentForm = Processor()

    currentForm.show()
    currentApp.exec_()