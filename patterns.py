from dataclasses import dataclass
from fnmatch import fnmatch
from pyparsing import nestedExpr
from trees import *


def match_str(patt: str, word: str) ->bool:
    "matching strings with wildcards * anywhere"
    return fnmatch(word, patt)


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
        case Pattern(field, [form]) if field in WORDLINE_FIELDS:
            return match_str(form, word.as_dict()[field])
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
            case Pattern ('IS_NONPROJECTIVE', _):
                return nonprojective(tree)
            case Pattern('TREE', [pt, *patts]):
                return (len(patts) == len(sts := tree.subtrees) 
                         and match_deptree(pt, tree)
                         and all(match_deptree(*pt) for pt in zip(patts, sts)))
            case Pattern('TREE_', [pt, *patts]):
                return (match_deptree(pt, tree)
                         and all(any(match_deptree(p, t) for t in tree.subtrees) for p in patts))
            case Pattern('SEQUENCE', patts):
                return (len(patts) == len(sts := tree.wordlines()) 
                         and all(match_wordline(*pt) for pt in zip(patts, sts)))
            case Pattern('SEQUENCE_', patts):
                return (all(any(match_wordline(p, t) for t in tree.wordlines()) for p in patts))
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


def match_wordlines(patt, lines):
    for line in lines:
        try:
            t = read_wordline(line)
            if match_wordline(patt, t):
                print(t)
        except:
            pass

            
def matches_in_deptree(patt: Pattern, tree: DepTree) -> bool:
    "finding all subtrees that match a pattern"
    ts = []
    if match_deptree(patt, tree):
        ts.append(tree)
    for subtree in tree.subtrees:
        ts.extend(matches_in_deptree(patt, subtree))
    return ts


def change_wordline(patt: Pattern, word: WordLine) ->WordLine:
    "changing the value of some field in accordance with a pattern"
    match patt:
        case Pattern('IF', [condpatt, changepatt]):
            if match_wordline(condpatt, word):
                return change_wordline(changepatt, word)
            else:
                return word
        case Pattern(field, [oldval, newval]) if field in WORDLINE_FIELDS:
            wdict = word.as_dict()
            if match_str(oldval, wdict[field]):
                wdict[field] = newval
                return WordLine(**wdict)
            else:
                return word
        case _:
            return word


def change_deptree(patt: Pattern, tree: DepTree) -> DepTree:
    "change a tree in accordance with a pattern"
    match patt:
        case Pattern('IF', [condpatt, changepatt]):
            if match_deptree(condpatt, tree):
                return change_deptree(changepatt, tree)
            else:
                return tree
        case Pattern('PRUNE', [depth]):
            depth = int(depth)
            return prune_subtrees_below(tree, depth)
        case _:
            return tree

    
def changes_in_deptree(patt: Pattern, tree: DepTree) -> DepTree:
    "performing change in a tree and recursively in all changed subtrees"
    tree = change_deptree(patt, tree)
    tree.subtrees = [change_deptree(patt, t) for t in tree.subtrees]
    return tree

    
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
            print(tree)  # relabel_deptree(tree))
            print()


# to be deprecated
def change_line_wordlines(patt, lines):
    for line in lines:
        try:
            t = read_wordline(line)
            t = change_in_wordline(patt, t)
            print(t)
        except:
            print(line.strip())


        
        
