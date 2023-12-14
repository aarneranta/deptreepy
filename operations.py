# operations that transform dependency structures and can be piped if types match

import sys
from dataclasses import dataclass
from typing import Iterable, Callable
from trees import *
from patterns import *


@dataclass
class Operation:
    oper: Callable
    argtype: type
    valtype: type
    name: str
    doc: str
    
    def __call__(self, arg):
        return self.oper(arg)
    def __doc__(self):
        return doc


def operation(f: Callable) -> Operation:
    if len(anns := f.__annotations__) == 2 and 'return' in anns:
        return Operation(
                f,
                list(anns.values())[0],
                anns['return'],
                f.__name__,
                f.__doc__)
    else:
        raise TypeError("expected type-decorated one-argument function, found " + f.__name__)


def pipe_two(oper1: Operation, oper2: Operation) -> Operation:
    if (t1 := oper1.valtype) == (t2 := oper2.argtype):
        return Operation(
            lambda x: oper2(oper1(x)),
            oper1.argtype,
            oper2.valtype,
            oper1.name + ' | ' + oper2.name,
            '\n'.join([oper1.doc, 'then' + oper2.doc])
            )
    else:
        raise TypeError(' '.join(
            ['output type', str(t1), 'of', oper1.name,
                 'does not match input type', str(t2), 'of', oper2.name]))

    
def pipe(opers: list[Operation]) -> Operation:
    oper = opers[0]
    for oper2 in opers[1:]:
        oper = pipe_two(oper, oper2)
    return oper
    

@operation
def strs2wordlines(lines: Iterable[str]) -> Iterable[WordLine]:
    "read a sequence of strings as WordLines, ignoring failed ones"
    for line in lines:
        try:
            word = read_wordline(line)
            yield word
        except:
            pass


@operation
def lines2deptrees(lines: Iterable[str]) -> Iterable[DepTree]:
    "convert a list of lines into a deptree"
    comms = []
    nodes = []
    for line in lines:
        if line.startswith('#'):
            comms.append(line.strip())
        elif line.strip():
            t = read_wordline(line)
            nodes.append(t)
        else:
            dt = build_deptree(nodes)
            dt.comments = comms
            yield dt
            comms = []
            nodes = []


@operation
def deptrees2wordlines(trees: Iterable[DepTree]) -> Iterable[list[WordLine]]:
    "convert a stream of deptrees to a list of lists of wordlines"
    for tree in trees:
        yield tree.wordlines()


@operation
def wordlines2sentences(wordliness: Iterable[list[WordLine]]) -> Iterable[str]:
    "extract sentences from a stream of lists of wordlines, using the FORM fields"
    for wordlines in wordliness:
        yield ' '.join([word.FORM for word in wordlines])


def word_match(s: str) -> Operation:
    patt = parse_pattern(s)
    return Operation (
        lambda ws: (w for w in ws if match_wordline(patt, w)),
        Iterable[WordLine],
        Iterable[WordLine],
        'word_match',
        'pattern matching with wordlines, yielding the ones that match'
        )
        

def subtree_match(s: str) -> Operation:
    patt = parse_pattern(s)
    def matcht(ts):
        for tr in ts:
            for t in matches_in_deptree(patt, tr):
                yield t
    return Operation (
        matcht,
        Iterable[DepTree],
        Iterable[DepTree],
        'subtree_match',
        'pattern matching with trees and subtrees, yielding the ones that match'
        )
        
if __name__ == '__main__':
    oper = lines2deptrees
    oper = pipe([lines2deptrees, deptrees2wordlines, wordlines2sentences])
    oper = pipe([lines2deptrees, subtree_match('DEPREL nsubj'), deptrees2wordlines, wordlines2sentences])
    for t in oper(sys.stdin):
        print(t)
        print()

