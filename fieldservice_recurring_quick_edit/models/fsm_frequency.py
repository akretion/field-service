# Copyright (C) 2019 - TODAY, mourad EL HADJ MIMOUNE, Akretion
# Copyright (C) 2021 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

import pytz
from dateutil.rrule import rrule

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.fieldservice_recurring.models.fsm_frequency import FREQUENCIES

INTERVAl_FREQUENCIES = [
    ("1", "First"),
    ("2", "Second"),
    ("3", "Third"),
    ("4", "Forth"),
    ("5", "Last"),
    ("6", "Each"),
]


class FSMFrequency(models.Model):
    _inherit = "fsm.frequency"

    fsm_recurring_id = fields.Many2one(
        # only if set.is_abstract is false
        # it's quite hard to have a good sql constraint
        "fsm.recurring",
        "Recurring order",
        ondelete="cascade",
        readonly=True,
    )
    # simple edit helper with planned_hour precision
    interval_frequency = fields.Selection(INTERVAl_FREQUENCIES, default="6", required=True)
    planned_hour = fields.Float("Planned Hours", help="Start at time")
    is_quick_editable = fields.Boolean(
        compute="_compute_is_quick_editable", default=False, store=True
    )
    day_quick_edit = fields.Selection(
        string="Day",
        selection=[
            ("mo", "Monday"),
            ("tu", "Tuesday"),
            ("we", "Wednesday"),
            ("th", "Thursday"),
            ("fr", "Friday"),
            ("sa", "Saturday"),
            ("su", "Sunday"),
        ],
        compute="_compute_day_quick_edit",
        default="mo",
    )
    week_day = fields.Char(compute="_calc_week_day")
    origin = fields.Char()

    def name_get(self):
        result = []
        for freq in self.sudo():
            name = freq.name
            if freq.fsm_recurring_id:
                name = "{} - {}".format(freq.fsm_recurring_id.name, freq.name)
            result.append((freq.id, name))
        return result

    @api.depends("mo", "tu", "we", "th", "fr", "sa", "su")
    def _compute_day_quick_edit(self):
        for rec in self:
            rec.day_quick_edit = False
            weekdays = ["mo", "tu", "we", "th", "fr", "sa", "su"]
            for field in weekdays:
                if rec[field]:
                    rec.day_quick_edit = field

    @api.depends(
        "interval_type",
        "use_byweekday",
        "use_bymonth",
        "use_bymonthday",
        "use_setpos",
        "set_pos",
        "mo",
        "tu",
        "we",
        "th",
        "fr",
        "sa",
        "su",
    )
    def _compute_is_quick_editable(self):
        for rec in self:
            if (
                # exclusions
                rec.interval_type != "monthly"
                or not rec.use_byweekday
                or rec.use_bymonth
                or rec.use_bymonthday
            ):
                rec.is_quick_editable = False
                continue

            # ensure only one day selected
            nb_dayselected = 0
            weekdays = ["mo", "tu", "we", "th", "fr", "sa", "su"]
            for field in weekdays:
                if rec[field]:
                    nb_dayselected += 1
            rec.is_quick_editable = nb_dayselected == 1

    @api.onchange("day_quick_edit")
    def onchange_day_quick_edit(self):
        if not self.day_quick_edit:
            self.name = ""
            return
        days = {
            "mo": _("Monday"),
            "tu": _("Tuesday"),
            "we": _("Wednesday"),
            "th": _("Thuesday"),
            "fr": _("Friday"),
            "sa": _("Saturday"),
            "su": _("Sunday"),
        }
        weekdays = ["mo", "tu", "we", "th", "fr", "sa", "su"]

        weekdays.remove(self.day_quick_edit)
        self[self.day_quick_edit] = True
        self.name = self.day_quick_edit and days[self.day_quick_edit] or ""
        self.use_byweekday = True
        for field in weekdays:
            print(field)
            self[field] = False

    def _calc_week_day(self):
        for rec in self:
            rec.week_day = ",".join(["%s" % d for d in (rec._byweekday() or [])])

    @api.onchange("interval_frequency")
    def _onchange_interval_frequency(self):
        """
        Checks use_bypose boolean
        """
        for freq in self:
            if not freq.interval_frequency or freq.interval_frequency == "6":
                freq.set_pos = 0
            elif freq.interval_frequency == "5":
                freq.set_pos = -1
            else:
                freq.set_pos = int(freq.interval_frequency)
            freq.use_setpos = True

    def _byhours(self):
        self.ensure_one()
        if not self.planned_hour:
            return 0, 0
        return self._split_time_to_hour_min(self.planned_hour)

    def _split_time_to_hour_min(self, time):
        if not time:
            time = 0.0
        duration_minute = time * 60
        hours, minutes = divmod(duration_minute, 60)
        return int(hours), int(minutes)

    def _get_rrule(self, dtstart=None, until=None, tz=None):
        self.ensure_one()
        if self.planned_hour is not False:
            # TODO move planned_hour to parent module
            hours, minutes = self._byhours()
            # localize dtstart and until to user timezone
            tz = pytz.timezone(
                tz or self._context.get("tz", None) or self.env.user.tz or "UTC"
            )

            freq = FREQUENCIES[self.interval_type]
            # to avoid bug off creation of rrule if somme args is none
            # we add anly defined args to kwargs
            kwargs = {}
            if self.interval:
                kwargs["interval"] = self.interval
            if dtstart:
                # Use naive datetime in current tz
                kwargs["dtstart"] = pytz.UTC.localize(dtstart).astimezone(tz)
            if until:
                # We force until in the starting timezone to avoid incoherent results
                kwargs["until"] = tz.normalize(
                    pytz.UTC.localize(until)
                    .astimezone(tz)
                    .replace(tzinfo=kwargs["dtstart"].tzinfo)
                )
            if self._byweekday():
                kwargs["byweekday"] = self._byweekday()
            if self._bymonth():
                kwargs["bymonth"] = self._bymonth()
            if self._bymonthday():
                kwargs["bymonthday"] = self._bymonthday()
            if self._bysetpos():
                kwargs["bysetpos"] = self._bysetpos()
            if hours or hours == 0:
                kwargs["byhour"] = hours
            if minutes or minutes == 0:
                kwargs["byminute"] = minutes
                kwargs["bysecond"] = 0

            return (
                # Replace original timezone with current date timezone
                # without changing the time and force it back to UTC,
                # this will keep the same final time even in case of
                # daylight saving time change
                #
                # for instance recurring weekly
                # from 2022-03-21 15:00:00+01:00 to 2022-04-11 15:30:00+02:00
                # will give:
                #
                # utc naive -> datetime timezone aware
                # 2022-03-21 14:00:00 -> 2022-03-21 15:00:00+01:00
                # 2022-03-28 13:00:00 -> 2022-03-28 15:00:00+02:00
                date.replace(tzinfo=tz.normalize(date).tzinfo)
                .astimezone(pytz.UTC)
                .replace(tzinfo=None)
                for date in rrule(freq, **kwargs)
            )
        return super(FSMFrequency, self)._get_rrule(dtstart=dtstart, until=until, tz=tz)
