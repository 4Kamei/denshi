import builtins
from itertools import count


SELECTED = 'denshiSelected'

more_builtins = {'__file__', '__path__', '__cached__'}
builtins = set(vars(builtins)) | more_builtins


class Node:
    """A node in the source code.

    """
    # Highlight ID for selected nodes
    MARK_ID = 31400
    # Highlight ID counter (chosen arbitrarily)
    id_counter = count(314001)

    __slots__ = ['id', 'name', 'lineno', 'col', 'end', 'env',
                 'symname', 'symbol', 'hl_group', 'target', '_tup']

    def __init__(self, name, lineno, col, end, hl_group):
        self.id = next(Node.id_counter)
        self.name = name
        self.lineno = lineno
        self.col = col
        # Encode the name to get the byte length, not the number of chars
        self.end = end
        self.hl_group = hl_group
        self.update_tup()

    def update_tup(self):
        """Update tuple used for comparing with other nodes."""
        self._tup = (self.lineno, self.col, self.hl_group, self.name)

    def __lt__(self, other):
        return self._tup < other._tup # pylint: disable=protected-access

    def __eq__(self, other):
        return self._tup == other._tup # pylint: disable=protected-access

    def __hash__(self):
        # Currently only required for tests
        return hash(self._tup)

    def __repr__(self):
        return '<%s %s %s (%s, %s) %d>' % (
            self.name,
            self.hl_group,  
            self.lineno,
            self.col,
            self.end,
            self.id,
        )

    def base_table(self):
        return None

    @property
    def pos(self):
        return (self.lineno, self.col)
