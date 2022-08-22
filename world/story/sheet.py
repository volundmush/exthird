from rich.console import group, Group
from rich.padding import Padding
from django.conf import settings
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.table import Table
from rich.layout import Layout
from rich.console import NewLine
from rich.box import ASCII2, ASCII


class SheetHandler:
    base_colors = {}

    def __init__(self, owner):
        self.owner = owner

    def colors(self):
        colors = dict(self.base_colors)
        colors.update(self.owner.story_template.template.sheet_colors)
        return colors

    def render_stat(self, stat, colors=None):
        if colors is None:
            colors = self.colors()
        out = list()
        out.append(Text(f"{stat.calculated_value():>2}", style=colors.get("stat_value")))
        out.append(Text(str(stat), style=colors.get("stat_name")))
        if stat.is_favored():
            out.append("(F)")
        return Text(" ").join(out)

    @group()
    def render(self, width=None):
        if width is None:
            width = 78
        colors = self.colors()

        table = Table(box=ASCII2, safe_box=True, padding=(0, 0, 0, 0), collapse_padding=True,
                      pad_edge=False, expand=True, show_header=False, border_style=colors.get("border"))

        table.add_column(header="Attributes", ratio=1)
        table.add_column(header="Abilities", ratio=4)

        left = list()
        right = list()

        should_attributes = False

        attributes = Columns()
        for stat in self.owner.story_attributes.all():
            if stat.should_display():
                should_attributes = True
                attributes.add_renderable(self.render_stat(stat, colors=colors))

        if should_attributes:
            left.append(Text("Attributes", style=colors.get("stat_header"), justify="center"))
            left.append(attributes)


        should_abilities = False
        abilities = Columns()
        for stat in self.owner.story_abilities.all():
            if stat.should_display():
                should_abilities = True
                abilities.add_renderable(self.render_stat(stat, colors=colors))

        if should_abilities:
            right.append(Text("Abilities", style=colors.get("stat_header"), justify="center"))
            right.append(abilities)


        should_crafts = False
        crafts = Columns()
        for stat in self.owner.story_crafts.all():
            if stat.should_display():
                should_crafts = True
                crafts.add_renderable(self.render_stat(stat, colors=colors))

        if should_crafts:
            right.append(NewLine())
            right.append(Text("Crafts", style=colors.get("stat_header"), justify="center"))
            right.append(crafts)

        should_styles = False
        styles = Columns()
        for stat in self.owner.story_styles.all():
            if stat.should_display():
                should_styles = True
                styles.add_renderable(self.render_stat(stat, colors=colors))

        if should_styles:
            right.append(NewLine())
            right.append(Text("Styles", style=colors.get("stat_header"), justify="center"))
            right.append(styles)

        table.add_row(Group(*left), Group(*right))

        yield table

        # yield Panel(layout, box=ASCII2, padding=(0,0,0,0), expand=False)
