import sys
import os.path
import optparse

import wasp.communication

_thisdir = os.path.dirname(os.path.abspath(__file__))

NAME = "Wasp Groundstation"
VERSION = "0.1"

IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    IS_INSTALLED = sys.argv[0].endswith(".exe")
    if IS_INSTALLED:
        #report a dir relative to the executable. these values
        #must be kept in sync with the py2exe configuration
        DATA_DIR =      os.environ.get("WASP_DATA_DIR",   os.path.join("..", "share","groundstation"))
        PLUGIN_DIR =    os.environ.get("WASP_PLUGIN_DIR", os.path.join("..", "lib", "groundstation", "plugins"))
        CONFIG_DIR =    os.environ.get("WASP_CONFIG_DIR", os.path.join("..", "etc", "groundstation", "config"))
    else:
        #report absolute dir
        DATA_DIR =      os.environ.get("WASP_DATA_DIR",   os.path.abspath(os.path.join(_thisdir, "..", "data")))
        PLUGIN_DIR =    os.environ.get("WASP_PLUGIN_DIR", os.path.abspath(os.path.join(_thisdir, "plugins")))
        CONFIG_DIR =    os.environ.get("WASP_CONFIG_DIR", os.path.abspath(os.path.join(_thisdir, "..", "..", "onboard", "config")))
else:
    #FIXME: dont support running installed yet..
    IS_INSTALLED = False
    DATA_DIR =          os.environ.get("WASP_DATA_DIR", os.path.join(_thisdir, "..", "data"))
    PLUGIN_DIR =        os.environ.get("WASP_PLUGIN_DIR", os.path.join(_thisdir, "plugins"))
    CONFIG_DIR =        os.environ.get("WASP_CONFIG_DIR", os.path.join(_thisdir, "..", "..", "onboard", "config"))

USER_CONFIG_DIR = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.environ.get("HOME","."), ".config", "wasp"))

del(_thisdir)

def linspace(xmin, xmax, N):
    """
    Return a list of N linearly spaced floats in
    the range [xmin,xmax], i.e. including the endpoints
    """
    if N==1: return [xmax]
    dx = (xmax-xmin)/(N-1)
    return [xmin] + [xmin + (dx*float(i)) for i in range(1,N)]

def user_file_path(filename):
    """
    Returns a file path with the given filename,
    on the users Desktop
    """
    return os.path.join(
                os.path.expanduser("~"),
                "Desktop",
                filename)

def scale_to_range(val, oldrange, newrange=(0.0,1.0)):
    #make 0 based
    tmpoldmax = float(oldrange[1]) - oldrange[0]
    tmpnewmax = float(newrange[1]) - newrange[0]

    #scale to new range
    val = ((val - oldrange[0]) / tmpoldmax) * tmpnewmax

    #offset from new min
    val += newrange[0]

    return val

class _SourceOptionParser(optparse.OptionParser):
    #override parse_args so that -t is the same as --source=test
    #it is easier to do it this was instead of with a 
    #optparse callback
    def parse_args(self):
        options, args = optparse.OptionParser.parse_args(self)
        if options.use_test_source:
            options.source = "test"
        else:
            #strip the optional args from the source and check it is valid
            source = options.source.split(":")
            if source[0] not in wasp.communication.get_available_sources():
                options.source = "test"
        return options, args
                
def get_default_command_line_parser(include_prefs, include_plugins, include_sources, messages_name="messages.xml", settings_name="settings.xml", preferences_name="groundstation.ini", ping_time=2):
    default_messages = os.path.join(CONFIG_DIR, messages_name)
    default_settings = os.path.join(CONFIG_DIR, settings_name)

    if include_prefs:
        if not os.path.exists(USER_CONFIG_DIR):
            os.makedirs(USER_CONFIG_DIR)
        prefs = os.path.join(USER_CONFIG_DIR, preferences_name)

    if include_sources:
        parser = _SourceOptionParser()
    else:
        parser = optparse.OptionParser()
    parser.add_option("-m", "--messages",
                    default=default_messages,
                    help="Messages xml file", metavar="FILE")
    parser.add_option("-s", "--settings",
                    default=default_settings,
                    help="Settings xml file", metavar="FILE")
    parser.add_option("-d", "--debug",
                    action="store_true",
                    help="Print extra debugging information")
    parser.add_option("-g", "--ping-time",
                    type="int", default=ping_time, metavar="n",
                    help="Send ping every n seconds, 0 disables")

    if include_prefs:
        parser.add_option("-p", "--preferences",
                        default=prefs,
                        help="User preferences file", metavar="FILE")
    if include_plugins:
        parser.add_option("-P", "--plugin-dir",
                        default=PLUGIN_DIR,
                        help="Directory to load plugins from", metavar="DIRECTORY")
        parser.add_option("-D", "--disable-plugins",
                        action="store_true", default=False,
                        help="Disable loading plugins")
    if include_sources:
        parser.add_option("-t", "--use-test-source",
                        action="store_true", default=False,
                        help="Use a test source, equiv to --source=test")
        parser.add_option("-S", "--source",
                        default="serial",
                        help="Source of uav data (%s)" % ",".join(wasp.communication.get_available_sources()),
                        metavar="SOURCE[opt_1:opt_2:opt_n]")

    return parser

