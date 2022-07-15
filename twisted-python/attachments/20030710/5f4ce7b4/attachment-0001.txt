    def _fetch_split(self, s):
        """Like split, but do not split within [].

        splitQuoted could be used instead, if it was changed to accept
        the 'quote' character.
        """
        in_bracket = b = 0
        for e in range(0, len(s)):
            if s[e] == ' ' and in_bracket == 0:
                yield s[b:e]
                b = e+1
            elif s[e] == '[':
                in_bracket += 1
            elif s[e] == ']':
                in_bracket -= 1
        if s[b:] != '':
            yield s[b:]

    class Flags(object):
        name = "flags"
        def __str__(self):
            return "FLAGS"

    class Internaldate(object):
        name = "internaldate"
        def __str__(self):
            return "INTERNALDATE"

    class Envelope(object):
        name = "envelope"
        def __str__(self):
            return "ENVELOPE"

    class UID(object):
        name = "uid"
        def __str__(self):
            return "UID"

    class RFC822(object):
        name = "rfc822"
        def __init__(self, header=False, size=False, text=False):
            self.header, self.size, self.text = header, size, text
            
        def __str__(self):
            if self.header:
                return "RFC822.HEADER"
            elif self.size:
                return "RFC822.SIZE"
            elif self.text:
                return "RFC822.TEXT"
            else:
                return "RFC822"

    class Body(object):
        name = 'body'
        def __init__(self, peek=False, header=False, fields=False,
                     fields_not=False, text=False, mime=False,
                     structure=False, only=False, fielditems=None,
                     section=None, partial=None):
            self.peek = peek
            self.header = header
            self.fields = fields
            self.fields_not = fields_not
            self.text = text
            self.mime = mime
            self.fielditems = fielditems
            self.section = section
            self.partial = partial
            self.structure = structure
            self.only = only

        def __str__(self):
            if self.only:
                return "BODY"
            elif self.structure:
                return "BODYSTRUCTURE"
            base = "BODY"
            if self.peek:
                base = "BODY.PEEK"
            if self.section:
                section = '.'.join(self.section)
            else:
                section = ""
            if self.partial:
                partial = "<%s.%s>" % partial
            else:
                partial = ""
            opt = ''
            if self.header:
                if self.fields_not:
                    opt = "HEADER.FIELDS.NOT %s" % \
                          (collapseNestedLists(self.fielditems),)
                elif self.fields:
                    opt = "HEADER.FIELDS %s" % \
                          (collapseNestedLists(self.fielditems),)
                else:
                    opt = "HEADER"
            elif self.text:
                opt = "TEXT" % (body, )
            elif self.mime:
                opt = "MIME" % (mime, )
            return "%s[%s%s]%s" % (base, section, opt, partial)

    fetch_atts = {"ALL" : [Flags(), Internaldate(), RFC822(size=True),
                           Envelope()],
                  "FAST" : [Flags(), Internaldate(), RFC822(size=True)],
                  "FULL" : [Flags(), Internaldate(), RFC822(size=True),
                            Envelope(), Body()],
                  "ENVELOPE" : [Envelope()],
                  "FLAGS" : [Flags()],
                  "INTERNALDATE" : [Internaldate()],
                  "UID" : [UID()],
                  "RFC822" : [RFC822()],
                  "RFC822.HEADER" : [RFC822(header=True)],
                  "RFC822.SIZE" : [RFC822(size=True)],
                  "RFC822.TEXT" : [RFC822(text=True)],
                  "BODY" : [Body(only=True)],
                  "BODYSTRUCTURE" : [Body(structure=True)],
                  }
    body_re = re.compile(r"""
    BODY                           # the initial BODY
    \.? (?P<peek> PEEK)?           # capture the PEEK (but not '.') into
                                   # group 'peek'
    \[ (?: (?P<section>            # the '[' and a non-capture group for
                                   # the final '.', and call the next group
                                   # 'section'
    [\d\.]*) \.)?                  # the 'section' group must be a sequence
                                   # of numbers, separated by '.'s
                                   # (this will capture invalid section
                                   # specifiers - it is up to the user to
                                   # verify that they are valid)
    (?P<part>                      # a group named 'part' for the part of
                                   # the message we are after
    HEADER | TEXT | MIME |         # the part must be any one of these
    HEADER.FIELDS | HEADER.FIELDS.NOT)
    (?: [ ] \(                     # don't capture the space and '('
    (?P<fielditems>                # an optional group named 'fielditems'
    [^\(\)] *) \) )?               # holding anything except '(' or ')'
    \]                             # the ']'
    (?: \<                         # a non-capture group for the optional
                                   # partial specifier and the opening '<'
    (?P<partial> \d+ \. [1-9] \d*) # the partial group which must be any
                                   # number, a '.', and then any non-zero
                                   # number
    \>)?                           # closing '>'
    """, re.VERBOSE)

    def arg_fetchatt(self, line):
        """
        fetch-att
        """
        query = []
        for item in self._fetch_split(line[1:-1]):
            if self.fetch_atts.has_key(item):
                query.extend(self.fetch_atts[item])
            else:
                mo = self.body_re.match(item)
                if mo is None:
                    raise IllegalIdentifierError()
                
                # A few checks that are beyond the regex
                if mo.group("part") == "MIME" and \
                   mo.group("section") == "":
                    raise IllegalIdentifierError()
                no_fields = (mo.group("fielditems") is None)
                fields_needed = (mo.group("part") in \
                                 ["HEADER.FIELDS", "HEADER.FIELDS.NOT"])
                if (no_fields and fields_needed) or \
                   (not no_fields and not fields_needed):
                    raise IllegalIdentifierError()
                # The mime section must start with a non-zero number,
                # and must not contain '..'.
                if mo.group("section") and \
                   (mo.group("section")[0] == '.' or \
                    mo.group("section")[0] == '0' or \
                    mo.group("section").find("..") == -1):
                        raise IllegalIdentifierError()

                args = mo.groupdict()
                if args["partial"]:
                    partial = args["partial"].split('.', 1)
                else:
                    partial = None
                if args["section"]:
                    section = args["section"].split('.')
                else:
                    section = None
                if args["fielditems"]:
                    fielditems = splitQuoted(args["fielditems"])
                else:
                    fielditems = None
                b = self.Body(peek=(args["peek"]=="PEEK"),
                              header=(args["part"].startswith("HEADER")),
                              fields=(args["part"][7:13] == "FIELDS"),
                              fields_not=(args["part"][14:17] == "NOT"),
                              text=(args["part"] == "TEXT"),
                              mime=(args["part"] == "MIME"),
                              fielditems=fielditems,
                              section=section,
                              partial=partial,
                         )
                query.append(b)
        return (query, '')

    def __cbFetch(self, results, tag, mbox, uid):
        for (mId, parts) in results.iteritems():
            if uid:
                if not parts.has_key(self.UID()):
                    parts['UID'] = str(mId)
            P = []
            for p, r in parts.iteritems():
                P.append("%s %s" % (str(p), collapseNestedLists([r])))
            self.sendUntaggedResponse(
                '%d FETCH (%s)' % (mId, ' '.join(P))
            )
        self.sendPositiveResponse(tag, 'FETCH completed')
