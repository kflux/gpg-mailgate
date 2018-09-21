# Installation instructions
## Content
- General information
- Install GPG-Mailgate
- Install GPG-Mailgate-Web
- Install Register-handler

## General information
GPG-Mailgate is divided in 3 main parts: GPG-Mailgate itself, GPG-Mailgate-Web and Register-handler. Some parts of the GPG-Mailgate project depend on other parts of the project. You will find information about these dependencies at the beginning of every installation part.

These instructions show you how to set up GPG-Mailgate in an easy way. If you are a more advanced user, feel free to experiment with the settings. For these instructions a home directory for the user `nobody` is set. Sadly this is an odd workaround but no better solution was found.

These instructions are based on an installation on an Ubuntu 14.04 LTS virtual machine. For other Linux distributions and other versions these instructions might need to be adapted to your distribution (e.g. installation of packages and used directories).

## Install GPG-Mailgate
### Requirements
- Python 2.X is already installed (GPG-Mailgate is not Python 3 compatible)
- Postfix is already installed and configured. It is recommended that you have already tested your configuration so we can exclude this as a main cause of problems
- GnuPG is already installed and configured

### Installation

1. Install the Python-M2Crypto module:

        apt-get install python-m2crypto
        
2. Set the home directory for the user `nobody` (sadly this workaround is needed as there is no better solution at this point). If you get an error that the user is currently used by a process, you might need to kill the process manually.

        usermod -d /var/gpgmailgate nobody
        
3. Create dedicated directories for storing PGP keys and S/MIME certificates and make the user `nobody` owner of these:
        
        mkdir -p /var/gpgmailgate/.gnupg
        mkdir -p /var/gpgmailgate/smime
        chown -R nobody:nogroup /var/gpgmailgate/

4. Place the `gpg-mailgate.py` in `/usr/local/bin/`, make the user `nobody` owner of the file and make it executable:

        chown nobody:nogroup /usr/local/bin/gpg-mailgate.py
        chmod u+x /usr/local/bin/gpg-mailgate.py

5. Place the `GnuPG` directory in `/usr/local/lib/python2.7/dist-packages` (replace 2.7 with your Python 2 version)

6. Configure `/etc/gpg-mailgate.conf` based on the provided `gpg-mailgate.conf.sample`. Change the settings according to your configuration. If you follow this guide and have a standard configuration for postfix, you don't need to change much. 

7. Add the following to the end of `/etc/postfix/master.cf`

        gpg-mailgate    unix    -   n   n   -   -   pipe
            flags= user=nobody argv=/usr/local/bin/gpg-mailgate.py ${recipient}

        127.0.0.1:10028 inet    n   -   n   -   10  smtpd
            -o content_filter=
            -o receive_override_options=no_unknown_recipient_checks,no_header_body_checks
            -o smtpd_helo_restrictions=
            -o smtpd_client_restrictions=
            -o smtpd_sender_restrictions=
            -o smtpd_recipient_restrictions=permit_mynetworks,reject
            -o mynetworks=127.0.0.0/8
            -o smtpd_authorized_xforward_hosts=127.0.0.0/8

    If you use Postfix versions from 2.5 onwards, it is recommended to change `${recipient}` to `${original_recipient}` in line two of the lines above.

8. Add the following line to `/etc/postfix/main.cf`

        content_filter = gpg-mailgate
  
9. Restart Postfix

You are now ready to go. To add a public key for encryption just use the following command:
        
        sudo -u nobody /usr/bin/gpg --homedir=/var/gpgmailgate/.gnupg --import /some/public.key

- Replace `/some/public.key` with the location of a public key
- `/some/public.key` can be deleted after importation
- Confirm that it's working:  
`sudo -u nobody /usr/bin/gpg --list-keys --homedir=/var/gpgmailgate/.gnupg`

Please also test your installation before using it.

GPG-Mailgate is also able to handle S/MIME certificates for encrypting mails. However, it is best to use it in combination with Register-Handler described later to add new certificates. If you try to add them manually it might fail. The certificates are stored in `/var/gpgmailgate/smime` in PKCS7 format and are named like `User@example.com` (the user part is case sensitive, the domain part should be in lower case).

####Additional settings
Most mail servers do not handle mail addresses case sensitive. If you know that all your recipient mail servers do not care about case sensitivity then you can set `mail_case_insensitive` in the settings to `yes` so looking up PGP keys or S/MIME certificates does also happen case insensitive.
If your recipients have problems to decrypt mails encrypted by GPG-Mailgate they might use a piece of software that does not support PGP/MIME encrypted mails. You can tell GPG-Mailgate to use the legacy PGP/INLINE format by adding the recipient to the `pgp_style` map in the following format:  
`User@example.com=inline`


### Mail decryption
GPG-Mailgate does not only feature encryption of mails but also decryption of PGP encrypted mails.
#### Important notice
**Read carefully before setting up and using this functionality!**

With this functionality you could use GPG-Mailgate to decrypt incoming PGP encrypted mails (it is also capable of decrypting outgoing mails if the necessary key is present). To use this, you need to store your private keys on the server. This means that anyone who is able to obtain admin rights on the server is able to get the private keys stored on the server and is able to decrypt any mail encrypted with the corresponding public key. **If the server gets compromised in any kind and the attacker may have gained access to the server's file system, the keys have to be regarded as compromised as well!** If this happens you have to revoke your keys, notify everyone who has your public key (key servers as well) not to use this key any longer. You also need to create a new key pair for encrypted communication.

#### Limitations
There are two main types of PGP encryption: PGP/MIME and PGP/INLINE. PGP/MIME is standardized while PGP/INLINE isn't completely clear standardized (even though some people claim so). Decrypting PGP/MIME encrypted mails works in most cases while decrypting PGP/INLINE encrypted mails may fail more often. The reason is that most clients are implementing PGP/INLINE in their own way. GPG-Mailgate is able to decrypt mails which are encrypted PGP/INLINE by GPG-Mailgate on the sender's side. Furthermore it should be able to decrypt PGP/INLINE encrypted mails encrypted by Enigmail. For PGP/INLINE the mail's structure may not be preserved due to how PGP/INLINE is implemented on most clients. If you receive a PGP/INLINE encrypted mail that could not be decrypted by GPG-Mailgate you may ask the sender to use PGP/MIME instead. Furthermore file types might get lost when using PGP/INLINE. Due to this limitations decrypting PGP/INLINE encrypted mails is disabled by default. If you want to take the risk you can set `no_inline_dec` to `no` in the `[default]` section. You have been warned.

#### Setting up decryption
You need the recipient's private key for whom you want to decrypt mails. Only unprotected keys are supported. Keys protected by a passphrase could not be used. To add the private key, use the following command:  
`sudo -u nobody /usr/bin/gpg --homedir=/var/gpgmailgate/.gnupg --import /some/private.key`
From now on PGP encrypted mails will be decrypted for the recipients for whom the keys are imported.

You also can remove a private key by using the following command. Replace `user@example.com` with the user's address for whom you want to remove the key:  
`sudo -u nobody /usr/bin/gpg --homedir=/var/gpgmailgate/.gnupg --delete-secret-keys user@example.com`

## Install GPG-Mailgate-Web
### Requirements
- A webserver is installed and reachable
- The webserver is able to handle PHP scripts
- MySQL is installed
- Python 2.X is already installed

### Installation
All files you need can be found in the [gpg-mailgate-web] (gpg-mailgate-web/) directory.

1. Install the Python-mysqldb and Python-markdown modules:

        apt-get install python-mysqldb python-markdown

2. Create a new database for GPG-Mailgate-Web.

3. Import the schema file `schema.sql` into the newly created database.

4. Edit the config file located at `/etc/gpg-mailgate.conf`. Set `enabled = yes` in `[database]` and fill in the necessary settings for the database connection.

5. Copy the files located in the [public_html] (gpg-mailgate-web/public_html) directory onto your webserver. They can also be placed in a subdirectory on your webserver.

6. On your webserver move the `config.sample.php` file to `config.php` and edit the configuration file.

7. Create directories for storing email templates:
        
        mkdir -p /var/gpgmailgate/cron_templates
        
8. Copy the templates found in the [cron_templates] (cron_templates/) directory into the newly created directory and transfer ownership:

        chown -R nobody:nogroup /var/gpgmailgate/cron_templates

9. Copy `cron.py` to `/usr/local/bin/gpgmw-cron.py`. Make it executable and and transfer ownership to `nobody`:

        chown nobody:nogroup /usr/local/bin/gpgmw-cron.py
        chmod u+x /usr/local/bin/gpgmw-cron.py

10. Create `/etc/cron.d/gpgmw` with contents:  
`*/3 * * * * nobody /usr/bin/python /usr/local/bin/gpgmw-cron.py > /dev/null`  
 for executing the cron job automatically.

11. Test your installation.

### GPG-Mailgate-Web as keyserver
GPG-Mailgate-Web can also be used as a keyserver. For more information have a look at GPG-Mailgate-Web's [readme] (gpg-mailgate-web/README).

## Install Register-handler
### Requirements
- Already set up and working GPG-Mailgate-Web. It should be reachable from the machine that will run register-handler
- Postfix is already installed and configured. It is recommended that you have already tested your configuration so we can exclude this as a main cause of problems. Your Postfix configuration should also support aliases

### Installation

1. Install the Python-requests module:

        apt-get install python-requests
        
2. Create directories for storing email templates:
        
        mkdir -p /var/gpgmailgate/register_templates
        
3. Copy the templates found in the [register_templates] (register_templates/) directory into the newly created directory and transfer ownership:

        chown -R nobody:nogroup /var/gpgmailgate/register_templates
        
4. Copy `register-handler.py` to `/usr/local/bin/register-handler.py`. Make it executable and own it to `nobody`:

        chown nobody:nogroup /usr/local/bin/register-handler.py
        chmod a+x /usr/local/bin/register-handler.py
        
5. Edit the config file located at `/etc/gpg-mailgate.conf`. Set the parameter `webpanel_url` in `[mailregister]` to the url of your GPG-Mailgate-Web panel (the URL should be the same as the one you use to access the panel with your web browser). Also set the parameter `register_email` to the email address you want the user to see when receiving mails from the register-handler (it does not have to be an existing address but it is recommended). Register-handler will send users mails when they are registering S/MIME certificates or when neither a S/MIME certificate nor a PGP key was found in a mail sent to the register-handler.

6. Add `register:   |/usr/local/bin/register-handler.py` to `/etc/aliases`

7. Update postfix's alias database with `postalias /etc/aliases`

8. Restart postfix.

9. Test your installation.
