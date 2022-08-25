from .command import Command


class Sheet(Command):
    key = "sheet"

    def func(self):
        target = self.caller
        if self.args:
            pass

        self.msg(target.story_sheet.render())