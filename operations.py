# operations that transform dependency structures and can be piped if types match

import sys
import os  # temporarily, to call VisualizeUD.hs
from dataclasses import dataclass
from typing import Iterable, Callable
from trees import *
from patterns import *


@dataclass
class Operation:
    "typed stream operations"
    oper: Callable
    argtype: type
    valtype: type
    name: str
    doc: str
    
    def __call__(self, arg):
        return self.oper(arg)
    def __doc__(self):
        return doc

    def pipe_two(self, oper2):
        "apply self, then apply another operation on the result"
        if (t1 := self.valtype) == (t2 := oper2.argtype):
            return Operation(
                lambda x: oper2(self(x)),
                self.argtype,
                oper2.valtype,
                self.name + ' | ' + oper2.name,
                '\n'.join([self.doc, 'then' + oper2.doc])
                )
        else:
            raise TypeError(' '.join(
                ['output type', str(t1), 'of', oper1.name,
                     'does not match input type', str(t2), 'of', oper2.name]))
        
    def __mul__(self, oper1):
        return pipe_two(oper1, self)
        
    
def operation(f: Callable) -> Operation:
    "a decorator that makes a one-argument function into an operation"
    if len(anns := f.__annotations__) == 2 and 'return' in anns:
        return Operation(
                f,
                list(anns.values())[0],
                anns['return'],
                f.__name__,
                f.__doc__)
    else:
        raise TypeError("expected type-decorated one-argument function, found " + f.__name__)

    
def pipe(opers: list[Operation]) -> Operation:
    "pipe a list of operations together"
    oper = opers[0]
    for oper2 in opers[1:]:
        oper = oper.pipe_two(oper2)
    return oper


# CoNLL-U input is a stream of lines representing a valid stream of trees
CoNLLU = Iterable[str]


@operation
def conllu2wordlines(lines: CoNLLU) -> Iterable[WordLine]:
    "read a sequence of strings as WordLines, ignoring failed ones"
    for line in lines:
        try:
            word = read_wordline(line)
            yield word
        except:
            pass


@operation
def conllu2deptrees(lines: CoNLLU) -> Iterable[DepTree]:
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
    "convert a stream of deptrees to a stream of relabeled lists of wordlines"
    for tree in trees:
        tree = relabel_deptree(tree)
        yield tree.wordlines()


@operation
def wordliness2conllu(stanzas: Iterable[list[WordLine]]) -> CoNLLU:
    "convert a stream of lists of wordlines to empty-line-separated stanzas"
    for ws in stanzas:
        for w in ws:
            yield str(w)
        yield ''
        

@operation
def wordlines2sentences(wordliness: Iterable[list[WordLine]]) -> Iterable[str]:
    "extract sentences from a stream of lists of wordlines, using the FORM fields"
    for wordlines in wordliness:
        yield ' '.join([word.FORM for word in wordlines])


@operation
def undescore_fields(fields: list[str]) -> Operation:
    return Operation (
        lambda ws: (replace_by_underscores(fields, w) for w in ws),
        Iterable[WordLine],
        Iterable[WordLine],
        "underscore fields",
        "replace the values of given fields by underscores"
        )

def take_trees(begin: int, end: int) -> Operation:
    
    def take(ts):
        i = begin
        while i < end:
            yield(next(ts))
            i += 1
            
    return Operation (
        take,
        Iterable[DepTree],
        Iterable[DepTree],
        "take_trees",
        "take a selection of trees from <begin> to <end>-1 (counting from 0)"
        )

        
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


# @operation
# def wordlines2latex(stanzas: Iterable[list[WordLine]]) -> str:
#     wordliness2strs(stanzas) 
    
        

def change_wordlines(patt: Pattern) -> Operation:
    return Operation (
        lambda ws: (change_in_wordline(patt, w) for w in ws),
        Iterable[WordLine],
        Iterable[WordLine],
        'match_wordlines',
        'pattern matching with wordlines, yielding the ones that match'
        )    


def parse_operation(ss: list[str]) -> Operation:
    match ss:
        case ['match_wordlines', *ww]:
            return match_wordlines(parse_pattern(' '.join([*ww])))
        case ['match_subtrees', *ww]:
            return match_subtrees(parse_pattern(' '.join([*ww])))
        case ['change_wordlines', *ww]:
            return change_wordlines(parse_pattern(' '.join([*ww])))
        case ['deptrees2wordlines']:
            return deptrees2wordlines
        case ['take_trees', begin, end]:
            return take_trees(int(begin), int(end))
        case ['statistics', *ww]:
            return statistics(ww)
        case ['underscore_fields', *ww]:
            return undescore_fields(ww)
        case _:
            raise ParseError(' '.join(['operation'] + ss + ['not matched']))


def parse_operation_pipe(s: str) -> Operation:    
    return pipe([parse_operation(op.split()) for op in s.split('|')])


def preprocess_operation(op: Operation) -> Operation:
    "convert file-like input into type expected by operation"
    if op.argtype == Iterable[WordLine]:
        return pipe([conllu2wordlines, op])
    elif op.argtype == Iterable[DepTree]:
        return pipe([conllu2deptrees, op])
    else:
        return op

    
def postprocess_operation(op: Operation) -> Operation:
    "convert the output of operations to strings"
    if op.valtype == Iterable[WordLine]:
        return pipe([op, wordlines2strs])
    elif op.valtype == Iterable[DepTree]:
        return pipe([op, deptrees2strs])
    elif op.valtype == Iterable[list[WordLine]]:
        return pipe([op, wordliness2conllu]) 
    else:
        return op

    
# an example of "static typing", i.e. checked and rejected before applied to input
# invalid_operation = pipe([conllu2wordlines, conllu2wordlines])


def execute_pipe_on_strings(command: str, strs: Iterable[str]): 
    oper = parse_operation_pipe(command)
    oper = preprocess_operation(oper)
    oper = postprocess_operation(oper)
    print('# ', oper)
    for t in oper(strs):
        print(t)


