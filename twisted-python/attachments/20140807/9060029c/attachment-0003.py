from twisted.spread import pb

class UknownWordException(Exception):
    pass

class UnknownDefinition(UknownWordException):
    pass
    # would like to remote define via error

class Dictionary():
    
    def __init__(self, language, word=None, definition=None):
        self.language = language
	self.words = {}
	if not word:
	    word = language
	if not definition:
	    definition = language + ' is a word worthy of a language'
	self.words[word] = set([definition])
	print self.words
    
    def get_language(self):
        return self.language

    def lookup_word(self, word, definition = None):
	print 'lookup_word', self.words
        try:
	    return self.words[word]            
        except:
	    if definition:
	        raise UknownWordException(word)            
	    else:
	        raise UnknownDefinition(word, definition)
    
class CopyDictionary(Dictionary, pb.Copyable):
    
    def getStateToCopy(self):
        print 'state getting copied', self.language
        return self.language, self.words

class DictionaryEditor(pb.Referenceable):
    
    def remote_word_definition(self, lanague, word, definition):
        pass

class RemoteDictionary(pb.RemoteCopy, Dictionary):
    
    def setCopyableState(self, state):
        print 'remote state receives copy', state
        self.language = state[0]
        self.words = state[1]
    
class Library(pb.Root):
    
    dictionaries = []    

    def remote_define(self, language, word, definition):
	dictionary = self.remote_dictionary(language, word, definition)	
	try:
	    definition_set = dictionary.lookup_word(word, definition)
	    print 'got definition_set', definition_set
	    if definition not in definition_set:
		print 'new definition'
		definition_set.add(definition)
	    else:
		print 'existing definition'
	except Exception as e:
	    print e
	    print 'new word'
	    dictionary.words[word] = set([definition])
	return dictionary.words
		

    def remote_dictionary(self, language, word = None, definition = None):
        for d in Library.dictionaries:
            if d.get_language() == language:
                print 'remote'
                return d
        print 'create copyable version'
        dictionary = CopyDictionary(language, word, definition)
        Library.dictionaries.append(dictionary)
        return dictionary
