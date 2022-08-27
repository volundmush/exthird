from evennia.utils.evmenu import EvMenu, _HELP_NO_OPTION_MATCH, EvMenuGotoAbortMessage, _HELP_FULL, _HELP_NO_OPTIONS_NO_QUIT
from evennia.utils.evmenu import EvMenuError, _HELP_NO_QUIT, _HELP_NO_OPTIONS
from evennia.utils.ansi import strip_ansi
from evennia.utils.utils import make_iter, is_iter
import re
from rich.table import Table
from rich.box import ASCII2
from rich.console import Group
from rich.text import Text
from rich.markup import escape


class Menu(EvMenu):
    re_cmd = re.compile(
        r"^(?P<cmd>(?P<prefix>[\|@\+\$-]+)?(?P<cmdname>\w+))(?P<fullargs>(?P<switches>(?:\/\w+){0,})(?: +(?P<args>(?P<lsargs>[^=]+)?(?:=(?P<rsargs>.+)?)?)?)?)?",
        flags=re.IGNORECASE | re.MULTILINE)

    def display_helptext(self):
        print(type(self.nodetext))
        super().display_nodetext()

    def options_formatter(self, optionlist):
        if not optionlist:
            return ""
        table = Table(safe_box=True, box=ASCII2)
        table.add_column("CMD", style="bold")
        table.add_column("Desc")
        table.add_column("Syntax")
        for op in optionlist:
            if (choices := op.get("choices", list())):
                choices = f"CHOICES: {', '.join(choices)}"
                syntax = escape("\n".join([op.get("syntax", ""), choices]))
            else:
                syntax = escape(op.get("syntax", ""))
            table.add_row(escape(op.get("key", "")), escape(op.get("desc", "")), syntax)
        if self.auto_quit:
            table.add_row("quit", "Exit Menu", "quit")
        return table

    def nodetext_formatter(self, nodetext):
        if hasattr(nodetext, "__rich_console__"):
            return nodetext
        return Text(escape(nodetext))

    def node_formatter(self, nodetext, optionstext):
        return Group(nodetext, optionstext)

    def parse_input(self, raw_string):
        """
        Parses the incoming string from the menu user.
        Args:
            raw_string (str): The incoming, unmodified string
                from the user.
        Notes:
            This method is expected to parse input and use the result
            to relay execution to the relevant methods of the menu. It
            should also report errors directly to the user.
        """
        stripped = strip_ansi(raw_string.strip())
        if not (match := self.re_cmd.match(stripped)):
            self.msg(_HELP_NO_OPTION_MATCH)
            return
        cmd = match.group("cmd").lower()
        self.caller.ndb._menu_match = match

        try:
            if self.options and cmd in self.options:
                # this will take precedence over the default commands
                # below
                goto, goto_kwargs, execfunc, exec_kwargs = self.options[cmd]
                self.run_exec_then_goto(execfunc, goto, raw_string, exec_kwargs, goto_kwargs)
            elif self.auto_look and cmd in ("look", "l"):
                self.display_nodetext()
            elif self.auto_help and cmd in ("help", "h"):
                self.display_helptext()
            elif self.auto_quit and cmd in ("quit", "q", "exit"):
                self.close_menu()
            elif self.debug_mode and cmd.startswith("menudebug"):
                self.print_debug_info(cmd[9:].strip())
            elif self.default:
                goto, goto_kwargs, execfunc, exec_kwargs = self.default
                self.run_exec_then_goto(execfunc, goto, raw_string, exec_kwargs, goto_kwargs)
            else:
                self.msg(_HELP_NO_OPTION_MATCH)
        except EvMenuGotoAbortMessage as err:
            # custom interrupt from inside a goto callable - print the message and
            # stay on the current node.
            self.msg(str(err))

    def goto(self, nodename, raw_string, **kwargs):
        """
        Run a node by name, optionally dynamically generating that name first.
        Args:
            nodename (str or callable): Name of node or a callable
                to be called as `function(caller, raw_string, **kwargs)` or
                `function(caller, **kwargs)` to return the actual goto string or
                a ("nodename", kwargs) tuple.
            raw_string (str): The raw default string entered on the
                previous node (only used if the node accepts it as an
                argument)
            **kwargs: Extra arguments to goto callables.
        """

        if callable(nodename):
            # run the "goto" callable, if possible
            inp_nodename = nodename
            nodename = self._safe_call(nodename, raw_string, **kwargs)
            if isinstance(nodename, (tuple, list)):
                if not len(nodename) > 1 or not isinstance(nodename[1], dict):
                    raise EvMenuError(
                        "{}: goto callable must return str or (str, dict)".format(inp_nodename)
                    )
                nodename, kwargs = nodename[:2]
            if not nodename:
                # no nodename return. Re-run current node
                nodename = self.nodename
        try:
            # execute the found node, make use of the returns.
            nodetext, options = self._execute_node(nodename, raw_string, **kwargs)
        except EvMenuError:
            return

        if self._persistent:
            self.caller.attributes.add(
                "_menutree_saved_startnode", (nodename, (raw_string, kwargs))
            )

        # validation of the node return values
        helptext = ""
        if is_iter(nodetext):
            if len(nodetext) > 1:
                nodetext, helptext = nodetext[:2]
            else:
                nodetext = nodetext[0]
        nodetext = "" if nodetext is None else nodetext
        options = [options] if isinstance(options, dict) else options

        # this will be displayed in the given order
        display_options = []
        # this is used for lookup
        self.options = {}
        self.default = None
        if options:
            for inum, dic in enumerate(options):
                # fix up the option dicts
                keys = make_iter(dic.get("key"))
                desc = dic.get("desc", dic.get("text", None))
                if "_default" in keys:
                    keys = [key for key in keys if key != "_default"]
                    goto, goto_kwargs, execute, exec_kwargs = self.extract_goto_exec(nodename, dic)
                    self.default = (goto, goto_kwargs, execute, exec_kwargs)
                else:
                    # use the key (only) if set, otherwise use the running number
                    keys = list(make_iter(dic.get("key", str(inum + 1).strip())))
                    goto, goto_kwargs, execute, exec_kwargs = self.extract_goto_exec(nodename, dic)
                if keys:
                    display_options.append((keys[0], desc))
                    for key in keys:
                        if goto or execute:
                            self.options[strip_ansi(key).strip().lower()] = (
                                goto,
                                goto_kwargs,
                                execute,
                                exec_kwargs,
                            )

        self.nodetext = self._format_node(nodetext, options)
        self.node_kwargs = kwargs
        self.nodename = nodename

        # handle the helptext
        if helptext:
            self.helptext = self.helptext_formatter(helptext)
        elif options:
            self.helptext = _HELP_FULL if self.auto_quit else _HELP_NO_QUIT
        else:
            self.helptext = _HELP_NO_OPTIONS if self.auto_quit else _HELP_NO_OPTIONS_NO_QUIT

        self.display_nodetext()
        if not options:
            self.close_menu()