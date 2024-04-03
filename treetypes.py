from dataclasses import dataclass
from typing import Iterable

from trees import *

@dataclass
class TreeType:
    "the 'type' of a deptree: (POS, DEPREL)[(POS, DEPREL)*] of head and dependents"
    head: tuple[str]
    deps: list[tuple[str]]   # POS, DEPREL

    
    def __str__(self):
        return str(self.head) + str(self.deps)

    def __hash__(self):
        return self.__str__().__hash__()


def deptree2treetype(tree: DepTree, fields: list[str]) -> TreeType:
#    if fs := [f not in WORDLINE_FIELDS for f in fields]:
 #       raise TypeError('invalid fields ' + str(fs))
    head = tuple(tree.root.as_dict()[f] for f in fields)
    deps = [tuple(t.root.as_dict()[f] for f in fields) for t in tree.subtrees]
    return TreeType(head, deps)


def deptree2treetypes(tree: DepTree, fields: list[str]) -> list[TreeType]:
    typs = [deptree2treetype(tree, fields)]
    for t in tree.subtrees:
        for typ in deptree2treetypes(t, fields):
            typs.append(typ)
    return typs


def treetype_statistics_dict(trees: Iterable[DepTree], fields: list[str]) -> dict[TreeType, int]:
    dict = {}
    for tree in trees:
        for typ in deptree2treetypes(tree, fields):
            if typ in dict:
                dict[typ] += 1
            else:
                dict[typ] = 1

    return dict


def head_dep_statistics_dict(trees: Iterable[DepTree], fields: list[str]) -> dict[tuple[tuple[str], tuple[str]], int]:
    dict = {}
    for tree in trees:
        for typ in deptree2treetypes(tree, fields):
            for item in typ.deps:
                dtyp = (typ.head, item)
                if dtyp in dict:
                    dict[dtyp] += 1
                else:
                    dict[dtyp] = 1

    return dict





