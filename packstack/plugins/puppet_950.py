"""
Installs and configures puppet
"""
import sys
import logging
import os
import platform
import time

import packstack.installer.common_utils as utils
from packstack.installer import basedefs, output_messages
from packstack.installer.exceptions import ScriptRuntimeError

from packstack.modules.ospluginutils import gethostlist,\
                                            manifestfiles,\
                                            validate_puppet_logfile

# Controller object will be initialized from main flow
controller = None

# Plugin name
PLUGIN_NAME = "OSPUPPET"
PLUGIN_NAME_COLORED = utils.getColoredText(PLUGIN_NAME, basedefs.BLUE)

logging.debug("plugin %s loaded", __name__)

PUPPETDIR = os.path.abspath(os.path.join(basedefs.DIR_PROJECT_DIR, 'puppet'))
MODULEDIR = os.path.join(PUPPETDIR, "modules")


def initConfig(controllerObject):
    global controller
    controller = controllerObject
    logging.debug("Adding OpenStack Puppet configuration")
    paramsList = [
                 ]

    groupDict = {"GROUP_NAME"            : "PUPPET",
                 "DESCRIPTION"           : "Puppet Config parameters",
                 "PRE_CONDITION"         : utils.returnYes,
                 "PRE_CONDITION_MATCH"   : "yes",
                 "POST_CONDITION"        : False,
                 "POST_CONDITION_MATCH"  : True}

    controller.addGroup(groupDict, paramsList)


def initSequences(controller):
    puppetpresteps = [
             {'title': 'Clean Up', 'functions':[runCleanup]},
    ]
    controller.insertSequence("Clean Up", [], [], puppetpresteps, index=0)

    puppetsteps = [
             {'title': 'Installing Dependencies', 'functions':[installdeps]},
             {'title': 'Copying Puppet modules and manifests', 'functions':[copyPuppetModules]},
             {'title': 'Applying Puppet manifests', 'functions':[applyPuppetManifest]},
    ]
    controller.addSequence("Puppet", [], [], puppetsteps)


def runCleanup():
    localserver = utils.ScriptRunner()
    localserver.append("rm -rf %s/*pp" % basedefs.PUPPET_MANIFEST_DIR)
    localserver.execute()


def installdeps():
    for hostname in gethostlist(controller.CONF):
        server = utils.ScriptRunner(hostname)
        for package in ("puppet", "openssh-clients", "tar"):
            server.append("rpm -q %s || yum install -y %s" % (package, package))
        server.execute()


def copyPuppetModules():
    # write puppet manifest to disk
    manifestfiles.writeManifests()

    server = utils.ScriptRunner()
    tar_opts = ""
    if platform.linux_distribution()[0] == "Fedora":
        tar_opts += "--exclude create_resources "
    for hostname in gethostlist(controller.CONF):
        host_dir = controller.temp_map[hostname]
        puppet_dir = os.path.join(host_dir, basedefs.PUPPET_MANIFEST_RELATIVE)
        server.append("cd %s/puppet" % basedefs.DIR_PROJECT_DIR)
        server.append("tar %s --dereference -cpzf - modules facts | "
                      "ssh -o StrictHostKeyChecking=no "
                          "-o UserKnownHostsFile=/dev/null "
                          "root@%s tar -C %s -xpzf -" % (tar_opts, hostname, host_dir))
        server.append("cd %s" % basedefs.PUPPET_MANIFEST_DIR)
        server.append("tar %s --dereference -cpzf - ../manifests | "
                      "ssh -o StrictHostKeyChecking=no "
                          "-o UserKnownHostsFile=/dev/null "
                          "root@%s tar -C %s -xpzf -" % (tar_opts, hostname, host_dir))

        for path, localname in controller.resources.get(hostname, []):
            server.append("scp -o StrictHostKeyChecking=no "
                "-o UserKnownHostsFile=/dev/null %s root@%s:%s/resources/%s" %
                (path, hostname, host_dir, localname))

    server.execute()


def waitforpuppet(currently_running):
    log_len = 0
    twirl = ["-","\\","|","/"]
    while currently_running:
        for hostname, finished_logfile in currently_running:
            log_file = os.path.splitext(os.path.basename(finished_logfile))[0]
            space_len = basedefs.SPACE_LEN - len(log_file)
            if len(log_file) > log_len:
                log_len = len(log_file)
            if sys.stdout.isatty():
                twirl = twirl[-1:] + twirl[:-1]
                sys.stdout.write(("\rTesting if puppet apply is finished : %s" % log_file).ljust(40 + log_len))
                sys.stdout.write("[ %s ]" % twirl[0])
                sys.stdout.flush()
            try:
                # Once a remote puppet run has finished, we retrieve the log
                # file and check it for errors
                local_server = utils.ScriptRunner()
                log = os.path.join(basedefs.PUPPET_MANIFEST_DIR,
                                   os.path.basename(finished_logfile).replace(".finished", ".log"))
                local_server.append('scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@%s:%s %s' % (hostname, finished_logfile, log))
                # Errors are expected here if the puppet run isn't finished so we suppress logging them
                local_server.execute(logerrors=False)

                # If we got to this point the puppet apply has finished
                currently_running.remove((hostname, finished_logfile))

                # clean off the last "testing apply" msg
                if sys.stdout.isatty():
                    sys.stdout.write(("\r").ljust(45 + log_len))

            except ScriptRuntimeError, e:
                # the test raises an exception if the file doesn't exist yet
                # TO-DO: We need to start testing 'e' for unexpected exceptions
                time.sleep(3)
                continue

            # check the log file for errors
            validate_puppet_logfile(log)
            sys.stdout.write(("\r%s : " % log_file).ljust(basedefs.SPACE_LEN))
            print ("[ " + utils.getColoredText(output_messages.INFO_DONE, basedefs.GREEN) + " ]")


def applyPuppetManifest():
    print
    currently_running = []
    lastmarker = None
    for manifest, marker in manifestfiles.getFiles():
        # if the marker has changed then we don't want to proceed until
        # all of the previous puppet runs have finished
        if lastmarker != None and lastmarker != marker:
            waitforpuppet(currently_running)
        lastmarker = marker

        for hostname in gethostlist(controller.CONF):
            if "%s_" % hostname not in manifest:
                continue

            host_dir = controller.temp_map[hostname]
            print "Applying " + manifest
            server = utils.ScriptRunner(hostname)

            man_path = os.path.join(controller.temp_map[hostname],
                                    basedefs.PUPPET_MANIFEST_RELATIVE,
                                    manifest)

            running_logfile = "%s.running" % man_path
            finished_logfile = "%s.finished" % man_path
            currently_running.append((hostname, finished_logfile))
            if not manifest.endswith('_horizon.pp'):
                server.append("export FACTERLIB=$FACTERLIB:%s/facts" % host_dir)
            server.append("touch %s" % running_logfile)
            server.append("chmod 600 %s" % running_logfile)
            server.append("export PACKSTACK_VAR_DIR=%s" % host_dir)
            command = "( flock %s/ps.lock puppet apply --modulepath %s/modules %s > %s 2>&1 < /dev/null ; mv %s %s ) > /dev/null 2>&1 < /dev/null &" % (host_dir, host_dir, man_path, running_logfile, running_logfile, finished_logfile)
            server.append(command)
            server.execute()

    # wait for outstanding puppet runs befor exiting
    waitforpuppet(currently_running)
