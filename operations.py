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
def strs2deptrees(lines: Iterable[str]) -> Iterable[DepTree]:
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
def wordlines2strs(lines: Iterable[WordLine]) -> Iterable[str]:
    "convert wordlines to tab-separated strings line by line"
    for line in lines:
        yield str(line)

        
@operation
def deptrees2strs(trees: Iterable[DepTree]) -> Iterable[str]:
    "convert wordlines to tab-separated strings line by line"
    for tree in trees:
        yield str(tree)
        yield ''
        

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


def statistics(fields: list[str]) -> Operation:
    return Operation (
        lambda ws: sorted_statistics(wordline_statistics(fields, ws)),
        Iterable[WordLine],
        list,
        'statistics',
        "frequency table of a combination of fields, sorted as a list in descending order"
        )


def match_wordlines(patt: Pattern) -> Operation:
    return Operation (
        lambda ws: (w for w in ws if match_wordline(patt, w)),
        Iterable[WordLine],
        Iterable[WordLine],
        'match_wordlines',
        'pattern matching with wordlines, yielding the ones that match'
        )
        

def match_subtrees(patt: Pattern) -> Operation:

    def matcht(ts):
        for tr in ts:
            for t in matches_in_deptree(patt, tr):
                yield t
                
    return Operation (
        matcht,
        Iterable[DepTree],
        Iterable[DepTree],
        'match_subtrees',
        'pattern matching with trees and subtrees, yielding the ones that match'
        )


def parse_operation(ss: list[str]) -> Operation:
    match ss:
        case ['match_wordlines', *ww]:
            return match_wordlines(parse_pattern(' '.join([*ww])))
        case ['match_subtrees', *ww]:
            return match_subtrees(parse_pattern(' '.join([*ww])))
        case ['statistics', *ww]:
            return statistics(ww)
        case _:
            raise ParseError(' '.join(['operation'] + ss + ['not matched']))


def parse_operation_pipe(s: str) -> Operation:    
    return pipe([parse_operation(op.split()) for op in s.split('|')])


def preprocess_operation(op: Operation) -> Operation:
    "convert file-like input into type expected by operation"
    if op.argtype == Iterable[WordLine]:
        return pipe([strs2wordlines, op])
    elif op.argtype == Iterable[DepTree]:
        return pipe([strs2deptrees, op])
    else:
        return op

    
def postprocess_operation(op: Operation) -> Operation:
    "convert the output of operations to strings"
    if op.valtype == Iterable[WordLine]:
        return pipe([op, wordlines2strs])
    elif op.valtype == Iterable[DepTree]:
        return pipe([op, deptrees2strs])
    else:
        return op
        
        
if __name__ == '__main__':
    oper = parse_operation_pipe(sys.argv[1])
    oper = preprocess_operation(oper)
    oper = postprocess_operation(oper)
    print('# ', oper)
    for t in oper(sys.stdin):
        print(t)


