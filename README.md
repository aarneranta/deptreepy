# deptreepy
Python utilities for dependency trees, replicating some of gf-ud

For a help message: do
```
  $ python3 deptreepy.py
```
You will see this:
```
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
```

