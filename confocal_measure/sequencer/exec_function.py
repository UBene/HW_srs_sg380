
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCompleter, QLineEdit

from .editors import EditorUI
from .list_items import Item


class Function(Item):

    item_type = 'function'

    def visit(self):
        self.kwargs
        if self.kwargs['type'] == 'function':
            s = 'self.app.' + \
                self.kwargs['function'] + '(' + self.kwargs['args'] + ')'
            print(s)
            print(eval(s))


class ExecFunction(EditorUI):

    item_type = 'function'
    description = 'eval a function'

    def __init__(self, measure, all_functions) -> None:
        self.all_functions = all_functions
        super().__init__(measure)

    def setup_ui(self):

        function_execute_layout = self.group_box.layout()
        self.function_lineEdit = QLineEdit()
        completer = QCompleter(self.all_functions)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.function_lineEdit.setCompleter(completer)
        self.function_lineEdit.setToolTip('path to a function')
        self.function_args_lineEdit = QLineEdit()
        self.function_args_lineEdit.setToolTip('function arguments')
        function_execute_layout.addWidget(self.function_lineEdit)
        function_execute_layout.addWidget(self.function_args_lineEdit)

    def get_kwargs(self):
        f = self.function_lineEdit.text()
        args = self.function_args_lineEdit.text()
        return {'function': f, 'args': args}

    def on_focus(self, d):
        self.function_lineEdit.setText(d['function'])
        self.function_args_lineEdit.setText(d['args'])
        self.function_args_lineEdit.selectAll()
