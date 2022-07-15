#
#
#

import email.Parser
import email.Utils
from email.Generator import Generator
from cStringIO import StringIO

class MsgRequest:
    ...
    
    def parseAddr(self, addr):
        "Turn address header value into IMAP list"
        if addr is None:
            return [(None, None, None),]
        addrs = email.Utils.getaddresses([addr])
        return [[fn or None, None] + addr.split('@') for fn, addr in addrs]

    def mkEnvelope(self, msg, toi=None):
        "Return an IMAP envelope tuple"
        _from = msg.get('from') or msg.get('sender')
        _sender = self.parseAddr(msg.get('sender') or _from)
        _replyto = self.parseAddr(msg.get('reply-to') or _from)
        _from = self.parseAddr(_from)
        _cc = msg.get('cc')
        _cc = _cc and self.parseAddr(_cc)
        _bcc = msg.get('bcc')
        _bcc = _bcc and self.parseAddr(_bcc)
        _date = msg.get('date')
        _subj = msg.get('subject')
        _refs = msg.get('in-reply-to')
        _msgid = msg.get('message-id')
        return (_date, _subj, _from, _sender, _replyto, _cc, _bcc, _refs,
                _msgid)

    def getParams(self, msg, header='content-type', default=None):
        """Get parameters from MIME-header, i.e. for
         Content-Type: text/plain; charset=us-ascii; foo=bar; baz
        return
         [ ('charset', 'us-ascii'), ('foo', 'bar'), ('baz' None)]
        """
        params = []
        val = msg.get(header)
        if val is None:
            return default

        for param in val.split(';')[1:]:
            try:
                name, val = param.split('=',1)
                name = name.strip()
                val = val.strip()
            except ValueError:
                # Bare attribute
                name = param.strip()
                val = None
            params.append((name, val))
        return params

    def getBody(self, msg, ext=0):
        "Generate IMAP BODY[STRUCTURE] response"
        res = []

        if msg.get_content_maintype() == 'multipart':
            for part in msg.get_payload():
                res.append(self.getBody(part, ext))
            res.append(msg.get_content_subtype())
            if ext:
                extdata = []
                for hdr in ['content-type', 'content-disposition']:
                    extdata.append(self.getParams(msg.hdr))
                
                extdata.extend([msg.get('content-language'),
                                msg.get('content-location')])
                res.extend(extdata)
        else:
            body = flattenBody(msg)

            res.extend([msg.get_content_maintype(), msg.get_content_subtype()])
            res.extend([self.getParams(msg), msg.get('content-id'),
                        msg.get('content-description'),
                        msg.get('content-transfer-encoding'),
                        str(len(body))])
            
            if msg.get_content_type() == 'message/rfc822':
                # A message/rfc822 has exactly 1 subpart
                part = msg.get_payload(0)
                res.extend([self.mkEnvelope(part),
                            self.getBody(part, ext),
                            str(len(body.splitlines()))])
            elif msg.get_content_maintype() == 'text':
                res.append(str(len(body.splitlines())))
            if ext:
                extdata = [msg.get('content-md5')]
                extdata.extend([self.getParams(msg,
                                               header='content-disposition'),
                                msg.get('content-language'),
                                msg.get('content-location')])
                res.extend(extdata)
                
        return res

class BodyGenerator(Generator):
    "A class that returns the body of a message object"
    def _write(self, msg):
        "Just write the contents, skip writing the headers"
        self._dispatch(msg)

    def clone(self, fp):
        """Return a normal generator, so we get headers inside"""
        return Generator(fp, self._mangle_from_, self._Generator__maxheaderlen)

def flattenBody(msg):
    b = StringIO()
    g = BodyGenerator(b)
    g.flatten(msg)
    return b.getvalue()
