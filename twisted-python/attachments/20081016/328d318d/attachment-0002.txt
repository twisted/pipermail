from twisted.internet import defer
from twisted.python import failure, log

def succeed(result):
    d = TDeferred()
    d.callback(result)
    return d

def fail(result=defer._nothing):
    if result is defer._nothing:
        result = failure.Failure()
    d = TDeferred()
    d.errback(result)
    return d

def _historyPop(result):
    return result

def _continue(result, d):
    d.result = result
    d.unpause()

class TDeferred(defer.Deferred):
    def __init__(self):
        defer.Deferred.__init__(self)
        self.history = []

    def _startRunCallbacks(self, result):
        self.initialResult = result
        defer.Deferred._startRunCallbacks(self, result)

    def _runCallbacks(self):
        if not self.paused:
            cb = self.cb = self.callbacks
            self.callbacks = []
            while cb:
                item = cb.pop(0)
                isFailure = isinstance(self.result, failure.Failure)
                callback, args, kw = item[isFailure]
                args = args or ()
                kw = kw or {}
                try:
                    self.result = callback(self.result, *args, **kw)
                    if isinstance(self.result, TDeferred):
                        self.callbacks = cb

                        # note: this will cause _runCallbacks to be called
                        # "recursively" sometimes... this shouldn't cause any
                        # problems, since all the state has been set back to
                        # the way it's supposed to be, but it is useful to know
                        # in case something goes wrong.  deferreds really ought
                        # not to return themselves from their callbacks.
                        self.pause()
                        self.result.addBoth(_historyPop)
                        self.result.addBoth(_continue, self)
                        break
                except:
                    self.result = failure.Failure()
                finally:
                    self.history.append(list(item) + [isFailure, self.result])

        if isinstance(self.result, failure.Failure):
            self.result.cleanFailure()
            if self._debugInfo is None:
                self._debugInfo = defer.DebugInfo()
            self._debugInfo.failResult = self.result
        else:
            if self._debugInfo is not None:
                self._debugInfo.failResult = None

def _addHistoryItem(isCallback, f, args, kwargs, indent):
    out = [indent + ('CALLBACK:' if isCallback else 'ERRBACK:')]
    if f is defer.passthru:
        out.append('%s  func   <pass>' % indent)
    elif f is logDeferredHistory:
        out.append('%s  func   <history>' % indent)
    else:
        out.extend([
            '%s  func   = %r' % (indent, f),
            '%s  args   = %r' % (indent, str(args)),
            '%s  kwargs = %r' % (indent, str(kwargs)),
            ])
    return out

def logDeferredHistory(result, d, indent=''):
    out = ['', '%sHistory for deferred %r' % (indent, d)]
    append, extend = out.append, out.extend
    if hasattr(d, 'initialResult'):
        append('%sInitial result = %r' % (indent, d.initialResult))
    if d.history:
        append('%s--- ALREADY FIRED ---' % indent)
        for item in d.history:
            (cb, cba, cbk), (eb, eba, ebk), wasFailure, fResult = item
            if cb is _historyPop:
                return out
            out += _addHistoryItem(True, cb, cba, cbk, indent)
            if not wasFailure:
                append('%s  result = %r' % (indent, fResult))
            if (eb, eba, ebk) == (cb, cba, cbk):
                append('%sERRBACK: <same as CALLBACK>' % indent)
            else:
                out += _addHistoryItem(False, eb, eba, ebk, indent)
            if wasFailure:
                append('%s  result = %r' % (indent, fResult))
            if isinstance(fResult, TDeferred):
                out += logDeferredHistory(None, fResult, indent + '\t')
    if d.cb:
        needHeader = True
        for item in d.cb:
            (cb, cba, cbk), (eb, eba, ebk) = item
            if cb is _continue or cb is _historyPop:
                continue
            if needHeader:
                append('%s--- STILL TO BE FIRED ---' % indent)
                needHeader = False
            out += _addHistoryItem(True, cb, cba, cbk, indent)
            if (eb, eba, ebk) == (cb, cba, cbk):
                append('%sERRBACK: <same as CALLBACK>' % indent)
            else:
                out += _addHistoryItem(False, eb, eba, ebk, indent)
    log.msg('\n'.join(out))
    return result
