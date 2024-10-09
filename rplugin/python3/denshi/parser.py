from collections import deque
from collections.abc import Iterable
from functools import singledispatch
from .util import debug_time, logger, lines_to_code, code_to_lines
from .node import Node

import subprocess
import tempfile
from threading import Lock

class UnparsableError(Exception):

    def __init__(self, error):
        super().__init__()
        self.error = error


class Parser:
    """The parser parses Python code and generates source code nodes. For every
    run of `parse()` on changed source code, it returns the nodes that have
    been added and removed.
    """
    def __init__(self, config_location, binary_location, exclude=None, fix_syntax=True):
        self._excluded = exclude or []
        self._fix_syntax = fix_syntax
        self._locations = {}
        self._nodes = []
        self.lines = []
        # Incremented after every parse call
        self.tick = 0
        self.parse_lock = Lock()
    
        self.binary_location = binary_location
        self.config_location = config_location
        # Holds the error of the current and previous run, so the buffer
        # handler knows if error signs need to be updated.
        self.syntax_errors = deque([None, None], maxlen=2)
        self.same_nodes = singledispatch(self.same_nodes)
        self.same_nodes.register(Iterable, self._same_nodes_cursor)

    @debug_time
    def parse(self, *args, **kwargs):
        """Wrapper for `_parse()`.

        Raises UnparsableError() if an unrecoverable error occurred.
        """
        try:
            return self._parse(*args, **kwargs)
        except (SyntaxError, RecursionError) as e:
            logger.debug('parsing error: %s', e)
            raise UnparsableError(e)
        finally:
            self.tick += 1

    @debug_time
    def _filter_excluded(self, nodes):
        return [n for n in nodes if n.hl_group not in self._excluded]

    def _parse(self, code, force=False):
        
        with self.parse_lock:
            """Parse code and return tuple (`add`, `remove`) of added and removed
            nodes since last run. With `force`, all highlights are refreshed, even
            those that didn't change.
            """
            self._locations.clear()
            old_lines = self.lines
            new_lines = code_to_lines(code)
            minor_change, change_lineno = self._minor_change(old_lines, new_lines)
            old_nodes = self._nodes
            

            new_nodes = self._make_nodes(code, new_lines, change_lineno)
            # Detecting minor changes keeps us from updating a lot of highlights
            # while the user is only editing a single line.
            if minor_change and not force:
                add, rem, keep = self._diff(old_nodes, new_nodes)
                self._nodes = keep + add
            else:
                add, rem = new_nodes, old_nodes
                self._nodes = add

        # Only assign new lines when nodes have been updated accordingly
        self.lines = new_lines
        logger.debug('[%d] nodes: +%d,  -%d', self.tick, len(add), len(rem))
        return (self._filter_excluded(add), self._filter_excluded(rem))

    def _make_nodes(self, code, lines=None, change_lineno=None):
        """Return nodes in code.

        Runs AST visitor on code and produces nodes. We're passing both code
        *and* lines around to avoid lots of conversions.
        """
        if lines is None:
            lines = code_to_lines(code)

        #FIXME tempfile used - I'm sure there's a more 
        #      vim way of getting a file from the underlying buffer 
        with tempfile.NamedTemporaryFile(mode="w+t") as tmp_file:
            tmp_file.write(code)
            tmp_file.flush()
            
            #tmp_file.seek(0)
            #assert tmp_file.readlines() != [], "File should be readable"
            args = [self.binary_location, 
                    str(tmp_file.name),
                    self.config_location,
                    "parse"]
    
   
            popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            popen.wait()
            output = popen.stdout.read()       
            err_out = popen.stderr.read()

        assert err_out == "", f"Parser return errors: Parser output: \n{err_out}  \nCalled with: {str(args)}"
  
        nodes = []
        for line in output.split("\n"):
            s = line.split(" ")
            if len(s) == 1: #Because s = ['']
                continue
            group = s[0]
            line = int(s[1])
            start = int(s[2])
            end = int(s[3])
            name = s[4]
            nodes.append(Node(name, line, start, end, group))

        return nodes

    @staticmethod
    def _minor_change(old_lines, new_lines):
        """Determine whether a minor change between old and new lines occurred.
        Return (`minor_change`, `change_lineno`) where `minor_change` is True
        when at most one change occurred and `change_lineno` is the line number
        of the change.

        A minor change is a change in a single line while the total number of
        lines doesn't change.
        """
        if len(old_lines) != len(new_lines):
            # A different number of lines doesn't count as minor change
            return (False, None)
        old_iter = iter(old_lines)
        new_iter = iter(new_lines)
        diff_lineno = None
        lineno = 0
        try:
            while True:
                old_lines = next(old_iter)
                new_lines = next(new_iter)
                if old_lines != new_lines:
                    if diff_lineno is not None:
                        # More than one change must have happened
                        return (False, None)
                    diff_lineno = lineno
                lineno += 1
        except StopIteration:
            # We iterated through all lines with at most one change
            return (True, diff_lineno)

    @staticmethod
    @debug_time
    def _diff(old_nodes, new_nodes):
        """Return difference between iterables of nodes old_nodes and new_nodes
        as three lists of nodes to add, remove and keep.
        """
        add_iter = iter(sorted(new_nodes))
        rem_iter = iter(sorted(old_nodes))
        add_nodes = []
        rem_nodes = []
        keep_nodes = []
        try:
            add = rem = None
            while True:
                if add == rem:
                    if add is not None:
                        keep_nodes.append(add)
                        # A new node needs to adopt the highlight ID of
                        # corresponding currently highlighted node
                        add.id = rem.id
                    add = rem = None
                    add = next(add_iter)
                    rem = next(rem_iter)
                elif add < rem:
                    add_nodes.append(add)
                    add = None
                    add = next(add_iter)
                elif rem < add:
                    rem_nodes.append(rem)
                    rem = None
                    rem = next(rem_iter)
        except StopIteration:
            if add is not None:
                add_nodes.append(add)
            if rem is not None:
                rem_nodes.append(rem)
            add_nodes += list(add_iter)
            rem_nodes += list(rem_iter)
        return add_nodes, rem_nodes, keep_nodes

    @debug_time
    def node_at(self, cursor):
        """Return node at cursor position."""
        lineno, col = cursor
        for node in self._nodes:
            if node.lineno == lineno and node.col <= col < node.end:
                return node
        return None

    # pylint: disable=method-hidden
    def same_nodes(self, cur_node, mark_original=True, use_target=True):
        """Return nodes with the same scope as cur_node.

        The same scope is to be understood as all nodes with the same base
        symtable. In some cases this can be ambiguous.
        """
        if use_target:
            target = cur_node.hl_group
            if target is not None:
                cur_node = target
        cur_name = cur_node.name
        base_table = cur_node.base_table()
        for node in self._nodes:
            if node.name != cur_name:
                continue
            if not mark_original and node is cur_node:
                continue
            if node.base_table() == base_table:
                yield node

    def _same_nodes_cursor(self, cursor, mark_original=True, use_target=True):
        """Return nodes with the same scope as node at the cursor position."""
        cur_node = self.node_at(cursor)
        if cur_node is None:
            return []
        return self.same_nodes(cur_node, mark_original, use_target)

    def locations_by_hl_group(self, group):
        """Return locations of all nodes whose highlight group is `group`."""
        return [n.pos for n in self._nodes if n.hl_group == group]

