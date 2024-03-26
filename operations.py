# operations that transform dependency structures and can be piped if types match

import sys
import os  # temporarily, to call VisualizeUD.hs
from dataclasses import dataclass
from typing import Iterable, Callable
from trees import *
from patterns import *
from visualize_ud import conll2svg
from udpipe2_client import process
from yaml import safe_load

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
                ['output type', str(t1), 'of', self.name,
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
def conllu2trees(lines: CoNLLU) -> Iterable[DepTree]:
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
def trees2strs(trees: Iterable[DepTree]) -> Iterable[str]:
    "convert wordlines to tab-separated strings line by line"
    for tree in trees:
        yield str(tree)
        yield ''


@operation
def trees2wordliness(trees: Iterable[DepTree]) -> Iterable[list[WordLine]]:
    "convert a stream of deptrees to a stream of relabeled lists of wordlines"
    for tree in trees:
        tree = relabel_deptree(tree)
        yield tree.wordlines()

@operation
def trees2conllu(trees: Iterable[DepTree]) -> Iterable[str]:
    "convert a stream of deptrees to a stream of relabeled lists of wordlines"
    for tree in trees:
        tree = relabel_deptree(tree)
        for line in tree.comments + list(map(str, tree.wordlines())):
            yield line
        yield ''


@operation
def trees2wordlines(trees: Iterable[DepTree]) -> Iterable[WordLine]:
    "convert a stream of deptrees to a stream wordlines"
    for tree in trees:
        for line in tree.wordlines():
            yield line


@operation
def wordliness2conllu(stanzas: Iterable[list[WordLine]]) -> CoNLLU:
    "convert a stream of lists of wordlines to relabelled empty-line-separated stanzas"
    for ws in stanzas:
        yield '# ' + ' '.join([w.FORM for w in ws])
        for w in ws:
            yield str(w)
        yield ''
        

@operation
def wordlines2sentences(wordliness: Iterable[list[WordLine]]) -> Iterable[str]:
    "extract sentences from a stream of lists of wordlines, using the FORM fields"
    for wordlines in wordliness:
        yield ' '.join([word.FORM for word in wordlines])


# operation that extracts a sentence from a dependency tree
extract_sentences : Operation = pipe([trees2wordliness, wordlines2sentences])


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


def count_wordlines() -> Operation:
    return Operation (
        lambda ws: [len(list(ws))],
        Iterable[WordLine],
        list[int],
        'count_wordlines',
        "return the number of wordlines"
        )


def count_trees() -> Operation:
    return Operation (
        lambda ws: [len(list(ws))],
        Iterable[DepTree],
        list[int],
        'count_trees',
        "return the number of trees"
        )


def match_wordlines(patt: Pattern) -> Operation:
    return Operation (
        lambda ws: (w for w in ws if match_wordline(patt, w)),
        Iterable[WordLine],
        Iterable[WordLine],
        'match_wordlines',
        'pattern matching with wordlines, yielding the ones that match'
        )
        

def match_trees(patt: Pattern) -> Operation:

    def matcht(ts):
        for tr in ts:
            for t in matches_of_deptree(patt, tr):
                yield t
                
    return Operation (
        matcht,
        Iterable[DepTree],
        Iterable[DepTree],
        'match_trees',
        'pattern matching with entire trees, yielding the ones that match'
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


def match_segments(patt: Pattern) -> Operation:
    def matcht(ts):
        for segm in matches_in_tree_stream(patt, ts):
            segm[0].prefix_comments(['# FIRST IN SEGMENT length ' + str(len(segm))])
            segm[-1].prefix_comments(['# LAST IN SEGMENT'])
            for tree in segm:
                yield tree
    return Operation(
        matcht,
        Iterable[DepTree],
        Iterable[DepTree],
        'match_segments',
        'pattern matching contiguous segments, marking the ones that match'
        )
        

def change_wordlines(patt: Pattern) -> Operation:
    return Operation (
        lambda ws: (change_wordline(patt, w) for w in ws),
        Iterable[WordLine],
        Iterable[WordLine],
        'change_wordlines',
        'pattern-based changes in wordlines'
        )    


def change_trees(patt: Pattern) -> Operation:
    return Operation (
        lambda ws: (change_deptree(patt, w) for w in ws),
        Iterable[DepTree],
        Iterable[DepTree],
        'change_subtrees',
        'pattern-based changes in trees (no recursion to subtrees)'
        )


def change_subtrees(patt: Pattern) -> Operation:
    return Operation (
        lambda ws: (changes_in_deptree(patt, w) for w in ws),
        Iterable[DepTree],
        Iterable[DepTree],
        'change_subtrees',
        'pattern-based changes recursively in subtrees, top-down'
        )


@operation
def visualize_conllu(s: Iterable[str]) -> Iterable[str]:
    'show CoNLLU as SVG in HTML'
    s = '\n'.join([s.strip() for s in s])  ## type of conll2svg should be It[str] 
    return conll2svg(s)

@operation
def txt2conllu(corpus: Iterable[str]) -> CoNLLU:
    "parse a raw text corpus into CoNNL-U, using UDPipe2"
    corpus = '\n'.join([line.strip() for line in corpus])
    with open("udpipe2_params.yaml") as f:
        udpipe2_params = safe_load(f)
    udpipe2_params = {
        "data": corpus,
        "model": udpipe2_params["model"],
        # empty strings (as opposed to None) will enable these components)
        "tokenizer": "", "parser": "", "tagger": "",
        "outfile": None, # stdout
        "service": "https://lindat.mff.cuni.cz/services/udpipe/api"
    }
    parsed = process(udpipe2_params)
    for line in parsed.split("\n"):
        yield line

def from_script(filename: str) -> Operation:
    "reads an operation by parsing a file"
    with open(filename) as script:
        return parse_operation_pipe(script.read())
            

def parse_operation(ss: list[str]) -> Operation:
    "operation parser for files and command line arguments"
    match ss:
        case ['count_wordlines', *ww]:
            return count_wordlines()
        case ['count_trees', *ww]:
            return count_trees()
        case ['match_wordlines', *ww]:
            return match_wordlines(parse_pattern(' '.join([*ww])))
        case ['match_subtrees', *ww]:
            return match_subtrees(parse_pattern(' '.join([*ww])))
        case ['match_trees', *ww]:
            return match_trees(parse_pattern(' '.join([*ww])))
        case ['match_segments', *ww]:
            return match_segments(parse_pattern(' '.join([*ww])))
        case ['change_wordlines', *ww]:
            return change_wordlines(parse_pattern(' '.join([*ww])))
        case ['change_trees', *ww]:
            return change_trees(parse_pattern(' '.join([*ww])))
        case ['change_subtrees', *ww]:
            return change_subtrees(parse_pattern(' '.join([*ww])))
        case ['extract_sentences']:
            return extract_sentences
        case ['trees2conllu']:
            return trees2conllu
        case ['trees2wordlines']:
            return trees2wordlines
        case ['take_trees', begin, end]:
            return take_trees(int(begin), int(end))
        case ['statistics', *ww]:
            return statistics(ww)
        case ['underscore_fields', *ww]:
            return undescore_fields(ww)
        case ['visualize_conllu']:
            return visualize_conllu
        case ['from_script', filename]:
            return from_script(filename)
        case ['txt2conllu']:
            return txt2conllu
        case ['conllu2trees']:
            return conllu2trees
        case _:
            raise ParseError(' '.join(['operation'] + ss + ['not matched']))


def parse_operation_pipe(s: str) -> Operation:
    "parsing operation pipes separated by |"
    return pipe([parse_operation(op.split()) for op in s.split('|')])


def preprocess_operation(op: Operation) -> Operation:
    "convert file-like input into type expected by operation"
    if op.argtype == Iterable[WordLine]:
        return pipe([conllu2wordlines, op])
    elif op.argtype == Iterable[DepTree]:
        return pipe([conllu2trees, op])
    else:
        return op

    
def postprocess_operation(op: Operation) -> Operation:
    "convert the output of operations to strings"
    if op.valtype == Iterable[WordLine]:
        return pipe([op, wordlines2strs])
    elif op.valtype == Iterable[DepTree]:
        return pipe([op, trees2strs])
    elif op.valtype == Iterable[list[WordLine]]:
        return pipe([op, wordliness2conllu]) 
    else:
        return op

    
# an example of "static typing", i.e. checked and rejected before applied to input
# invalid_operation = pipe([conllu2wordlines, conllu2wordlines])


def execute_pipe_on_strings(command: str, strs: Iterable[str]):
    "apply a command to a stream of strings, with pre- and postprocessing if needed"
    oper = parse_operation_pipe(command)
    oper = preprocess_operation(oper)
    oper = postprocess_operation(oper)
    print('# ', oper)

    for t in oper(strs):
        print(t)


