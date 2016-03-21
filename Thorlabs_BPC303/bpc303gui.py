# -*- coding: utf-8 -*-
""" This script runs the GUI for the BPC303 class implemented in bpc303.py

Classes, Exceptions and Functions:
class mywindow --   main PyQt window class
function main --    main function to run when the script is called standalone
                    (intended use)

@author: Thibaud Ruelle, PhD student, Poggio Lab, Basel University
"""

import sys
from PyQt4 import QtCore, QtGui
from bpc303gui_ui import Ui_MainWindow
import bpc303


class mywindow(QtGui.QMainWindow, Ui_MainWindow):
    """
    Class expanding the main application window designed in QtDesigner
    and exported to .py format using pyuic4.bat
    """
    def __init__(self, parent=None):
        """
        Method creating a QMainWindow instance based on the design in
        Ui_MainWindow in bpc303gui_ui.py, defining additional variables and
        connecting UI elements to adequate methods
        """
        # Make a new QMainWindow instance and set up the layout and widgets
        super(mywindow, self).__init__(parent)
        self.setupUi(self)

        # Define the self.stage variable, in which an instance of the BPC303
        # class will be loaded later on
        self.stage = None

        # Connect signals from the different widgets to the methods handling
        # them
        self.connectDevice.clicked.connect(self.connectDeviceClicked)
        self.identifyDevice.clicked.connect(self.identifyDeviceClicked)
        self.setZero.clicked.connect(self.setZeroClicked)
        self.setPosition.clicked.connect(self.setPositionClicked)

    def connectDeviceClicked(self):
        """
        Method handling clicks on the connectDevice button by:
            - checking the deviceID string retrieved from the deviceID text
                box is valid
            - populating self.stage with an instance of the BPC303 class based
                on the deviceID string
            - running the stage's connect() method
            - enabling other UI elements as suitable
        """
        # retrieve ID from text box
        ID = self.deviceID.text()
        if ID == "71858688":
            # create BPC303 instance
            self.stage = bpc303.BPC303(ID)
            try:
                # initialize physical instrument
                self.stage.connect()
            except:
                raise
            try:
                # set to close loop mode
                self.stage.set_close_loop(True)
            except:
                raise
            # update connection LED
            self.isDeviceConnected.setStyleSheet("background-color: green;")
            # enable UI elemnts
            self.identifyDevice.setEnabled(True)
            self.setZero.setEnabled(True)
            self.setPosition.setEnabled(True)
            # grab instrument info and update text box
            info = self.stage.get_info()
            self.deviceInfo.clear()
            self.deviceInfo.appendPlainText(info)
        else:
            self.isDeviceConnected.setStyleSheet("background-color: red;")

    def identifyDeviceClicked(self):
        """
        Method handling clicks on the identifyDevice button by retrieving the
        active axis from the axisToIdentify combo box and running the
        stage's identify(axis) method. 
        """
        axis = str(self.axisToIdentify.currentText())
        print("Trying to ID axis: ", axis)
        self.stage.identify(axis)

    def setZeroClicked(self):
        """
        Method handling clicks on the setZero button by calling the stage's
        zero method
        """
        self.stage.zero()

    def setPositionClicked(self):
        """
        Method handling clicks on the setPosition button by retrieving
        positions from the xPos, yPos and zPos double boxes and calling
        the stage's set_position(xPos, yPos, zPos) method
        """
        x = self.xPos.value()
        y = self.yPos.value()
        z = self.zPos.value()
        self.stage.set_position(x, y, z)

    def cleanup(self):
        """
        Method handling the aboutToQuit() signal from the main application by
        running the stage's shutdown method (shut the connection to the stage
        down cleanly).
        """
        if self.stage:
            self.stage.shutdown()
            self.stage = None
        self.isDeviceConnected.setStyleSheet("background-color: lightgrey;")


def main():
    app = QtGui.QApplication(sys.argv)

    main = mywindow()
    main.show()

    app.aboutToQuit.connect(main.cleanup)
    app.aboutToQuit.connect(app.deleteLater)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
