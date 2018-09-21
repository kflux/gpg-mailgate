# gpg-mailgate

gpg-mailgate is a content filter for Postfix that automatically encrypts unencrypted incoming email using PGP or S/MIME for select recipients. It is also able to decrypt incoming PGP mails.

For installation instructions, please refer to the included INSTALL file.

# Features
- Correctly displays attachments and general email content; currently will only display first part of multipart messages
- Public keys are stored in a dedicated gpg-home-directory
- Encrypts both matching incoming and outgoing mail (this means gpg-mailgate can be used to encrypt outgoing mail for software that doesn't support PGP or S/MIME)
- Decrypts PGP encrypted mails for present private keys (but no signature check and it does not always work with PGP/INLINE encrypted mails)
- Easy installation
- gpg-mailgate-web extension is a web interface allowing any user to upload PGP keys so that emails sent to them from your mail server will be encrypted (see gpg-mailgate-web directory for details)
- people can submit their public key like to any keyserver to gpg-mailgate with the gpg-mailgate-web extension
- people can send an S/MIME signed email to register@yourdomain.tld to register their public key
- people can send their public OpenPGP key as attachment or inline to register@yourdomain.tld to register it

This is forked from the original project at http://code.google.com/p/gpg-mailgate/

# Authors

This is a combined work of many developers and contributors:

* mcmaster <mcmaster@aphrodite.hurricanelabs.rsoc>
* Igor Rzegocki <ajgon@irgon.com> - [GitHub](https://github.com/ajgon/gpg-mailgate)
* Favyen Bastani <fbastani@perennate.com> - [GitHub](https://github.com/uakfdotb/gpg-mailgate)
* Colin Moller <colin@unixarmy.com> - [GitHub](https://github.com/LeftyBC/gpg-mailgate)
* Taylor Hornby <havoc@defuse.ca> - [GitHub](https://github.com/defuse/gpg-mailgate)
* Martin (uragit) <uragit@telemage.com> - [GitHub](https://github.com/uragit/gpg-mailgate)
* Braden Thomas - [BitBucket](https://bitbucket.org/drspringfield/emailencrypt.net/)
* Bruce Markey - [GitHub](https://github.com/TheEd1tor)
* Remko Tronçon - [GitHub](https://github.com/remko/phkp/)
* Kiritan Flux [GitHub](https://github.com/kflux)
* Fabian Krone [GitHub] (https://github.com/fkrone/gpg-mailgate)

# To Do

* rename from gpg-mailgate to openpgp-s-mime-mailgate or something.....
* find a better solution for an own user instead of the user `nobody`
* make PGP/INLINE decryption more reliable