odoo.define("fieldservice_crew.calendar_model", function (require) {
    "use strict";

    const CalendarModel = require("web.CalendarModel");
    const adjustFilters = (filter) => () => {
        const allFilter = filter.filters.find((f) => f.value === "all");
        const activeFilters = filter.filters.filter(
            (f) => f.value !== "all" && f.active === true
        );

        // If it's the first load, we want to show all the records
        if (filter._hasLoaded === undefined) {
            filter.all = allFilter.active = true;
            activeFilters.forEach((f) => {
                f.active = false;
            });
            filter._hasLoaded = true;
        }

        // If there's no active filter, we activate all
        else if (activeFilters.length === 0) {
            filter.all = allFilter.active = true;
        } else if (allFilter.active) {
            // If there are active filters, we deactivate all
            filter.all = allFilter.active = false;
        }
    };

    CalendarModel.include({
        _loadFilter: function (filter) {
            if (!filter.write_model) {
                return Promise.resolve();
            }
            return new Promise((resolve) => {
                this._super(filter).then(adjustFilters(filter)).then(resolve);
            });
        },
    });
});
