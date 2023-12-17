# deptreepy
Python utilities for dependency trees, replicating some of gf-ud.
Designed to work on CoNNL-U data, such as in https://universaldependencies.org

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
   'match_subtrees <pattern>'
   'match_wordlines <pattern>'
   'change_wordlines <pattern>'
   'change_subtrees <pattern>'
   'statistics <field>*'
   'take_trees <int-from> <int-to>'
   'underscore_fields <field>*'
   'extract_sentences'
   'from_script <file>'

The commands without <file> arguments read CoNLL-U content from std-in,
for example, with the redirection <eng-ud.conllu.
These command can also be piped: for example,

   python3 deptreepy.py python3 'match_wordlines DEPREL nsubj | statistics POS' <FILE.conllu
   
gives statistics of POS (part of speech) of words that appear as subjects (DEPREL nsubj).
   
The single quotes around the commands where they are used above are
necessary to group the command into one command-line argument.

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
   TREE_ <pattern> <pattern>*
   SEQUENCE <pattern>*
   SEQUENCE_ <pattern>*
   HAS_SUBTREE <pattern>*
   IS_NONPROJECTIVE

The auxialiary concepts are:

   <strpatt>, a string with *,?,[seq] wildcards (like Unix filenames)
   <intpred>, one of =n, <n, >n, !n, giving a comparison to number n (which can be negative)

For example,

   match_subtrees TREE (AND) (HEAD_DISTANCE >0) (HEAD_DISTANCE <0)

matches trees that have both a head-final and a head-initial constituent: `(AND)` is true
of the head, because it poses no conditions on it, the first subtree comes before the head
(has a positive distance to it) and the second one after the head (negative distance).

   match_wordlines FEATS *=In*

matches indicative, infinitive, inessive, and other features starting with "In".

Quotes are not used around string patterns: if used, they can only match strings with
actual quotes.

In addition to search patterns, there are ones that change the trees, invoked by the
command change_wordlines:

  <field> <strpatt> <str>
  IF <pattern> <changepattern>
  AND <changepatterd>*

The command change_subtrees admits the following patterns:

  PRUNE <int>
  IF <pattern> <changepattern>

It traverses each tree recursively top-down: the next step is performed in the tree
resulting from the previoues step.


To visualize dependency trees, you can use the Haskell program utils/VisualizeUD.hs.
It can be used directly on CoNLL-U input,

  cat FILE.conllu | runghc utils/VisualizeUD.hs (latex | svg)

to produce either a LaTeX file or an HTML file with embedded SVG images.
To pipe into this visualization from deptreepy, use the deptrees2wordlines operation
at the end of the pipe, for instance,

  cat FILE.conllu |
  python3 deptreepy.py 'match_subtrees IS_NONPROJECTIVE | deptrees2wordlines' |
  runghc utils/VisualizeUD.hs svg

The svg option is recommended for non-latin alphabets such as Chinese, unless you have
suitable LaTeX packages available.
```
