import time
import gi
import numpy as np
from time import sleep as _sleep

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")

from gi.repository import Gst, GstApp, GLib

# _ = GstApp

# gst-launch-1.0 appsrc ! audioconvert ! audio/x-raw,format=S16LE,channels=1,rate=16000 ! fakesink silent = TRUE

PIPELINE = """appsrc name=src ! audio/x-raw,format=S16LE,channels=1,rate=22050,layout=interleaved ! audioconvert ! pulsesink"""
CAPS = "audio/x-raw,format=S16LE,channels=1,rate=22050,layout=interleaved"

def ndarray_to_gst_buffer(arr: list[np.float32]) -> Gst.Buffer:
    """Convert numpy array to Gst.Buffer"""
    #buf = np.array(arr)
    buf = np.array(arr) * 32767
    buf = (np.rint(buf)).astype(np.int16)
    return Gst.Buffer.new_wrapped(buf.tobytes())


class GStreamerSource(object):
    def __init__(self, callback=lambda : True):
        Gst.init(None)
        self._wait = True
        self.callback = callback
        self.main_loop = GLib.MainLoop()

        self.player = Gst.parse_launch(PIPELINE)
        self.player.set_auto_flush_bus(True)
        self.appsrc = self.player.get_by_name("src")

        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self._on_message)

    def _on_message(self, bus, message):
        """ Currently not used, see send_chunk """
        t = message.type
        if t == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            print("EOS")
            self.callback()
        elif t == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("Error: %s" % err, debug)
            self.callback()

    def send_chunk(self, buffer, duration_ms=0):
        self.player.set_state(Gst.State.NULL)

        result = self.player.set_state(Gst.State.PLAYING)
        if result != Gst.StateChangeReturn.ASYNC:
            raise RuntimeError('player.set_state returned: %r' % str(result))
        result = self.appsrc.push_buffer(ndarray_to_gst_buffer(buffer))
        result = self.appsrc.end_of_stream()
        # in nanoseconds
        timeout = (10 + round(len(buffer) / 22.050)) * 1_000_000
        bus = self.player.get_bus()
        if self._wait:
            #bus.add_signal_watch_full(GLib.PRIORITY_HIGH)
            #bus.connect('message', self._on_message)  # call back on end

            bus.poll(Gst.MessageType.EOS, timeout)  # wait for end
            self.player.set_state(Gst.State.NULL)
            #_sleep(round(len(buffer) / 22050 + .1, 3))
        return result

    def stop(self):
        self.player.set_state(Gst.State.NULL)

####### Unused code, several attempts to make it work or test gstreamer #####

    def create_pipeline(self):
        """ Create a pipeline "by hand" """
        self.player = Gst.Pipeline.new("player")
        #self.test_source()

        self.tts_source()
        self.conv = Gst.ElementFactory.make("audioconvert", "converter")
        self.sink = Gst.ElementFactory.make("pulsesink", "pulse-output")
        self.player.add(self.appsrc)
        self.player.add(self.conv)
        self.player.add(self.sink)
        self.appsrc.link(self.conv)
        self.conv.link(self.sink)

    def tts_source(self):
        self.appsrc = Gst.ElementFactory.make("appsrc", "app-source")
        self.appsrc.set_property("block", False)
        caps = Gst.Caps.from_string(CAPS)
        self.appsrc.set_property("caps", caps)

    def test_source(self):
        sample_rate=22050
        volume=0.2
        frequency_hz=880
        duration_ms=100000

        self.appsrc = Gst.ElementFactory.make("audiotestsrc", "source")
        self.appsrc.set_property("wave", 0)  # Audio-test-src-wave = sine (0)
        self.appsrc.set_property("freq", frequency_hz)
        self.appsrc.set_property("volume", volume)

        # calculating duration is quite clumsy, not sure if correct:
        sfactor = 44_100/sample_rate
        num_buffers = round(duration_ms/10)  # take one zero from here
        samples_per = round((sample_rate * sfactor)/100)  # add here

        #~ print(' * num-buffers ', num_buffers)
        #~ print(' * samples per buffer ', samples_per)
        #~ print('   = %2.4f secs' % est_seconds)
        self.appsrc.set_property("num-buffers", num_buffers)
        self.appsrc.set_property("samplesperbuffer", samples_per)

    def play_sound(self):
        result = self.player.set_state(Gst.State.PLAYING)
        if result != Gst.StateChangeReturn.ASYNC:
            raise RuntimeError('player.set_state returned: %r' % result)
        if self._wait:
            _sleep(round(1 + .1, 3))


def test(data, size):
    print("streaming finished ")

if __name__ == '__main__':
    gms = GStreamerSource(callback=test)
    gms.play_sound()
