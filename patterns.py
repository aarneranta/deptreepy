import sys
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


@dataclass
class Pattern(Tree):
    pass

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
        case Pattern('HEAD_BEFORE', []):
            return int(word.HEAD) < int(word.ID) if word.ID.isdigit() else False
        case Pattern('HEAD_AFTER', []):
            return int(word.HEAD) > int(word.ID) if word.ID.isdigit() else False
        case Pattern('AND', patts):
            return all(match_wordline(p, word) for p in patts) 
        case Pattern('OR', patts):
            return any(match_wordline(p, word) for p in patts)
        case _:
            print('cannot match', str(patt))

            
def match_in_deptree(patt: Pattern, tree: DepTree):
    "finding all subtrees whose head matches a given pattern"
    if match_wordline(patt, tree.root):
        yield tree
    for subtree in tree.subtrees:
        print('ENTER', subtree.sentence())
        match_in_deptree(patt, subtree)
        


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
        for tree in match_in_deptree(patt, deptree):
            print('#', tree.sentence())
            print(tree)

        
if __name__ == '__main__':
    match sys.argv[1]:
        case 'match_wordlines':
            pattern = parse_pattern(sys.argv[2])
            print('#', pattern)
            match_wordlines(pattern, sys.stdin)
        case 'match_subtrees':
            pattern = parse_pattern(sys.argv[2])
            print('#', pattern)
            match_subtrees(pattern, sys.stdin)

