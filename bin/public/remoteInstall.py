#!/usr/bin/env python
'''
Execute commands on the remote hosts defined in etc/install.cfg
  
Changelog:
  2011-01-29 - Daniel Lindh - Adding file header and comments
'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The syscon project"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel.lindh@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import subprocess, os, sys, time, paramiko, threading
import ssh, app
from exception import SettingsError

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  commands.add("remote-install", remote_install, "[server]", help="Connect to all servers, and run all commands defined in install.cfg.")

def remote_install(args):
  '''
  '''
  # Ask the user for all passwords that might be used in the remote install
  # so the installation can go on headless.
  app.init_all_passwords()
  
  remote_host=args[1]
  obj = RemoteInstall()
  obj.run(remote_host)
  
class RemoteInstall:
  '''Run commands defined in install.cfg on remote hosts through SSH.

  If the remote host is not yet installed/started/available, 
  the script will retry to connect every 5 second until it answers.
  
  '''
  servers={}
  
  # All hosts that are alive.
  alive={}

  # All hosts valid config status
  invalid_config={}

  # All hosts that has been installed.
  installed={}
  
  # Abort error
  abort_error={}
  
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
        is_not_installed=(host_name not in self.installed)        
        has_no_abort_errors=(host_name not in self.abort_error)
            
        if (is_not_installed and has_no_abort_errors):            
          t=threading.Thread(target=self._execute_commands, args=[host_name])
          t.start()          
      
      time.sleep(30)
    
    # Wait for all threads to finish  
    for t in threading.enumerate():
      if (threading.currentThread() != t):
        t.join()          

  def _execute_commands(self, host_name):
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
      self._install_fosh_on_remote_host(obj)
      self._execute(obj, host_name)                  
    except SettingsError, e:
      app.print_error(e, 2)
      
    except paramiko.AuthenticationException, e:
      app.print_error(e.args)
      self.abort_error[host_name]=e

  def _execute(self, obj, host_name):
    self.installed[host_name]="Progress"
    for option, command in app.get_commands(host_name):
      obj.ssh_exec(command)
    self.installed[host_name]="Yes"
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
      self.invalid_config[host_name]="Yes"
      if (not app.config.has_option(host_name, "server")):
        self.invalid_config[host_name]="No"
        app.print_verbose("In install.cfg, cant find ip for " + host_name)

  def _validate_alive(self, ssh_obj, host_name):
    if (ssh_obj.is_alive()):
      self.alive[host_name]="Yes"
    else:
      self.alive[host_name]="No"
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
      ("-"*19).ljust(20) +
      ("-"*14).ljust(15) +
      ("-"*5).ljust(6) +
      ("-"*12).ljust(13) +      
      ("-"*9).ljust(10) +
      ("-"*20).ljust(21) 
    )      
    for host_name in self.servers:       
      app.print_verbose("   " + 
        host_name.ljust(20) +
        app.get_ip(host_name).ljust(15)+
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
          
  def _install_fosh_on_remote_host(self, ssh):
    '''Rsync fosh to remote server, and install it
    
    '''
    app.print_verbose("Install fosh on remote host")
    ssh.rsync(os.path.abspath(sys.path[0] + "/../") + "/" ,  "/opt/fosh", "--exclude version.cfg")
    ssh.ssh_exec("/opt/fosh/bin/fosh.py install-fosh")
    
