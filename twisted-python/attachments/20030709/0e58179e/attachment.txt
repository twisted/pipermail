    def _strip_paren(self, s):
        """Remove leading and trailing parentheses."""
        if s[0] == '(':
            if s[-1] != ')':
                raise MismatchedNesting(s)
            s = s[1:-1]
        return s

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

    def _build_body_query(self, d):
        body_query = "%s(" % (d["body"],)
        for item, value in d.items():
            if item == "peek" and value is not None:
                body_query += "%s=1, " % (value,)
            elif item == "section" and value is not None:
                body_query += '%s="%s", ' % (item, value,)
            elif item == "partial" and value is not None:
                min, max = value.split('.', 1)
                body_query += "%s=(%s,%s), " % (item, min, max)
            elif item == "part" and value is not None:
                if '.' in value:
                    value, extra = value.split('.', 1)
                    if '.' in extra:
                        extra, extra2 = extra.split('.', 1)
                        body_query += "%s=1, %s=1, %s=1, " % (value, extra,
                                                              extra2)
                    else:
                        body_query += "%s=1, %s=1, " % (value, extra)
                else:
                    body_query += "%s=1, " % (value,)
            elif item == "fielditems" and value is not None:
                body_query += "%s=%s, " % (item, splitQuoted(value),)
        body_query = "%s)" % (body_query[:-2],)
        return body_query

    macro_fetch_atts = {"ALL" : ["FLAGS()", "INTERNALDATE()",
                                 "RFC822(SIZE=1)", "ENVELOPE()"],
                        "FAST" : ["FLAGS()", "INTERNALDATE()",
                                  "RFC822(SIZE=1)"],
                        "FULL" : ["FLAGS()", "INTERNALDATE()",
                                  "RFC822(SIZE=1)", "ENVELOPE()", "BODY()"]}
    simple_fetch_atts = ["ENVELOPE", "FLAGS", "INTERNALDATE", "UID"]
    body_re = re.compile(r"(?P<body>BODY)(?:.(?P<peek>PEEK))?\[(?:(?P<sect" \
                         r"ion>[1-9]\d*[\d*\.]*)\.)?(?P<part>HEADER|TEXT|H" \
                         r"EADER.FIELDS|HEADER.FIELDS.NOT|MIME)(?: \((?P<f" \
                         r"ielditems>[^\(\)]*)\))?\](?:\<(?P<partial>\d+\." \
                         r"[1-9]\d*)\>)?", re.IGNORECASE)

    def arg_fetchatt(self, line):
        """
        fetch-att
        """
        line = self._strip_paren(line.lstrip().rstrip())
        if self.macro_fetch_atts.has_key(line.upper()):
            query = self.macro_fetch_atts[line.upper()]
        else:
            query = []
            line = self._strip_paren(line)
            for word in self._fetch_split(line):
                uword = word.upper()
                if uword in self.simple_fetch_atts:
                    query.append("%s()" % (word,))
                elif uword.startswith("RFC822"):
                    if uword == "RFC822":
                        query.append("%s()" % (word,))
                    else:
                        query.append("%s(%s=1)" % (word[:6], word[7:]))
                elif uword.startswith("BODY"):
                    if uword[4:] == "STRUCTURE":
                        query.append("%s(%s=1)" % (word[:4], word[4:]))
                        continue
                    elif uword[4:] == "":
                        query.append("%s()" % (word,))
                        continue
                    mo = self.body_re.match(word)
                    if mo is None:
                        raise IllegalIdentifierError()
                    
                    # A few checks that are beyond the regex
                    if mo.group("part").upper() == "MIME" and \
                       mo.group("section") == "":
                        raise IllegalIdentifierError()
                    no_fields = (mo.group("fielditems") is None)
                    fields_needed = (mo.group("part").upper() in \
                                     ["HEADER.FIELDS", "HEADER.FIELDS.NOT"])
                    if (no_fields and fields_needed) or \
                       (not no_fields and not fields_needed):
                        raise IllegalIdentifierError()

                    query.append(self._build_body_query(mo.groupdict()))
                else:
                    raise IllegalIdentifierError()
        return query
