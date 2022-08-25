from django.db import models


class CharacterTemplate(models.Model):
    id = models.OneToOneField('objects.ObjectDB', null=False, related_name='storyteller', primary_key=True,
                              on_delete=models.CASCADE)
    name = models.CharField(max_length=15, null=False, blank=False, default='Mortal')
    sub_name = models.CharField(max_length=15, null=True, blank=False)
    extra = models.JSONField(null=True, default=None)


class Stat(models.Model):
    category = models.CharField(max_length=20, null=False, blank=False)
    name = models.CharField(max_length=80, null=False, blank=False)
    creator = models.ForeignKey('objects.ObjectDB', null=True, related_name='+', on_delete=models.SET_NULL)

    class Meta:
        unique_together = (("category", "name"),)


class CharacterStat(models.Model):
    stat = models.ForeignKey(Stat, on_delete=models.PROTECT, related_name="users")
    owner = models.ForeignKey("objects.ObjectDB", on_delete=models.CASCADE, related_name="db_stats")
    value = models.PositiveIntegerField(default=0, null=False)
    extra = models.JSONField(null=True, default=None)
    flag_1 = models.IntegerField(default=0)
    flag_2 = models.IntegerField(default=0)

    def __str__(self):
        return str(self.stat)

    class Meta:
        unique_together = (("stat", "owner"),)


class CharacterSpecialty(models.Model):
    stat = models.ForeignKey(CharacterStat, on_delete=models.CASCADE, related_name='specialties')
    name = models.CharField(max_length=80, null=False, blank=False)
    value = models.PositiveIntegerField(default=1, null=False)

    def __str__(self):
        return f"{str(self.stat)}/{self.name}"

    class Meta:
        unique_together = (("stat", "name",),)


class Power(models.Model):
    root = models.CharField(max_length=30, null=False, blank=False)
    category = models.CharField(max_length=30, null=False, blank=False)
    subcategory = models.CharField(max_length=40, null=False, blank=False)
    name = models.CharField(max_length=80, null=False, blank=False)
    creator = models.ForeignKey('objects.ObjectDB', null=True, related_name='+', on_delete=models.SET_NULL)

    class Meta:
        unique_together = (("root", "category", "subcategory", "name"),)

    def __str__(self):
        return self.name


class CharacterPower(models.Model):
    power = models.ForeignKey(Power, on_delete=models.PROTECT, related_name="users")
    owner = models.ForeignKey("objects.ObjectDB", on_delete=models.CASCADE, related_name="db_powers")
    value = models.PositiveIntegerField(default=1, null=False)
    extra = models.JSONField(null=True, default=None)
    flag_1 = models.IntegerField(default=0)
    flag_2 = models.IntegerField(default=0)

    def __str__(self):
        return str(self.power)

    class Meta:
        unique_together = (("power", "owner"),)


class Merit(models.Model):
    category = models.CharField(max_length=100, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    creator = models.ForeignKey('objects.ObjectDB', null=True, related_name='+', on_delete=models.SET_NULL)

    class Meta:
        unique_together = (("category", "name"),)

    def __str__(self):
        return self.name


class CharacterMerit(models.Model):
    owner = models.ForeignKey("objects.ObjectDB", on_delete=models.CASCADE, related_name='db_merits')
    merit = models.ForeignKey(Merit, on_delete=models.PROTECT, related_name="users")
    value = models.PositiveIntegerField(default=1, null=False)
    extra = models.JSONField(null=True, default=None)
    flag_1 = models.IntegerField(default=0)
    flag_2 = models.IntegerField(default=0)

    class Meta:
        unique_together = (("owner", "merit"),)

    def __str__(self):
        return str(self.merit)
