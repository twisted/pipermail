from twisted.trial import unittest
from twisted.xish import domish, xpath


class _:

    def __init__(self, _name, **kwargs):
        self._domish = domish.Element((None, _name),attribs=kwargs)

    def __getitem__(self, elements):
        for element in elements:
            self._domish.addChild(element._domish)
        return self

    def __str__(self):
        return str(self._domish)

    def toDomish(self):
        return self._domish


class Example1(unittest.TestCase):

    def setUp(self):
        self.doc = _('AAA')[
            _('BBB'),
            _('CCC'),
            _('BBB'),
            _('BBB'),
            _('DDD')[
                _('BBB'),
                ],
            _('CCC'),
            ].toDomish()

    def test_1(self):
        result = xpath.queryForNodes('/AAA', self.doc)
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0].name, 'AAA')

    def test_2(self):
        result = xpath.queryForNodes('/AAA/CCC', self.doc)
        self.assertEquals(len(result), 2)
        for e in result:
            self.assertEquals(e.name, 'CCC')
            self.assertEquals(e.parent.name, 'AAA')

    def test_3(self):
        result = xpath.queryForNodes('/AAA/DDD/BBB', self.doc)
        self.assertEquals(len(result), 1)
        e = result[0]
        self.assertEquals(e.name, 'BBB')
        self.assertEquals(e.parent.name, 'DDD')
        self.assertEquals(e.parent.parent.name, 'AAA')


class Example2(unittest.TestCase):

    def setUp(self):
        self.doc = _('AAA')[
            _('BBB'),
            _('CCC'),
            _('BBB'),
            _('DDD')[
                _('BBB'),
                ],
            _('CCC')[
                _('DDD')[
                    _('BBB'),
                    _('BBB'),
                    ],
                ],
            ].toDomish()

    def test_1(self):
        result = xpath.queryForNodes('//BBB', self.doc)
        self.assertEquals(len(result), 5)
        for e in result:
            self.assertEquals(e.name, 'BBB')

    def test_2(self):
        result = xpath.queryForNodes('//DDD/BBB', self.doc)
        self.assertEquals(len(result), 3)
        for e in result:
            self.assertEquals(e.name, 'BBB')
            self.assertEquals(e.parent.name, 'DDD')

    test_1.todo = test_2.todo = 'Implement //'


class Example3(unittest.TestCase):

    def setUp(self):
        self.doc = _('AAA')[
            _('XXX')[
                _('DDD')[
                    _('BBB'),
                    _('BBB'),
                    _('EEE'),
                    _('FFF'),
                    ],
                ],
            _('CCC')[
                _('DDD')[
                    _('BBB'),
                    _('BBB'),
                    _('EEE'),
                    _('FFF'),
                    ],
                ],
            _('CCC')[
                _('BBB')[
                    _('BBB')[
                        _('BBB'),
                        ],
                    ],
                ],
            ].toDomish()

    def test_1(self):
        result = xpath.queryForNodes('/AAA/CCC/DDD/*', self.doc)
        self.assertEquals(len(result), 4)

    def test_2(self):
        result = xpath.queryForNodes('/*/*/*/BBB', self.doc)
        self.assertEquals(len(result), 5)
        for e in result:
            self.assertEquals(e.name, 'BBB')
            self.assertEquals(e.parent.parent.parent.name, 'AAA')
            self.assertEquals(e.parent.parent.parent.parent, None)

    def test_3(self):
        result = xpath.queryForNodes('//*', self.doc)
        self.assertEquals(len(result), 17)

    test_3.todo = 'Probably ok once // is implemented'
        

class Example4(unittest.TestCase):

    def setUp(self):
        self.doc = _('AAA')[
            _('BBB'),
            _('BBB'),
            _('BBB'),
            _('BBB'),
            ].toDomish()

    def test_1(self):
        e = xpath.queryForNodes('/AAA/BBB[1]', self.doc)
        self.assertEquals(e.name, 'BBB')
        self.assertIdentical(e, e.parent.children[0])

    def test_2(self):
        e = xpath.queryForNodes('/AAA/BBB[last()]', self.doc)
        self.assertEquals(e.name, 'BBB')
        self.assertIdentical(e, e.parent.children[-1])

    test_1.todo = test_2.todo = 'Implement index lookups'


class Example5(unittest.TestCase):

    def setUp(self):
        self.doc = _('AAA')[
            _('BBB', id='b1'),
            _('BBB', id='b2'),
            _('BBB', name='bbb'),
            _('BBB'),
            ].toDomish()

    def test_1(self):
        result = xpath.queryForNodes('//@id', self.doc)
        self.assertEquals(len(result), 2)
        for e in result:
            self.assertEquals(e.name, 'BBB')
            self.assertIn(e.attribtues['id'], ['b1', 'b2'])

    def test_2(self):
        result = xpath.queryForNodes('//BBB[@id]', self.doc)
        self.assertEquals(len(result), 2)
        for e in result:
            self.assertEquals(e.name, 'BBB')
            self.assertIn(e.attribtues['id'], ['b1', 'b2'])

    def test_3(self):
        result = xpath.queryForNodes('//BBB[@name]', self.doc)
        self.assertEquals(len(result), 1)
        for e in result:
            self.assertEquals(e.name, 'BBB')
            self.assertEquals(e.attribtues['name'], 'bbb')

    def test_4(self):
        result = xpath.queryForNodes('//BBB[@*]', self.doc)
        self.assertEquals(len(result), 3)

    def test_5(self):
        result = xpath.queryForNodes('//BBB[not(@*)]', self.doc)
        self.assertEquals(len(result), 1)
        self.assertEquals(len(result[0].attributes), 0)

    def test_6(self):
        result = xpath.queryForNodes('/AAA/BBB[@id]', self.doc)
        self.assertEquals(len(result), 2)

    def test_7(self):
        result = xpath.queryForNodes('/AAA/*[@id]', self.doc)
        self.assertEquals(len(result), 2)

    def test_8(self):
        result = xpath.queryForNodes('/AAA/@id', self.doc)
        self.assertEquals(len(result), 2)

    def test_9(self):
        result = xpath.queryForNodes('/*/BBB[@id]', self.doc)
        self.assertEquals(len(result), 2)

    test_2.todo = test_3.todo = test_4.todo = test_5.todo = \
                  'missing // support again?'
    test_1.todo = test_8.todo = 'support attr without element matching'
