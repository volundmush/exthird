from .exceptions import StoryDBException
from athanor.utils import partial_match
import typing


class Template:
    sub_types = []
    sub_name = "Caste"
    sheet_colors = {}
    start_advantages = {
        "Willpower": 5,
        "Essence": 1
    }

    def set_sub(self, entry: str):
        if not entry:
            raise StoryDBException(f"Must enter a Template name!")
        if not (found := partial_match(entry, self.sub_types)):
            raise StoryDBException(f"No {self.sub_name} matches {entry}.")
        self.handler.owner.db.template_subtype = found

    def initialize_attributes(self):
        c = self.handler.owner
        for a in _ATTRIBUTES:
            c.st_attributes.set(c, c, [a], value=1)

    def initialize_abilities(self):
        pass

    def initialize_advantages(self):
        c = self.handler.owner
        for k, v in self.start_advantages.items():
            c.st_advantages.set(c, c, [k], value=v)

    def initialize_template(self):
        if self.sub_types:
            self.handler.owner.db.template_subtype = self.sub_types[0]

    def initialize(self):
        self.initialize_template()
        self.initialize_attributes()
        self.initialize_abilities()
        self.initialize_advantages()

    def pool_personal_max(self):
        pass

    def pool_peripheral_max(self):
        pass

    def pool_overdrive_max(self):
        pass

    @classmethod
    def get_name(cls):
        return getattr(cls, "name", cls.__name__)

    def __str__(self):
        return getattr(self, "name", self.__class__.__name__)

    def __repr__(self):
        return '<Template: %s>' % str(self)

    def __init__(self, handler):
        self.handler = handler

    def initialize(self):
        pass


class TemplateHandler:

    def get_templates(self) -> dict[str, typing.Type[Template]]:
        return TEMPLATES

    def __init__(self, owner):
        self.owner = owner
        self.template = self.get_templates().get(self.owner.attributes.get(key="template", default="Mortal"), None)(self)

    def __str__(self):
        return f"<{self.__class__.__name__}: {str(self.template)}>"

    def set(self, template_name: str):
        templates = self.get_templates()
        if not template_name:
            raise StoryDBException(f"Must enter a Template name!")
        if not (found := partial_match(template_name, templates.keys())):
            raise StoryDBException(f"No Template matches {template_name}.")
        self.template = templates[found](self)
        self.template.initialize()
