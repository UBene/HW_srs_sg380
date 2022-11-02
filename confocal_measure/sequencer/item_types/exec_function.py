from typing_extensions import Self, TypedDict

from qtpy.QtWidgets import QLineEdit

from .helper_func import new_q_completer
from ..editors import EditorUI
from ..item import Item
from .item_factory import register_item


class ExecFunctionKwargs(TypedDict):
    function: str
    args: str


class Function(Item):

    item_type = 'function'

    def visit(self) -> None:
        s = 'self.app.' + self.kwargs['function'] + \
            '(' + self.kwargs['args'] + ')'
        print(eval(s))


register_item(Function)


class ExecFunctionEditorUI(EditorUI):

    item_type = 'function'
    description = 'eval a function'

    def __init__(self, measure, all_functions) -> None:
        self.all_functions = all_functions
        super().__init__(measure)

    def setup_ui(self):
        self.function_le = QLineEdit()
        completer = new_q_completer(self.all_functions)
        self.function_le.setCompleter(completer)
        self.function_le.setToolTip('path to a function')
        self.args_le = QLineEdit()
        self.args_le.setToolTip('function arguments')
        self.layout.addWidget(self.function_le)
        self.layout.addWidget(self.args_le)

    def get_kwargs(self) -> ExecFunctionKwargs:
        f = self.function_le.text()
        args = self.args_le.text()
        return {'function': f, 'args': args}

    def edit_item(self, **kwargs):
        self.function_le.setText(kwargs['function'])
        self.args_le.setText(kwargs['args'])
        self.args_le.selectAll()
