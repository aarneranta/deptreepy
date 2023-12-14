# operations that transform dependency structures and can be piped if types match

from dataclasses import dataclass
from typing import Iterable, Callable
from trees import *


@dataclass
class Operation:
    oper: Callable
    argtype: type
    valtype: type
    doc: str
    
    def __call__(self, arg):
        return self.oper(arg)
    def __doc__(self):
        return doc


def pipe_two(oper1: Operation, oper2: Operation) -> Operation:
    if oper1.valtype == oper2.argtype:
        return Operation(
            lambda x: oper2(oper1(x)),
            oper1.argtype,
            oper2.valtype,
            '\n'.join([oper1.doc, 'then' + oper2.doc])
            )
    else:
        raise TypeError("operation types do not match in pipe")

def pipe(opers: list[Operation]) -> Operation:
    oper = opers[0]
    for oper2 in opers[1:]:
        oper = pipe_two(oper, oper2)
    return oper
    
    

def str2wordline(line: str) -> WordLine:
    "read a string as a WordLine, fail if not valid"
    return read_wordline(line)

s2w = Operation(
    str2wordline,
    str,
    WordLine,
    "read a string as a WordLine, fail if not valid"
    )

w2lemma = Operation(
    lambda w: w.LEMMA,
    WordLine,
    str,
    "return the LEMMA"
    )


def strs2wordlines(lines: Iterable[str]) -> Iterable[WordLine]:
    "read a sequence of strings as WordLines, ignoring failed ones"
    for line in lines:
        try:
            word = str2wordline(line)
            yield word
        except:
            pass
        

def wordlines2deptree(wordlines: list[WordLine]) -> DepTree:
    "convert a list of wordlines into a deptree"
    return build_deptree(wordlines)


def deptree2wordlines(tree: DepTree) -> list[WordLine]:
    "convert a deptree to a list of wordlines"
    return tree.wordlines()


def wordlines2sentence(wordlines: list[WordLine]) -> str:
    "extract a sentence from a list of wordlines, using the FORM fields"
    return ' '.join([word.FORM for word in self.wordlines()])



if __name__ == '__main__':

    example = "1	This	this	DET	DT	Number=Sing|PronType=Dem	4	det	4:det	_"
    print(pipe([s2w, s2w])(example))

