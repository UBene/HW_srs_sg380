
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCompleter, QLineEdit

from ..editors import EditorUI
from ..item import Item


class Function(Item):

    item_type = 'function'

    def visit(self):
        self.kwargs
        if self.kwargs['type'] == 'function':
            s = 'self.app.' + \
                self.kwargs['function'] + '(' + self.kwargs['args'] + ')'
            print(eval(s))


class ExecFunction(EditorUI):

    item_type = 'function'
    description = 'eval a function'

    def __init__(self, measure, all_functions) -> None:
        self.all_functions = all_functions
        super().__init__(measure)

    def setup_ui(self):
        self.function_le = QLineEdit()
        completer = QCompleter(self.all_functions)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.function_le.setCompleter(completer)
        self.function_le.setToolTip('path to a function')
        self.args_le = QLineEdit()
        self.args_le.setToolTip('function arguments')
        self.layout.addWidget(self.function_le)
        self.layout.addWidget(self.args_le)

    def get_kwargs(self):
        f = self.function_le.text()
        args = self.args_le.text()
        return {'function': f, 'args': args}

    def edit_item(self, **kwargs):
        self.function_le.setText(kwargs['function'])
        self.args_le.setText(kwargs['args'])
        self.args_le.selectAll()
