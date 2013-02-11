"""
Installs and configures an OpenStack Client
"""

import logging

import packstack.installer.engine_validators as validate
import packstack.installer.engine_processors as process
from packstack.installer import basedefs, output_messages
import packstack.installer.common_utils as utils

from packstack.modules.ospluginutils import gethostlist,\
                                            getManifestTemplate, \
                                            appendManifestFile

# Controller object will be initialized from main flow
controller = None

# Plugin name
PLUGIN_NAME = "OS-POSTSCRIPT"

logging.debug("plugin %s loaded", __name__)

def initConfig(controllerObject):
    global controller
    controller = controllerObject
    logging.debug("Executing post run scripts")


    groupDict = {"GROUP_NAME"            : "POSTSCRIPT",
                 "DESCRIPTION"           : "POSTSCRIPT Config parameters",
                 "PRE_CONDITION"         : utils.returnYes,
                 "PRE_CONDITION_MATCH"   : "yes",
                 "POST_CONDITION"        : False,
                 "POST_CONDITION_MATCH"  : True}

    controller.addGroup(groupDict, [])


def initSequences(controller):
    osclientsteps = [
             {'title': 'Adding post install manifest entries', 'functions':[createmanifest]}
    ]
    controller.addSequence("Running post install scripts", [], [], osclientsteps)

def createmanifest():
    for hostname in gethostlist(controller.CONF):
        manifestfile = "%s_postscript.pp" % hostname
        manifestdata = getManifestTemplate("postscript.pp")
        appendManifestFile(manifestfile, manifestdata, 'postscript')
