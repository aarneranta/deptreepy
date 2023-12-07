import sys
from trees import *
from patterns import *

help_message = (
"""
usage:

   python3 deptreepy.py <command> <arg>*

The command-arg combinations are

   cosine_similarity <file> <file> <field>*
   match_subtrees '<pattern>'
   match_wordlines '<pattern>'
   statistics <field>*
   underscore_fields <field>*

The command without <file> arguments read CoNLL-U content from std-in,
for example, with the redirection <eng-ud.conllu.

The <field> arguments correspond to CoNLL-U word line fields from left to right:

    ID FORM LEMMA POS XPOS FEATS HEAD DEPREL DEPS MISC

The following patterns match both wordlines and trees, depending on the command:

   <field>  <strpatt>
   HEAD_DISTANCE <inpred>
   AND <pattern>*
   OR  <pattern>*
   NOT <pattern>*

When applied to trees, they match the root node of the tree.
The following patterns match only trees:

   LENGTH <intpred>
   DEPTH <intpred>
   TREE <pattern> <pattern>*
   HAS_SUBTREE <pattern>*

The auxialiary concepts are:

   <strpatt>, a string with *,?,[seq] wildcards (like Unix filenames)
   <intpred>, one of =n, <n, >n, !n, giving a comparison to number n (which can be negative)

For example,

   match_subtrees 'TREE (AND) (HEAD_DISTANCE >0) (HEAD_DISTANCE <0)'

matches trees that have both a head-final and a head-initial constituent: `(AND)` is true
of the head, because it poses no conditions on it, the first subtree comes before the head
(has a positive distance to it) and the second one after the head (negative distance).

   match_wordlines 'FEATS *=In*'

matches indicative, infinitive, inessive, and other features starting with "In".

Quotes are not used outside string patterns: if used, they can only match strings with
actual quotes.
"""
)

if __name__ == '__main__':
    if not sys.argv[1:]:
        print(help_message)
    else:
      match sys.argv[1]:
        case 'match_wordlines':
            pattern = parse_pattern(sys.argv[2])
            print('#', pattern)
            match_wordlines(pattern, sys.stdin)
        case 'match_subtrees':
            pattern = parse_pattern(sys.argv[2])
            print('#', pattern)
            match_subtrees(pattern, sys.stdin)
        case 'statistics':
            fields = sys.argv[2:]
            wordlines = read_wordlines(sys.stdin)
            for item in sorted_statistics(statistics(fields, wordlines)):
                print(item)
        case 'cosine_similarity':
            file1, file2 = sys.argv[-2:]
            fields = sys.argv[2:-2]
            with open(file1) as lines1:
                stats1 = statistics(fields, read_wordlines(lines1))
            with open(file2) as lines2:
                stats2 = statistics(fields, read_wordlines(lines2))
            print(cosine_similarity(stats1, stats2))
        case 'underscore_fields':
            fields = sys.argv[2:]
            wordlines = read_wordlines(sys.stdin)
            for line in wordlines:
                ldict = line.as_dict()
                for field in fields:
                    ldict[field] = '_'
                print(WordLine(**ldict))
        case 'help' | _:
            print(help_message)
            

