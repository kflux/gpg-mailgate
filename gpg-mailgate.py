#!/usr/bin/python

#
#	gpg-mailgate
#
#	This file is part of the gpg-mailgate source code.
#
#	gpg-mailgate is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	gpg-mailgate source code is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with gpg-mailgate source code. If not, see <http://www.gnu.org/licenses/>.
#

from ConfigParser import RawConfigParser
from email.mime.base import MIMEBase
import email
import email.message
import re
import GnuPG
import smtplib
import sys
import syslog
import traceback
import email.utils
import os

# imports for S/MIME
from M2Crypto import BIO, Rand, SMIME, X509
from email.mime.message import MIMEMessage

# Read configuration from /etc/gpg-mailgate.conf
_cfg = RawConfigParser()
_cfg.read('/etc/gpg-mailgate.conf')
cfg = dict()
for sect in _cfg.sections():
	cfg[sect] = dict()
	for (name, value) in _cfg.items(sect):
		cfg[sect][name] = value

def log(msg):
	if cfg.has_key('logging') and cfg['logging'].has_key('file'):
		if cfg['logging']['file'] == "syslog":
			syslog.syslog(syslog.LOG_INFO | syslog.LOG_MAIL, msg)
		else:
			logfile = open(cfg['logging']['file'], 'a')
			logfile.write(msg + "\n")
			logfile.close()

verbose=cfg.has_key('logging') and cfg['logging'].has_key('verbose') and cfg['logging']['verbose'] == 'yes'

CERT_PATH = cfg['smime']['cert_path']+"/"

# Read e-mail from stdin
raw = sys.stdin.read()
raw_message = email.message_from_string( raw )
from_addr = raw_message['From']
to_addrs = sys.argv[1:]

def send_msg( message, recipients = None ):
	if recipients == None:
		recipients = to_addrs
	recipients = filter(None, recipients)
	if recipients:
		log("Sending email to: <%s>" % '> <'.join( recipients ))
		relay = (cfg['relay']['host'], int(cfg['relay']['port']))
		smtp = smtplib.SMTP(relay[0], relay[1])
		smtp.sendmail( from_addr, recipients, message )
	else:
		log("No recipient found");

def encrypt_payload( payload, gpg_to_cmdline ):
	raw_payload = payload.get_payload(decode=True)
	if "-----BEGIN PGP MESSAGE-----" in raw_payload and "-----END PGP MESSAGE-----" in raw_payload:
		return payload
	gpg = GnuPG.GPGEncryptor( cfg['gpg']['keyhome'], gpg_to_cmdline, payload.get_content_charset() )
	gpg.update( raw_payload )
	payload.set_payload( gpg.encrypt() )
	isAttachment = payload.get_param( 'attachment', None, 'Content-Disposition' ) is not None
	if isAttachment:
		filename = payload.get_filename()
		if filename:
			pgpFilename = filename + ".pgp"
			if payload.get('Content-Disposition') is not None:
				payload.set_param( 'filename', pgpFilename, 'Content-Disposition' )
			if payload.get('Content-Type') is not None:
				if payload.get_param( 'name' ) is not None:
					payload.set_param( 'name', pgpFilename )
	if payload.get('Content-Transfer-Encoding') is not None:
		payload.replace_header( 'Content-Transfer-Encoding', "7bit" )
	return payload

def encrypt_all_payloads( message, gpg_to_cmdline ):
	encrypted_payloads = list()
	if type( message.get_payload() ) == str:
		return encrypt_payload( message, gpg_to_cmdline ).get_payload()
	for payload in message.get_payload():
		if( type( payload.get_payload() ) == list ):
			encrypted_payloads.extend( encrypt_all_payloads( payload, gpg_to_cmdline ) )
		else:
			encrypted_payloads.append( encrypt_payload( payload, gpg_to_cmdline ) )
	return encrypted_payloads

def get_msg( message ):
	if not message.is_multipart():
		return message.get_payload()
	return '\n\n'.join( [str(m) for m in message.get_payload()] )
	
def get_cert_for_email(to_addr):
	simple_path = os.path.join(CERT_PATH, to_addr)
	if os.path.exists(simple_path): return (simple_path, to_addr)
	# support foo+ignore@bar.com -> foo@bar.com
	multi_email = re.match('^([^\+]+)\+([^@]+)@(.*)$', to_addr)
	if multi_email:
		fixed_up_email = "%s@%s"%(multi_email.group(1), multi_email.group(3))
		log("Multi-email %s converted to %s"%(to_addr, fixed_up_email))
		return get_cert_for_email(fixed_up_email)
	return None
	
def to_smime_handler( raw_message, recipients = None ):
	if recipients == None:
		recipients = to_addrs
	s = SMIME.SMIME()
	sk = X509.X509_Stack()
	normalized_recipient = []
	for addr in recipients:
		addr_addr = email.utils.parseaddr(addr)[1].lower()
		cert_and_email = get_cert_for_email(addr_addr)
		if cert_and_email: 
			(to_cert, normal_email) = cert_and_email
			log("Found cert "+to_cert+" for "+addr+": "+normal_email)
			normalized_recipient.append((email.utils.parseaddr(addr)[0], normal_email))
			x509 = X509.load_cert(to_cert, format=X509.FORMAT_PEM)
			sk.push(x509)
	if len(normalized_recipient):
		s.set_x509_stack(sk)
		s.set_cipher(SMIME.Cipher('aes_192_cbc'))
		p7 = s.encrypt( BIO.MemoryBuffer(raw_message.as_string()) )
		# Output p7 in mail-friendly format.
		out = BIO.MemoryBuffer()
		out.write('From: '+from_addr+'\n')
		to_list = ",".join([email.utils.formataddr(x) for x in normalized_recipient])
		out.write('To: '+to_list+'\n')
		if raw_message['Subject']:
			out.write('Subject: '+raw_message['Subject']+'\n')
		if cfg['default'].has_key('add_header') and cfg['default']['add_header'] == 'yes':
			out.write('X-GPG-Mailgate: Encrypted by GPG Mailgate\n')
		s.write(out, p7)
		log("Sending message from "+from_addr+" to "+str(recipients))
		raw_msg = out.read()
		send_msg(raw_msg, recipients)
	else:
		log("Unable to find valid S/MIME recipient")
		send_msg(raw_message.as_string(), recipients)
	return None


keys = GnuPG.public_keys( cfg['gpg']['keyhome'] )
gpg_to = list()
ungpg_to = list()

for to in to_addrs:
	if to in keys and not ( cfg['default'].has_key('keymap_only') and cfg['default']['keymap_only'] == 'yes'  ):
		gpg_to.append( (to, to) )
	elif cfg.has_key('keymap') and cfg['keymap'].has_key(to):
		gpg_to.append( (to, cfg['keymap'][to]) )
	else:
		if verbose:
			log("Recipient (%s) not in PGP domain list." % to)
		ungpg_to.append(to)

if gpg_to == list():
	if cfg['default'].has_key('add_header') and cfg['default']['add_header'] == 'yes':
		raw_message['X-GPG-Mailgate'] = 'Not encrypted, public key not found'
	if verbose:
		log("No PGP encrypted recipients.")
	to_smime_handler( raw_message )
	exit()

if ungpg_to != list():
	to_smime_handler( raw_message, ungpg_to )

log("Encrypting email to: %s" % ' '.join( map(lambda x: x[0], gpg_to) ))

if cfg['default'].has_key('add_header') and cfg['default']['add_header'] == 'yes':
	raw_message['X-GPG-Mailgate'] = 'Encrypted by GPG Mailgate'

gpg_to_cmdline = list()
gpg_to_smtp = list()
for rcpt in gpg_to:
	gpg_to_smtp.append(rcpt[0])
	gpg_to_cmdline.extend(rcpt[1].split(','))

encrypted_payloads = encrypt_all_payloads( raw_message, gpg_to_cmdline )
raw_message.set_payload( encrypted_payloads )

to_smime_handler( raw_message, gpg_to_smtp )
