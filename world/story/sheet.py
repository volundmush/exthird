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
        if stat.is_supernal():
            out.append(Text(str(stat), style=colors.get("stat_supernal")))
        elif stat.is_caste():
            out.append(Text(str(stat), style=colors.get("stat_caste")))
        elif stat.is_favored():
            out.append(Text(str(stat), style=colors.get("stat_favored")))
        else:
            out.append(Text(str(stat), style=colors.get("stat_name")))
        return Text(" ").join(out)

    def render_stats(self, stats, colors: dict=None):
        if colors is None:
            colors = self.colors()
        render = Columns()
        for stat in stats:
            render.add_renderable(self.render_stat(stat, colors=colors))
        return render

    def get_specialties(self):
        out = list()
        for cat in ("story_attributes", "story_abilities"):
            out.extend(getattr(self.owner, cat).all_specialties())
        return out

    def render_specialties(self, specialties, colors: dict = None):
        if colors is None:
            colors = self.colors()
        render = Columns()
        for spec in specialties:
            render.add_renderable(Text(f"{spec.stat.name_2}/{spec.stat.name_3}"))
        return render

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

        left.append(self.text_header("Attributes"))
        left.append(self.render_stats(self.owner.story_attributes.all()))

        if (abil_stats := [abil for abil in self.owner.story_abilities.all() if abil.should_display()]):
            right.append(self.text_header("Abilities"))
            right.append(self.render_stats(abil_stats, colors=colors))

        if (craft_stats := [stat for stat in self.owner.story_crafts.all() if stat.should_display()]):
            right.append(self.text_header("Crafts"))
            right.append(self.render_stats(craft_stats, colors=colors))

        if (style_stats := [stat for stat in self.owner.story_styles.all() if stat.should_display()]):
            right.append(self.text_header("Styles"))
            right.append(self.render_stats(style_stats, colors=colors))

        if (specialties := self.get_specialties()):
            right.append(self.text_header("Specialties"))
            right.append(self.render_specialties(specialties, colors=colors))

        table.add_row(Group(*left), Group(*right))

        yield table

        if (charms_all := self.owner.story_charms.all_main()):
            yield self.render_powers(charms_all, "Charms", "Charms", colors=colors)

        if (spells_all := self.owner.story_spells.all_main()):
            yield self.render_powers(spells_all, "Spells", "Spells", colors=colors)

        if (evocations_all := self.owner.story_evocations.all_main()):
            evocations = Table(box=ASCII2, safe_box=True, padding=(0, 0, 0, 0), collapse_padding=True,
                      pad_edge=False, expand=True, show_header=False, border_style=colors.get("border"))
            evocations.add_column()
            evo = list()
            evo.append(self.text_header("Evocations"))
            evo.extend(self.render_powersection(evocations_all, "Evocations", "Evocations", colors=colors))
            evocations.add_row(Group(*evo))
            yield evocations

    def render_powersection(self, powers_dict, title: str, name: str, colors: dict = None):
        if colors is None:
            colors = self.colors()

        out = list()
        sub_categories = sorted(list(powers_dict.keys()))
        for sub in sub_categories:
            col = Columns()
            out.append(Text(sub, justify='center', style=colors.get("power_subcategory")))
            for power in sorted(powers_dict[sub], key=lambda x: str(x)):
                col.add_renderable(Text(str(power)))
            out.append(col)

        return out

    def render_powers(self, powers_dict, title: str, name: str, colors: dict = None):
        if colors is None:
            colors = self.colors()

        powers = Table(box=ASCII2, safe_box=True, padding=(0, 0, 0, 0), collapse_padding=True,
                      pad_edge=False, expand=True, show_header=False, border_style=colors.get("border"))

        powers.add_column(header=title)
        ch = list()
        categories = sorted(list(powers_dict.keys()))
        for category in categories:
            if ch:
                ch.append(NewLine())
            ch.append(self.text_header(f"{category} {name}"))
            ch.extend(self.render_powersection(powers_dict[category], title=title, name=name, colors=colors))
        powers.add_row(Group(*ch))

        return powers

    def text_header(self, name: str, colors: dict = None, color_name: str = "stat_header", border_name: str = "border"):
        if colors is None:
            colors = self.colors()
        sides = Text("==", style=colors.get(border_name))
        header = sides + Text(name, style=colors.get(color_name)) + sides
        header.justify = "center"
        return header