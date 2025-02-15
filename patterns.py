from dataclasses import dataclass
from typing import Iterable, Callable
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


def combos(altlists):
    match altlists:
        case [[], _]:
            return []
        case [xs, *yss]:
            return [[x] + ys
                    for x in xs
                    for ys in combos([[y for y in ys if y != x] for ys in yss])]
        case _:
            return [[]]
        

def different_matches(mf, ps, xs):
    "each pattern in ps finds a different matching object in xs with match function mf"
    matchlist = [[x for x in xs if mf(p, x)] for p in ps]
    return combos(matchlist)
    
    
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
        case Pattern(field, ['IN', *forms]) if field in WORDLINE_FIELDS:
            wfield = word.as_dict()[field]
            return any(match_str(form, wfield) for form in forms)
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

        
def match_deptree(patt: Pattern, tree: DepTree) -> bool:
    "matching entire trees - either their root wordline or the whole tree"
    if match_wordline(patt, tree.root):
        return True
    else:
        match patt:
            case Pattern('LENGTH', [n]):
                return intpred(n, len(tree))
            case Pattern('DEPTH', [n]):
                return intpred(n, tree.depth())
            case Pattern('METADATA', [strpatt]):
                return match_str(strpatt, '\n'.join(tree.comments))
            case Pattern ('IS_NONPROJECTIVE', []):
                return nonprojective(tree)
            case Pattern('TREE', [pt, *patts]):
                return (len(patts) == len(sts := tree.subtrees) 
                         and match_deptree(pt, tree)
                         and all(match_deptree(*pt) for pt in zip(patts, sts)))
            case Pattern('TREE_', [pt, *patts]):
                return (match_deptree(pt, tree)
                        and different_matches(match_deptree, patts, tree.subtrees))
                # this could use the same subtree twice:            
                #       and all(any(match_deptree(p, t) for t in tree.subtrees) for p in patts))
            case Pattern('SEQUENCE', patts):
                return (len(patts) == len(sts := tree.wordlines()) 
                         and all(match_wordline(*pt) for pt in zip(patts, sts)))
            case Pattern('SUBSEQUENCE', patts):
                for i in range(len(tree.wordlines())-len(patts)):
                     sts = tree.wordlines()[i:i+len(patts)]
                     if all(match_wordline(*pt) for pt in zip(patts, sts)):
                         return True
                return False
            case Pattern('SEQUENCE_', patts):
                return (all(any(match_wordline(p, t) for t in tree.wordlines()) for p in patts))
            case Pattern('HAS_SUBTREE', patts):
                return any(all(match_deptree(p, st) for p in patts) for st in tree.subtrees) 
            case Pattern('HAS_NO_SUBTREE', patts):
                return not any(all(match_deptree(p, st) for p in patts) for st in tree.subtrees) 
            case Pattern('CONTAINS_SUBTREE', patts):  ## to revisit
                return (all(match_deptree(p, tree) for p in patts) or
                        any(match_deptree(patt, st) for st in tree.subtrees)) 
            case Pattern('AND', patts):  # must be defined again for tree patterns
                return all(match_deptree(p, tree) for p in patts) 
            case Pattern('OR', patts):
                return any(match_deptree(p, tree) for p in patts)
            case Pattern('NOT', [patt]):
                return not (match_deptree(patt, tree))
            case _:
                return False

            
def matches_of_deptree(patt: Pattern, tree: DepTree) -> list[DepTree]:
    "return singleton list if the tree matches, otherwise empty"
    if match_deptree(patt, tree):
        return [tree]
    else:
        return []


def matches_in_deptree(patt: Pattern, tree: DepTree) -> list[DepTree]:
    "finding all subtrees that match a pattern"
    ts = []
    if match_deptree(patt, tree):
        ts.append(tree)
    for subtree in tree.subtrees:
        ts.extend(matches_in_deptree(patt, subtree))
    return ts


def match_found_in_deptree(patt: Pattern, tree: DepTree) -> list[DepTree]:
    "return a tree that has at least one matching subtree"

    def found_in(tr):
        if match_deptree(patt, tr):
            tr.add_misc('MATCH')
        for subtree in tr.subtrees:
            found_in(subtree)

    found_in(tree)

    if any(w.MISC.endswith('+MATCH') for w in tree.wordlines()):
        ### +MATCH should not appear in MISC for another reason
        return [tree]
    else:
        return []


def len_segment_pattern(patt: Pattern) -> int:
    match patt:
        case Pattern('SEGMENT', patts):
            return sum(len_segment_pattern(pt) for pt in patts)
        case Pattern('REPEAT', [n, patt]):
            return int(n) * len_segment_pattern(patt)
        case _:
            return 1


def match_segment(patt: Pattern, trees: list[DepTree]) -> bool:
    "matching a contiguous segment of trees"
    if len_segment_pattern(patt) == len(trees):
        match patt:
            case Pattern('SEGMENT', patts):
                for pt in patts:
                    if match_segment(pt, trees[:len_segment_pattern(pt)]):
                        trees = trees[len_segment_pattern(pt):]
                        continue
                    else:
                        return False
                return True
            case Pattern('REPEAT', [n, pt]):
                for _ in range(int(n)):
                    if match_segment(pt, trees[:len_segment_pattern(pt)]):
                        trees = trees[len_segment_pattern(pt):]
                        continue
                    else:
                        return False
                return True
            case _:
                return match_deptree(patt, trees[0])  # must be a singleton

        
def matches_in_tree_stream(patt: Pattern,
                           trees: Iterable[DepTree]) -> Iterable[list[DepTree]]:
    match patt:
        case Pattern('REPEAT', [n, pt]) if n[0] == '>':
            segment = []
            while trees:
                try:
                    tr = next(trees)
                except StopIteration:
                    break
                while match_deptree(pt, tr):
                    segment.append(tr)
                    if trees:
                        try:
                            tr = next(trees)
                        except StopIteration:
                            break
                    else:
                        break
                if len(segment) > int(n[1:]):
                    yield segment
                segment = []
            
        case _:
            lenp = len_segment_pattern(patt)
            try:
                segment = [next(trees) for _ in range(lenp)]
            except StopIteration:
                return
            while trees:
                if match_segment(patt, segment):
                    yield segment
                    try:
                        segment = [next(trees) for _ in range(lenp)]  # segments may not overlap
                    except StopIteration:
                        return
                else:
                    try:
                        segment.pop(0)
                        segment.append(next(trees))
                    except StopIteration:
                        return
        

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
        case Pattern('AND', patts):  # cumulative changes in the order of patts
            for patt in patts:
                word = change_wordline(patt, word)
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
        case Pattern('FILTER_SUBTREES', [condpatt]):  ## to revisit
            tree.subtrees = [t for t in tree.subtrees if match_deptree(condpatt, t)]
            return tree
        case Pattern('AND', patts):
            for patt in patts:
                tree = change_deptree(patt, tree)
            return tree
        case _:
            tree.root = change_wordline(patt, tree.root)
            return tree

    
def changes_in_deptree(patt: Pattern, tree: DepTree) -> DepTree:
    "performing change in a tree and recursively in all changed subtrees"
    tree = change_deptree(patt, tree)
    tree.subtrees = [change_deptree(patt, t) for t in tree.subtrees]
    return tree


def find_paths_in_tree(patts: list[Pattern], tree: DepTree) -> list[DepTree]:
    "find paths in a tree"
    if patts[1:]:
        return [DepTree(tree.root, [stp], [])
                    for st in tree.subtrees
                    for stp in find_paths_in_tree(patts[1:], st)
                    if match_wordline(patts[0], tree.root)
                    ]
    elif patts:
        return [DepTree(tree.root, [], [])
                    for _ in [0]
                    if match_wordline(patts[0], tree.root)]
    else:
        return []

    
def find_paths_in_subtrees(patts: list[Pattern], tree: DepTree) -> list[DepTree]:
    "find parts in tree and all subtrees"
    paths = find_paths_in_tree(patts, tree)
    for st in tree.subtrees:
        for p in find_paths_in_subtrees(patts, st):
            paths.append(p)
    return paths

    
def find_partial_local_trees(patts: list[Pattern], tree: DepTree) -> list[DepTree]:
    "find partial trees in a tree"
    if patts and match_wordline(patts[0], tree.root):
        xss = different_matches(match_deptree, patts[1:], tree.subtrees)
        
        return [DepTree(tree.root, [DepTree(x.root, [], []) for x in xs], []) for xs in xss]
    else:
        return []

    
def find_partial_local_subtrees(patts: list[Pattern], tree: DepTree) -> list[DepTree]:
    subtrs = find_partial_local_trees(patts, tree)
    for st in tree.subtrees:
        for p in find_partial_local_subtrees(patts, st):
            subtrs.append(p)
    return subtrs

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


        
