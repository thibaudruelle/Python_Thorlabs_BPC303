# -*- coding: utf-8 -*-
""" This module contains the BPC303 class and its related functions, which
implement simultaneous initialization and control of the 3 channels of a
Thorlabs BPC 303 Benchtop Piezo Controller.

Classes, Exceptions and Functions:
class BPC303 --     initialization and control of the 3 channels of a
                    Thorlabs BPC 303 Benchtop Piezo Controller

@author: Thibaud Ruelle, PhD student, Poggio Lab, Basel University
"""

import sys
import logging as log
from time import sleep
import operator
import clr

clr.AddReference("System.Collections")
clr.AddReference("System.Linq")
from System.Collections.Generic import List #analysis:ignore
import System.Collections.Generic #analysis:ignore
from System import String, Decimal #analysis:ignore
import System.Linq #analysis:ignore
import System #analysis:ignore

sys.path.append(r"C:\Program Files\Thorlabs\Kinesis")
clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
clr.AddReference("Thorlabs.MotionControl.GenericPiezoCLI")
clr.AddReference("Thorlabs.MotionControl.Benchtop.PiezoCLI")
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI #analysis:ignore
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceNotReadyException #analysis:ignore
import Thorlabs.MotionControl.GenericPiezoCLI.Piezo as Piezo #analysis:ignore
from Thorlabs.MotionControl.Benchtop.PiezoCLI import BenchtopPiezo #analysis:ignore


class BPC303:
    """
    Main class for the BPC303 3 channel Benchtop Piezo Controller. Wraps the
    .NET base class from Thorlabs providing channel by channel control.

    Attributes and methods:
    attribute deviceID -- stores the device ID of the physical instrument
    attribute axis_chan_mapping -- stores the direction (x, y or z) which
        each channel of the controller addresses
    attribute isconnected -- boolean representing the state of the connection
        to the physical instrument
    attribute controller -- controller instance (from Thorlabs .NET dll)
    attributes xchannel, ychannel and zchannel -- channel instances
        (from Thorlabs .NET dll)
    method __init__(self, deviceID, axis_chan_mappign) --
    method __enter__(self) -- special class, see doc
    method connect(self) -- initializes the physical instrument
    """
    def __init__(self, deviceID, axis_chan_mapping={'x': 1, 'y': 2, 'z': 3}):
        """
        Method creating a BPC303 instance and setting up the connection to the
        device with device ID. Also creates the attributes self.deviceID,
        self.isconnected and self.axis_chan_mapping
        """
        DeviceManagerCLI.BuildDeviceList()
        self.deviceID = deviceID
        self.isconnected = False
        self.axis_chan_mapping = axis_chan_mapping
        if (self.deviceID in DeviceManagerCLI.GetDeviceList().ToArray()):
            self.controller = BenchtopPiezo.CreateBenchtopPiezo(self.deviceID)
        else:
            raise DeviceNotReadyException
        for attrname in ("xchannel", "ychannel", "zchannel"):
            setattr(self, attrname, None)

    def __enter__(self):
        return self

    def __get_chan(self, axis):
        """
        Internal method returning the channel corresponding to axis
        """
        attrname = axis + "channel"
        channel = getattr(self, attrname)
        return(channel)

    def connect(self):
        """
        Method initializing the physical instrument, first the main controller
        unit and then each channel, which is linked to the corresponding axis
        as defined in self.axis_chan_mapping
        """
        print("Connecting to BPC303:")
        print("\t- connecting to controller %s -->" % self.deviceID, end="")
        self.controller.Connect(self.deviceID)
        self.isconnected = self.controller.IsConnected
        print(" done" if self.controller.IsConnected else "failed")
        for axis in ("x", "y", "z"):
            channelno = self.axis_chan_mapping[axis]
            attrname = axis + "channel"
            print("\t- connecting channel %d (%s axis) -->" % (channelno, axis), end="")
            setattr(self, attrname, self.controller.GetChannel(channelno))
            channel = getattr(self, attrname)
            if not channel.IsSettingsInitialized():
                try:
                    channel.WaitForSettingsInitialized(5000)
                except:
                    raise
            channel.StartPolling(100)
            channel.EnableDevice()
            print(" done" if channel.IsConnected else "failed")
        print("\n")

    def identify(self, axis):
        """
        Method identifying the channel corresponding to axis by making the
        controller blink.
        """
        if axis in ("x", "y", "z"):
            channelno = self.axis_chan_mapping[axis]
            print("Identifying BPC303 channel %d (%s axis) -->" % (channelno, axis), end="")
            channel = self.__get_chan(axis)
            channel.IdentifyDevice()
            sleep(5)
            print(" done")
        else:
            print("Cannot identify BPC303 channel (axis invalid)")
        print("\n")

    def set_close_loop(self, yes):
        """
        Method setting all channels to closed loop or open loop control mode
        """
        print("Setting control mode to %s loop" % "closed" if yes else "open")
        mode = Piezo.PiezoControlModeTypes.CloseLoop if yes else Piezo.PiezoControlModeTypes.OpenLoop
        print(mode)
        for axis in ("x", "y", "z"):
            channel = self.__get_chan(axis)
            channel.SetPositionControlMode(mode)

    def zero(self, axis="all"):
        """
        Method performing a Set Zero operation on all channels or on a single
        one
        """
        print("Performing Set Zero:")
        if axis == "all":
            for ax in ("x", "y", "z"):
                self.__zero_axis(ax)
        elif axis in ("x", "y", "z"):
            self.__zero_axis(axis)
        else:
            print("\t- axis invalid)")

    def __zero_axis(self, axis):
        """
        Internal method performing a Set Zero operation on a single channel
        """
        if axis in ("x", "y", "z"):
            channelno = self.axis_chan_mapping[axis]
            print("\t- zeroing channel %d (%s axis) -->" % (channelno, axis), end="")
            channel = self.__get_chan(axis)
            channel.SetZero()
            print(" done")
        else:
            print("\t- axis invalid)")

    def set_position(self, x=None, y=None, z=None):  # define
        """
        Method setting the position in um if the channel is in
        Closed Loop mode
        """
        print("Setting Position:")
        pos = {"x": x, "y": y, "z": z}
        for axis, pos in pos.items():
            if pos is None:
                pass
            else:
                self.__set_axis_position(axis, pos)

    def __set_axis_position(self, axis, pos):  # define
        """
        Internal method setting the position in um if the channel is in
        Closed Loop mode
        """
        if axis in ("x", "y", "z"):
            print("\t- moving %s axis piezo to %f um -->" % (axis, pos), end="")
            channel = self.__get_chan(axis)
            channel.SetPosition(Decimal(pos))
            print(" done")
        else:
            print("\t- axis invalid)")

    def get_info(self):
        """
        Method returning a string containing the info on the controller and
        channels
        """
        print("Getting info")
        info = "Controller:\n%s\n" % self.controller.GetDeviceInfo().BuildDeviceDescription()
        sortedMap = sorted(self.axis_chan_mapping.items(), key=operator.itemgetter(1))
        for axis, channelno in sortedMap:
            channel = self.__get_chan(axis)
            chaninfo = channel.GetDeviceInfo().BuildDeviceDescription()
            piezoConfig = channel.GetPiezoConfiguration(self.deviceID)
            curDevSet = channel.PiezoDeviceSettings
            piezoInfo = "Piezo Configuration Name: %s, Piezo Max Voltage: %s" % (
                piezoConfig.DeviceSettingsName,
                curDevSet.OutputVoltageRange.MaxOutputVoltage.ToString())
            info += "Channel %d (%s axis):\n%s%s\n\n" % (channelno,
                                                         axis,
                                                         chaninfo,
                                                         piezoInfo)
        info += "\n"
        return info

    def shutdown(self):
        """
        Method for shutting down the connection to the physical instrument
        cleanly. The polling of the connected channels is stopped and the
        controller is disconnected.
        """
        print("Shutting BPC303 down:")
        if self.controller.IsConnected:
            for axis in ("x", "y", "z"):
                channelno = self.axis_chan_mapping[axis]
                print("\t- disconnecting channel %d (%s axis) -->" % (channelno, axis), end="")
                channel = self.__get_chan(axis)
                channel.StopPolling()
                channel.DisableDevice()
                print(" done")
            print("\t- disconnecting controller %s -->" % self.deviceID, end="")
            self.controller.Disconnect()
            print(" done")
        print("\t- done\n")

    def __del__(self):
        self.shutdown()

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()
        return True if exc_type is None else False

if __name__ == "__main__":
    print("\n")
    deviceID = "71858688"
    with BPC303(deviceID) as stage:
        stage.connect()
#        for axis in ("x", "y", "z"):
#            stage.identify(axis)
        print(stage.get_info())

    del stage
