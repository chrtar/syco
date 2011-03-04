#!/usr/bin/env python
'''
Application global wide helper functions.

Changelog:
110211 DALI - Removed dependency from General.py
110201 DALI - Some minor refactoring and commenting.
110129 DALI - Adding file header and comments.
'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The syscon project"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel.lindh@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import ConfigParser
import os
import re
import socket
import sys
import time
import subprocess

import passwordStore

#
#  Contains global functions and settings.
#

# The version of the syco script
version = "0.1"
parser = ''

# SYCO root folder.
SYCO_PATH = os.path.abspath(sys.path[0] + "/../") + "/"

# Scripts that should be availble in public repos.
SYCO_PUBLIC_PATH = os.path.abspath(SYCO_PATH + "/bin/public/")

# Scripts that should only be available in private repos.
SYCO_USR_PATH = os.path.abspath(SYCO_PATH + "/usr/")

# Etc (config) files.
SYCO_ETC_PATH = SYCO_PATH + "etc/"

# Files (rpm etc.) that should be installed by syco, are temporary stored here.
INSTALL_DIR = "/tmp/install/"

# All passwords used by syco are stored in this enrypted file.
PASSWORD_STORE_PATH = SYCO_PATH + "etc/passwordstore"

# When a general username is required.
SERVER_ADMIN_NAME = "syco"

# Logs will be sent to this email from the servers.
SERVER_ADMIN_EMAIL = "syscon@cybercow.se"

# String codes affecting output to shell.
BOLD = "\033[1m"
RESET = "\033[0;0m"

# Global accessible object containing all install.cfg options.
config_file_name = SYCO_ETC_PATH + "install.cfg"
config = ConfigParser.RawConfigParser()
config.read(config_file_name)

# Options set from commandline are stored here.
class Options:

  # Set by -v and -q.
  verbose = 1

  # Set by -f
  force = 0

options = Options()

def print_error(message, verbose_level=1):
  '''
  Print bold error text to stdout, affected by the verbolse level.

  All error print to screen done by syco should be done with this.

  '''
  print_verbose(message, verbose_level=verbose_level, caption=BOLD + "Error: " + RESET)

def print_verbose(message, verbose_level=1, caption="", new_line=True, enable_caption=True):
  '''
  Print a text to the stdout, affected by the verbose level.

  All print to screen done by syco should be done with this.

  #TODO: The caption are not always written ok when using new_line=False, see example at the bottom.

  '''
  if (caption):
    caption += " "
  caption = time.strftime('%Y-%m-%d %H:%M:%S') + " - " + socket.gethostname() + " - " + caption

  messages = []
  if (not isinstance(message, tuple)):
    messages.append(message)
  else:
    messages = message

  # Output will look like
  # fo-tp-system: Caption This is a message
  for msg in messages:
    if (len(str(msg)) > 0):
      msg = re.sub("[\n]", "\n" + caption, str(msg))

    if (options.verbose >= verbose_level):
      msg = str(msg)
      if (enable_caption):
        msg = caption + msg

      if (new_line):
        msg += "\n"

      sys.stdout.write(msg)
      sys.stdout.flush()

def _get_password(service, user_name):
  '''
  Get a password from the password store.

  '''
  if (not _get_password.password_store):
    _get_password.password_store = passwordStore.PasswordStore(PASSWORD_STORE_PATH)
  password = _get_password.password_store.get_password(service, user_name)
  _get_password.password_store.save_password_file()
  return password

_get_password.password_store = None

def get_root_password():
  '''The linux shell root password.'''
  return _get_password("linux", "root")

def get_root_password_hash():
  '''
  Openssl hash of the linux root password.

  '''
  root_password = get_root_password()
  p = subprocess.Popen("openssl passwd -1 -salt 'sa#Gnxw4' '" + root_password + "'", shell=True)
  hash_root_password, stderr = p.communicate()
  return hash_root_password

def get_svn_password():
  '''The svn password for user syscon_svn'''
  return _get_password("svn", "syscon")

def get_glassfish_master_password():
  '''Used to sign keystore, never transfered over network.'''
  return _get_password("glassfish", "master")

def get_glassfish_admin_password():
  '''Login to asadmin or web admin console'''
  return _get_password("glassfish", "admin")

def get_mysql_root_password():
  '''The root password for the mysql service.'''
  return _get_password("mysql", "root")

def get_mysql_fp_integration_password():
  '''A user password for the mysql service, used by Farepayment'''
  return _get_password("mysql", "fp_integration")

def get_mysql_fp_stable_password():
  '''A user password for the mysql service, used by Farepayment'''
  return _get_password("mysql", "fp_stable")

def get_mysql_fp_qa_password():
  '''A user password for the mysql service, used by Farepayment'''
  return _get_password("mysql", "fp_qa")

def get_mysql_fp_production_password():
  '''A user password for the mysql service, used by Farepayment'''
  return _get_password("mysql", "fp_production")

def init_mysql_passwords():
  get_mysql_root_password()
  get_mysql_fp_integration_password()
  get_mysql_fp_stable_password()
  get_mysql_fp_qa_password()
  get_mysql_fp_production_password()

def init_all_passwords():
  '''
  Ask the user for all passwords used by syco, and add to passwordstore.

  '''
  get_root_password()
  get_svn_password()
  get_glassfish_master_password()
  get_glassfish_admin_password()
  init_mysql_passwords()

def get_option(section, option):
  '''
  Get an option from the install.cfg file.

  '''
  if (config.has_section(section)):
    if (config.has_option(section, option)):
      return config.get(section, option)
    else:
      raise Exception("Can't find option '" + option + "' in section '" + section + "' in install.cfg")
  else:
    raise Exception("Can't find section '" + section + "' in install.cfg")

def get_mysql_primary_master():
  '''IP or hostname for primary mysql server.'''
  return get_ip(get_option("general", "mysql.primary_master"))

def get_mysql_secondary_master():
  '''IP or hostname for secondary mysql server.'''
  return get_ip(get_option("general", "mysql.secondary_master"))

def get_installation_server():
  '''The hostname of the installation server.'''
  return get_option("general", "installation_server")

def get_installation_server_ip():
  '''The ip of the installation server.'''
  return get_ip(get_installation_server())

def get_dns_resolvers():
  '''ip list of dns resolvers that are configured on all servers.'''
  return get_option("general", "dns_resolvers")

def get_ip(host_name):
  '''Get ip for a specific host, as it is defined in install.cfg'''
  return get_option(host_name, "server")

def get_mac(host_name):
  '''Get network mac address for a specific host, as it is defined in install.cfg'''
  return get_option(host_name, "mac")

def get_ram(host_name):
  '''Get the amount of ram in MB that are used for a specific kvm host, as it is defined in install.cfg.'''
  return get_option(host_name, "ram")

def get_cpu(host_name):
  '''Get the number of cores that are used for a specific kvm host, as it is defined in install.cfg'''
  return get_option(host_name, "cpu")

def get_disk_var(host_name):
  '''Get the size of the var partion in GB that are used for a specific kvm host, as it is defined in install.cfg'''
  return get_option(host_name, "disk_var")

def get_servers():
  '''A list of all servers that are defined in install.cfg.'''
  servers = config.sections()
  servers.remove("general")
  return servers

def get_commands(host_name):
  '''Get all commands that should be executed on a host'''
  options = []

  if (config.has_section(host_name)):
    for option, value in config.items(host_name):
      option = option.lower()
      if "command" in option:
        options.append([option, value])

  return sorted(options)

def get_hosts():
  '''Get the hostname of all kvm hosts.'''
  hosts = []

  for host_name in get_servers():
    if is_host(host_name):
      hosts.append(host_name)
  return sorted(hosts)

def is_host(host_name):
  if (config.has_section(host_name)):
    for option, value in config.items(host_name):
      if ("guest" in option):
        return True
  return False

def get_guests(host_name):
  '''Get the hostname of all guests that should be installed on the kvm host name.'''
  guests = []

  if (config.has_section(host_name)):
    for option, value in config.items(host_name):
      if ("guest" in option):
        guests.append(value)

  return sorted(guests)


if (__name__ == "__main__"):
  print_error("This is a error.")
  print_verbose("This is some text")
  long_text = '''First line
New line

Another new line

last new line'''
  print_verbose(long_text, caption="fo-tp-vh01", new_line=False)
  print_verbose(", and some more text on the last line", caption="fo-tp-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=True, enable_caption=False)

