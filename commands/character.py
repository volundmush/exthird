from .command import Command
from world.menu import Menu


class Sheet(Command):
    key = "sheet"

    def func(self):
        target = self.caller
        if self.args:
            pass

        self.msg(target.story_sheet.render())


class Editor(Command):
    key = "editor"

    def func(self):
        target = self.caller
        if self.args:
            pass

        self.caller.ndb.target = target
        Menu(self.caller, "world.story.editor",
             startnode="template")
