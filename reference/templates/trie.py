"""Trie. Invariant: a path from the root spells a prefix; node.end marks a full word.
Bug: returning True on prefix match when the problem asks for a full word."""

class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node['$'] = True

    def search(self, word):
        node = self._walk(word)
        return node is not None and '$' in node

    def starts_with(self, prefix):
        return self._walk(prefix) is not None

    def _walk(self, s):
        node = self.root
        for ch in s:
            if ch not in node:
                return None
            node = node[ch]
        return node

# Wildcard '.' (Design Add and Search Words): DFS over all children at that position.
# Word Search II: DFS the grid while walking the trie; prune when the trie has no child.
