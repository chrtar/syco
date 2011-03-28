#!/usr/bin/env python
'''
Execute commands on the remote hosts defined in etc/install.cfg

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import socket
import sys
import threading
import time

import app
import general
import ssh
from exception import SettingsError

# Need to be after ssh, because ssh.py installs pexpect
import pexpect
import pxssh

def build_commands(commands):
  commands.add("remote-install", remote_install, "[hostname]", help="Connect to all servers, and run all commands defined in install.cfg.")
  commands.add("install-local", install_local, "[hostname]", help="Run all commands defined in install.cfg.")

def remote_install(args):
  '''
  '''
  # Ask the user for all passwords that might be used in the remote install
  # so the installation can go on headless.
  app.init_all_passwords()

  remote_host = args[1]
  obj = RemoteInstall()
  obj.run(remote_host)

def install_local(args):
  # Ask the user for all passwords that might be used in the remote install
  # so the installation can go on headless.
  app.init_all_passwords()

  host_name = ""
  if len(args) == 2:
    host_name = args[1]

  if host_name == "":
    host_name = socket.gethostname()
  app.print_verbose("Install all commands defined in install.cfg for host " + host_name + ".")
  
  commands = app.get_commands(host_name)
  if len(commands) > 0:
    for command in commands:
      general.shell_exec(command)
  else:
    app.print_error("No commands for this host.")

class RemoteInstall:
  '''
  Run commands defined in install.cfg on remote hosts through SSH.

  If the remote host is not yet installed/started/available,
  the script will retry to connect every 30 second until it answers.

  '''
  servers = {}

  # All hosts that are alive.
  alive = {}

  # All hosts valid config status
  invalid_config = {}

  # All hosts that has been installed.
  installed = {}

  # Abort error
  abort_error = {}

  def run(self, host_name=""):
    '''
    Start the installation

    '''
    self._set_servers(host_name)
    self._validate_install_config()

    while(len(self.servers) != len(self.installed)):
      self._print_install_stat()
      app.print_verbose(str(threading.activeCount()) + " threads are running.")

      for host_name in self.servers:
        if (not self._is_installed(host_name) and not self.has_abort_errors(host_name)):
          self.installed[host_name] = "Progress"
          t = threading.Thread(target=self._install_host, args=[host_name])
          t.start()

      # End script if all threads are done, otherwise sleep for 30
      for i in range(30):
        time.sleep(1)
        if len(self.servers) != len(self.installed):
          break

    # Wait for all threads to finish
    for t in threading.enumerate():
      if (threading.currentThread() != t):
        t.join()

  def _is_installed(self, host_name):
    if (host_name in self.installed and self.installed[host_name] == "Yes"):
      return True
    else:
      return False

  def has_abort_errors(self, host_name):
    return (host_name in self.abort_error)

  def _install_host(self, host_name):
    '''
    Execute the commands on the remote host.

    Create one process for each remote host.

    '''
    try:
      server = app.config.get(host_name, "server")
      app.print_verbose("Try to install " + host_name + " (" + server + ")", 2)

      obj = ssh.Ssh(server, app.get_root_password())
      self._validate_alive(obj, host_name)
      app.print_verbose("========================================================================================")
      app.print_verbose("=== Update " + host_name + " (" + server + ")")
      app.print_verbose("========================================================================================")

      obj.install_ssh_key()
      self._install_syco_on_remote_host(obj)      
      self._execute_commands(obj, host_name)

    except SettingsError, e:
      app.print_error(e, 2)

      # Remove progress state.
      del(self.installed[host_name])

  def _install_syco_on_remote_host(self, ssh):
    '''
    Rsync syco to remote server, and install it

    '''
    app.print_verbose("Install syco on remote host")
    ssh.rsync(app.SYCO_PATH, app.SYCO_PATH, "--exclude version.cfg")
    ssh.ssh_exec(app.SYCO_PATH + "bin/syco.py install-syco")

  def _execute_commands(self, obj, host_name):
    commands = app.get_commands(host_name)

    while(len(commands) != 0):
      try:
        obj.ssh_exec(commands[0])
        commands.pop(0)
      except ssh.SSHTerminatedException, e:
        app.print_error("SSHTerminatedException on host " + host_name + " with command " + commands[0])
        obj.wait_until_alive()
        
      except pexpect.EOF, e:
        app.print_error("pexpect.EOF on host " + host_name + " with command " + commands[0])

      except pxssh.ExceptionPxssh, e:
        app.print_error("pxssh.ExceptionPxssh on host " + host_name + " with command " + commands[0] + ", might be because the remote host rebooted.")
      
    self.installed[host_name] = "Yes"
    app.print_verbose("")

  def _set_servers(self, host_name):
    '''
    Set servers/hosts to perform the remote install on.

    '''
    if (host_name):
      self.servers = [host_name]
    else:
      self.servers = app.get_servers()

    sorted(self.servers)

  def _validate_install_config(self):
    '''
    Validate all host options in install.cfg.

    Print error messages in verbose mode.

    '''
    for host_name in self.servers:
      self.invalid_config[host_name] = "Yes"
      if (not app.config.has_option(host_name, "server")):
        self.invalid_config[host_name] = "No"
        app.print_verbose("In install.cfg, cant find ip for " + host_name)

  def _validate_alive(self, ssh_obj, host_name):
    if (ssh_obj.is_alive()):
      self.alive[host_name] = "Yes"
    else:
      self.alive[host_name] = "No"
      raise SettingsError(host_name + " is not alive.")

  def _print_install_stat(self):
    '''
    Display information about the servers that are being installed.

    '''
    app.print_verbose(repr(len(self.servers)) + " servers left to install.")
    app.print_verbose("   " +
      "SERVER NAME".ljust(20) +
      "IP".ljust(15) +
      "ALIVE".ljust(6) +
      "VALID CONFIG".ljust(13) +
      "INSTALLED".ljust(10) +
      "ABORT ERROR".ljust(20)
      )
    app.print_verbose("   " +
      ("-" * 19).ljust(20) +
      ("-" * 14).ljust(15) +
      ("-" * 5).ljust(6) +
      ("-" * 12).ljust(13) +
      ("-" * 9).ljust(10) +
      ("-" * 20).ljust(21)
      )
    for host_name in self.servers:
      app.print_verbose("   " +
        host_name.ljust(20) +
        app.get_ip(host_name).ljust(15) +
        self._get_alive(host_name).ljust(6) +
        self._get_invalid_config(host_name).ljust(13) +
        self._get_installed(host_name).ljust(10) +
        self._get_abort_errors(host_name)
        )
    app.print_verbose("")

  def _get_alive(self, host_name):
    if (host_name in self.alive):
      return self.alive[host_name]
    else:
      return "?"

  def _get_invalid_config(self, host_name):
    if (host_name in self.invalid_config):
      return self.invalid_config[host_name]
    else:
      return "?"

  def _get_installed(self, host_name):
    if (host_name in self.installed):
      return self.installed[host_name]
    else:
      return "No"

  def _get_abort_errors(self, host_name):
    if (host_name in self.abort_error):
      return str(self.abort_error[host_name])
    else:
      return "?"