#!/usr/bin/env python
'''
control MAVLink2 signing
'''    

from pymavlink import mavutil
import time, struct, math, sys

from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_util

if mp_util.has_wxpython:
    from MAVProxy.modules.lib.mp_menu import *

class SigningModule(mp_module.MPModule):

    def __init__(self, mpstate):
        super(SigningModule, self).__init__(mpstate, "link", "link control", public=True)
        self.add_command('signing', self.cmd_signing, "signing control",
                         ["<setup|key>"])
        self.allow = None

    def cmd_signing(self, args):
        '''handle link commands'''
        usage = "signing: <setup|key> passphrase"
        if len(args) == 0:
            print(usage)
        elif args[0] == 'setup':
            self.cmd_signing_setup(args[1:])
        elif args[0] == 'key':
            self.cmd_signing_key(args[1:])
        else:
            print(usage)

    def passphrase_to_key(self, passphrase):
        '''convert a passphrase to a 32 byte key'''
        import hashlib
        h = hashlib.new('sha256')
        h.update(passphrase)
        return h.digest()

    def cmd_signing_setup(self, args):
        '''setup signing key on board'''
        if len(args) == 0:
            print("usage: signing setup passphrase")
            return
        passphrase = args[0]
        key = self.passphrase_to_key(passphrase)
        secret_key = []
        for b in key:
            secret_key.append(ord(b))

        epoch_offset = 1420070400
        now = max(time.time(), epoch_offset)
        initial_timestamp = int((now - epoch_offset)*1e5)
        self.master.mav.setup_signing_send(self.target_system, self.target_component,
                                           secret_key, initial_timestamp)
        print("Sent secret_key")
        self.cmd_signing_key([passphrase])


    def allow_unsigned(self, mav, dialect, msgId):
        '''see if an unsigned packet should be allowed'''
        if self.allow is None:
            self.allow = {
                (mavutil.mavlink.MAVLINK_MSG_DIALECT_RADIO_STATUS, mavutil.mavlink.MAVLINK_MSG_ID_RADIO_STATUS) : True 
                }
        if (dialect,msgId) in self.allow:
            return True
        if self.settings.allow_unsigned:
            return True
        return False

    def cmd_signing_key(self, args):
        '''set signing key on connection'''
        if len(args) == 0:
            print("usage: signing setup passphrase")
            return
        passphrase = args[0]
        key = self.passphrase_to_key(passphrase)
        self.master.setup_signing(key, sign_outgoing=True, allow_unsigned_callback=self.allow_unsigned)
        print("Setup signing key")
        
def init(mpstate):
    '''initialise module'''
    return SigningModule(mpstate)
