from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCompleter


def new_q_completer(l: list[str]) -> QCompleter:
    completer = QCompleter(l)
    completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    completer.setModelSorting(QCompleter.ModelSorting.UnsortedModel)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    return completer
