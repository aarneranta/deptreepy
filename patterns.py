from dataclasses import dataclass
from pyparsing import nestedExpr
from trees import *


def match_str(patt: str, word: str) ->bool:
    "matching strings with wildcards * anywhere"

    # split patt into parts between *; ** reduces to *
    parts = []
    if patt.startswith('*'):
        parts.append('*')
    parts.extend(patt.split('*'))
    if patt.endswith('*'):
        parts.append('*')
    parts = [p for p in parts if p]  # removing empty strings

    # find matches part by part, shrinking the string
    while parts:
        if parts[0] == '*':    
            if parts[1:]:  # must be nonempty and not *
                if (p := parts[1]) in word:
                    word = word[word.index(p)+len(p):]
                    parts.pop(0)
                    parts.pop(0)
                else:
                    return False
            else:  # the last pattern was *, any tail matches
                return True
        elif word.startswith(p := parts[0]):
            word = word[len(p):]
            parts.pop(0)
        else:
            return False
    return word == ''  # pattern exhausted, the word must be too


def intpred(n, x):
    "condition compared with a number: =8, <8, >8, !8"
    number = int(n[1:])
    match n[0]:
        case '=': return x == number
        case '!': return x != number
        case '<': return x < number
        case '>': return x > number
    

@dataclass
class Pattern(Tree):
    def __str__(self):
        if sts := self.subtrees:
            return '(' + ' '.join([self.root] + [t.__str__() for t in sts]) + ')'
        else:
            return self.root
        

def match_wordline(patt: Pattern, word: WordLine) ->bool:
    "matching individual wordlines"
    match patt:
        case Pattern('FORM', [form]):
            return match_str(form, word.FORM)
        case Pattern('LEMMA', [lemma]):
            return match_str(lemma, word.LEMMA)
        case Pattern('POS', [pos]):
            return match_str(pos, word.POS)
        case Pattern('FEATS', [feats]):
            return match_str(feats, word.FEATS)
        case Pattern('DEPREL', [rel]):
            return match_str(rel, word.DEPREL)
        case Pattern('HEAD_DISTANCE', [n]):
            return intpred(n, int(word.HEAD) - int(word.ID)) if word.ID.isdigit() else False
        case Pattern('AND', patts):
            return all(match_wordline(p, word) for p in patts) 
        case Pattern('OR', patts):
            return any(match_wordline(p, word) for p in patts)
        case Pattern('NOT', [patt]):
            return not (match_wordline(patt, word))
        case _:
            return False

def match_deptree(patt: Pattern, tree: DepTree) ->bool:
    "matching entire trees - either their root wordline or the whole tree"
    if match_wordline(patt, tree.root):
        return True
    else:
        match patt:
            case Pattern('LENGTH', [n]):
                return intpred(n, len(tree))
            case Pattern('DEPTH', [n]):
                return intpred(n, tree.depth())
            case Pattern('TREE', [pt, *patts]):
                return (len(patts) == len(sts := tree.subtrees) 
                         and match_deptree(pt, tree)
                         and all(match_deptree(*pt) for pt in zip(patts, sts)))
            case Pattern('HAS_SUBTREE', patts):
                return any(all(match_deptree(p, st) for p in patts) for st in tree.subtrees) 
            case Pattern('AND', patts):  # must be defined again for tree patterns
                return all(match_deptree(p, tree) for p in patts) 
            case Pattern('OR', patts):
                return any(match_deptree(p, tree) for p in patts)
            case Pattern('NOT', [patt]):
                return not (match_deptree(patt, tree))
            case _:
                return False
        

            
def matches_in_deptree(patt: Pattern, tree: DepTree):
    "finding all subtrees that match a pattern"
    ts = []
    if match_deptree(patt, tree):
        ts.append(tree)
    for subtree in tree.subtrees:
        ts.extend(matches_in_deptree(patt, subtree))
    return ts


class ParseError(Exception):
    pass


def parse_pattern(s: str) ->Pattern:
    "to get a pattern from a string"
    if not s.startswith('('):  # add outer parentheses if missing
        s = '(' + s + ')'
    parse = nestedExpr().parseString(s)
    def to_pattern(lisp):
        match lisp:
            case [fun, *args]:
                args = [to_pattern(arg) for arg in args]
                return Pattern(fun, args)
            case tok:
                return tok
    return to_pattern(parse[0])

        
# example:
# AND (DEPREL *subj) (POS V*) (FEATS *=Ind*)
example_pattern = Pattern('AND',
                    [Pattern('DEPREL', ['*subj']),
                     Pattern('POS', ['V*']),
                     Pattern('FEATS', ['*=Ind*'])])


def match_wordlines(patt, lines):
    for line in lines:
        try:
            t = read_wordline(line)
            if match_wordline(patt, t):
                print(t)
        except:
            pass

        
def match_subtrees(patt, file):
    for deptree in conllu_file_trees(file):
        for tree in matches_in_deptree(patt, deptree):
            print('#', tree.sentence())
            print(tree)

        
