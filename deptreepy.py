import sys
from trees import *
from patterns import *

def print_help_message():
    with open('README.md') as file:
        for line in file.readlines()[9:-1]:
            print(line, end='')


if __name__ == '__main__':
    if not sys.argv[1:]:
        print_help_message()
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
            for item in sorted_statistics(wordline_statistics(fields, wordlines)):
                print(item)
        case 'change_wordlines':
            pattern = parse_pattern(sys.argv[2])
            print('#', pattern)
            change_wordlines(pattern, sys.stdin)
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
            print_help_message()
            

