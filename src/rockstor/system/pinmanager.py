"""
Copyright (c) 2012-2016 RockStor, Inc. <http://rockstor.com>
This file is part of RockStor.

RockStor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

RockStor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import random, string
from hashlib import md5
from pwd import getpwnam
from storageadmin.models import (Pincard, EmailClient, User)
from system.users import (smbpasswd, usermod)
from django.contrib.auth.models import User as DjangoUser


def reset_password(uname, uid, pinlist):
    
    pass_change_enabled = True
    
    #Loop through pinlist, get md5 digest of every pin and
    #and compare with Pincard model values
    for pin_index, pin_value in pinlist.items():
        
        pin_value_md5 = md5(pin_value).hexdigest()
        if not Pincard.objects.filter(
                        user=int(uid)).filter(pin_number=int(pin_index)).filter(
                        pin_code=pin_value_md5).exists():
            
            pass_change_enabled = False
            break
    
    if pass_change_enabled:
        
        #Generate new 8 chars random password
        new_password = ''.join(random.choice(string.letters + string.digits) for _ in range(8))
        #Reset system password
        usermod(uname, new_password)
        
        #If user is a managed one we have to reset smb pass too
        if User.objects.filter(username=uname).exists():
            smbpasswd(uname, new_password)
        #If user is a Django user reset pass
        if DjangoUser.objects.filter(username=uname).exists():
            duser = DjangoUser.objects.get(username=uname)
            duser.set_password(new_password)
            duser.save()
        
        password_message = 'Password reset succeeded. New current password is %s' % new_password
    
    else:
        
        password_message = 'Password change failed'
    
    return password_message
    
def reset_random_pins(uid):
    
    #Random get 4 pins from Pincard for selected user
    random_pins = random.sample(range(1,24),4)
    pin_rows = list(Pincard.objects.filter(user=int(uid)).filter(pin_number__in=random_pins).values('pin_number'))
    
    return pin_rows

def username_to_uid(username):
    
    #Convert from username to user uid
    try:
        user_uid = getpwnam(username).pw_uid
    except KeyError:
        # user doesn't exist
        user_uid = None

    return user_uid

def email_notification_enabled():

    #Check for email notifications state
    #required for password reset over root user (Pincard + otp via mail)
    try:
        mail_accounts = EmailClient.objects.filter().count()
    except EmailClient.DoesNotExist:
        mail_accounts = 0
        
    has_mail = True if mail_accounts > 0 else False

    return has_mail

def has_pincard(user):

    #Check if user has already a Pincard
    #Added uid_field to dinamically handle passed data:
    #user can be and User obcject or directly a uid
    uid_field = user.uid if hasattr(user, 'uid') else user
    try:
        pins = Pincard.objects.filter(user=int(uid_field)).count()
    except Pincard.DoesNotExist:
        pins = 0
    
    has_pincard = True if (pins == 24) else False

    return has_pincard

def pincard_states(user):

    #If user has a Pincard that means already allowed to have one, so avoid computing
    #If selected user is a managed one allowed to have a pincard_allowed
    #If user is uid 0 (root) and mail notifications enabled -> ok Pincard
    #Otherwise 'otp' third state : allowed to have a Pincard, but mail notifications required
    pincard_allowed = 'no'
    pincard_present = has_pincard(user)
    if user.managed_user:
        pincard_allowed = 'yes'
    else:
        if int(user.uid) == 0:
            pincard_allowed = 'yes' if email_notification_enabled() else 'otp'
        else:
            pincard_allowed = 'no'

    return pincard_allowed, pincard_present

def generate_pincard():

    #Generate a 72 chars string over letters, digits and punctuation
    #Split string in 3 chars groups for 24 total pins
    #and crypt them
    chars_base = string.letters + string.digits + string.punctuation
    pincard_plain = ''.join(random.choice(chars_base) for _ in range(72))
    pincard_plain = [pincard_plain[i:i+3] for i in range(0, len(pincard_plain), 3)]
    pincard_crypted = []
    for pin in pincard_plain:
        pincard_crypted.append(md5(pin).hexdigest())
    
    return pincard_plain, pincard_crypted

def flush_pincard(uid):

    Pincard.objects.filter(user=int(uid)).delete()

def save_pincard(uid):

    #Generate new pincard - plain text for frontend and md5 vals for db
    #Flush current pincard over db
    #Populate db and return plain text pins to user
    pincard_touser, pincard_todb = generate_pincard()
    flush_pincard(uid)

    for index, pin in enumerate(pincard_todb, start=1):
        newpin = Pincard(user=int(uid), pin_number=index, pin_code=pin)
        newpin.save()
    
    return pincard_touser