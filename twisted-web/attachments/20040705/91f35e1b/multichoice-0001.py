from nevow import compy, tags
from formless import annotate, iformless, webform

class MultipleChoice(annotate.Typed):
    """
    Allow the user to pick from a list of 'choices', or a list of
    choices found by accessing the list in the attribute
    'choicesAttribute' of the object we are configuring. The elements
    of the list will be rendered by calling the function passed to
    stringify, which is by default 'str'.
    """
    def __init__(self,
                 choices=None,
                 choicesAttribute=None,
                 stringify=str,
                 *args, **kw):
        super(MultipleChoice, self).__init__(*args, **kw)
        if choices is None:
            self.choices = []
        else:
            self.choices = choices
        self.choicesAttribute = choicesAttribute
        self.stringify = stringify

    def coerceWithBinding(self, values, binding):
        """Coerce a value with the help of an object, which is the object
        we are configuring.
        """
        int_values = []
        try:
            for val in values:
                int_values.append(int(val))
        except ValueError:
            raise annotate.InputError("%s contains an invalid choice." % str(values))
        if self.choicesAttribute is not None:
            choices = getattr(binding, self.choicesAttribute)
        else:
            choices = self.choices
        return [choices[val] for val in int_values]


class MultipleChoiceInputProcessor(compy.Adapter):
    __implements__ = iformless.IInputProcessor,

    def process(self, context, boundTo, data):
        """data is a list of strings at this point
        """
        typed = self.original

        if data[0] == '':
            if typed.required:
                raise annotate.InputError(typed.requiredFailMessage)
            else:
                return []
        elif hasattr(typed, 'coerceWithBinding'):
            return typed.coerceWithBinding(data, boundTo)
        return typed.coerce(data)


class MultipleChoiceRenderer(webform.BaseInputRenderer):
    def input(self, context, slot, data, name, value):
        tv = data.typedValue
        if tv.choicesAttribute:
            conf = context.locate(iformless.IConfigurable)
            choices = getattr(conf, tv.choicesAttribute)
        else:
            choices = tv.choices

        numChoices = len(choices)
        if numChoices == 0:
            return None

        selecter = tags.select(name=name, size=min(5,numChoices), multiple="multiple")
        stringify = tv.stringify

        for index, val in enumerate(choices):
            if val in value:
                selecter[tags.option(value=str(index),
                                     selected="selected")[stringify(val)]]
            else:
                selecter[tags.option(value=str(index))[stringify(val)]]
        return slot[selecter]

compy.registerAdapter(MultipleChoiceRenderer,
                      MultipleChoice,
                      iformless.ITypedRenderer)
compy.registerAdapter(MultipleChoiceInputProcessor,
                      MultipleChoice,
                      iformless.IInputProcessor)
