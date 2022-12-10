from typing_extensions import Protocol, Self, Type

from ..item import Item


# class ItemProtocol(Protocol):

#     item_type: str

#     def visit(self) -> None | Self:
#         ...

#     def reset(self) -> None:
#         ...


factories = {}


def register_item(item: Type[Item]):
    factories[item.item_type] = item


def item_factory(measure, item_type: str, **kwargs):
    return factories[item_type](measure, **kwargs)
