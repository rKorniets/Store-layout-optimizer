
class StoreLayout {
    color_scheme = {
        "wall": "dark",
        "floor": "light",
        "rack": "primary",
        "door": "warning",
        "cashier": "danger",
    }
    constructor(config) {
        if (config.isEmpty) {
            this.generateEmptyConfig(config.rows, config.columns);
        }
        else {
            this.config = config;
        }

        this.maxFloorCount = this.max_floor_count();

        this.generateLayout();
        this.initializeControls();
    }

    mapColor(sell_type){
        return this.color_scheme[sell_type];
    }

    mapPathCountToHSVColor(path_count){
        path_count = parseInt(path_count);
        return 240 - Math.round(path_count/this.maxFloorCount * 240);
    }

    max_floor_count(){
        let max = 0;
        for (let n_row = 0; n_row < this.config.sells.length; n_row++) {
            const row = this.config.sells[n_row];
            for (let n_sell = 0; n_sell < row.length; n_sell++) {
                let sell = row[n_sell];
                if (sell.type === "floor" && sell.pathCount > max){
                    max = sell.pathCount;
                }
            }
        }
        return max;
    }

    mapType(color){
        for (const [key, value] of Object.entries(this.color_scheme)) {
            if (value === color) {
                return key;
            }
        }
    }

    generateLayout() {
        let layoutBody = $("#layout-body");
        $(layoutBody).empty();
        for (let n_row = 0; n_row < this.config.sells.length; n_row++) {
            const row = this.config.sells[n_row];
            $(layoutBody).append(`<tr n-row="n_row"></tr>`);
            for (let n_sell = 0; n_sell < row.length; n_sell++) {
                let sell = row[n_sell];
                let currentRow = $("#layout-table tr:last-child");
                let currentSellContainer = $(`<td class="clickable-sell border border-secondary table-${this.mapColor(sell.type)}" n-sell="${n_sell}" n-row="${n_row}" sell-type="${sell.type}"></td>`);
                let currentSell = $(`<div></div>`);
                let tooltip = $(`<div id="tooltip-${n_row}-${n_sell}" class="popper-tooltip">Sell type: ${sell.type}</div>`);
                if (sell.type === "floor") {
                    const path_count = sell.pathCount || 0;
                    const color = this.mapPathCountToHSVColor(path_count);
                    $(currentSellContainer).css("background-color", `hsl(${color}, 50%, 50%)`);
                    $(currentSellContainer).attr("data-bs-original-title", `${sell.type}\n${path_count}`);
                    tooltip.append("<br/>Path count: " + path_count);
                }
                if (sell.type === "rack") {
                    const items = sell.items || [];
                    $(currentSellContainer).attr("data-bs-original-title", `${sell.type}\n${sell.category}`);
                    tooltip.append("<br/>Category: " + sell.category);
                    tooltip.append("<br/>Items: " + items.length);
                    for (let i = 0; i < items.length; i++) {
                        tooltip.append(`<br/>&emsp;${items[i][1]}x ${items[i][0]}`);
                    }
                    tooltip.append(`<button class="btn btn-sm btn-outline-info" onclick="">Manage items</button>`);
                }
                if (sell.type === "door" || sell.type === "cashier") {
                    const path_count = sell.pathCount || 0;
                    $(currentSellContainer).attr("data-bs-original-title", `${sell.type}\n${path_count}`);
                    tooltip.append("<br/>Path count: " + path_count);
                }
                $(currentSellContainer).append(currentSell);
                $(currentRow).append(currentSellContainer);
                $(currentSellContainer).append(tooltip);
                this.initializeTooltip(tooltip);
            }
        }
    }

    generateEmptyConfig(rows = 17, cols = 32) {
        const sells = [];
        for (let i = 0; i < rows; i++) {
            const row = [];
            for (let j = 0; j < cols; j++) {
                if (i === 0 || i === rows - 1 || j === 0 || j === cols - 1)
                    row.push({ type: "wall", items : [], pathCount: 0 });
                else
                    row.push({ type: "floor", items : [], pathCount: 0 });
            }
            sells.push(row);
        }
        this.config = { sells };
    }

    updateConfig(config) {
        config.hideSaveLoadButtons = false;
        config.rackLevels = 4;
        config.items = [];
        for (let n_row = 0; n_row < config.sells.length; n_row++) {
            for (let n_sell = 0; n_sell < config.sells[0].length; n_sell++) {
                // add empty itmes array and path count
                if (!config.sells[n_row][n_sell].items) {
                    config.sells[n_row][n_sell].items = [];
                }
                if (!config.sells[n_row][n_sell].pathCount) {
                    config.sells[n_row][n_sell].pathCount = 0;
                }
            }
        }
        return config
    }

    getTypeCycle(sell_type, direction = 1) {
        const types = Object.keys(this.color_scheme);
        const index = types.indexOf(sell_type);
        return types[(index + direction + types.length) % types.length];
    }

    //reset the sell and set new empty attributes
    setNewSellType(sell, n_row, n_sell, new_type){
        this.config.sells[n_row][n_sell].type = new_type;
        this.config.sells[n_row][n_sell].pathCount = 0;
        this.config.sells[n_row][n_sell].items = [];
    }

    #cycleType(sell, direction = 1) {
        const sell_type = $(sell).attr("sell-type");
        const next_type = this.getTypeCycle(sell_type, direction);
        this.config.sells[$(sell).parent().index()][$(sell).index()].type = next_type;
        let n_row = $(sell).attr("n-row");
        let n_sell = $(sell).attr("n-sell");

        this.setNewSellType(sell, n_row, n_sell, next_type);
        this.generateLayout();
    }

    saveLayout(){
        //this.#updateConfig();
        const data = JSON.stringify(this.config);
        const blob = new Blob([data], {type: 'text/plain'});
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `layout ${this.config.sells.length}x${this.config.sells[0].length}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    loadLayout(){
        const self = this;
        const input = document.createElement('input');
        input.type = 'file';
        input.onchange = e => {
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.readAsText(file,'UTF-8');
            reader.onload = readerEvent => {
                const content = readerEvent.target.result;
                self.config = this.updateConfig(JSON.parse(content));
                $("#layout-body").empty();
                self.generateLayout();
            }
        }
        input.click();
    }

    initializeControls() {
        const self = this;

        $("#layout-table tbody")
            .on("click", "td", function (event) {
                console.debug("left click");
                if (!(event.target.tagName === "BUTTON")) self.#cycleType(this);
            })
            .on("contextmenu", "td", function () {
                console.debug("right click");
                if (!(event.target.tagName === "BUTTON")) self.#cycleType(this, -1);
                return false;
            });

        $("#btn-save-layout").click(function(){
            console.log("save layout");
            self.saveLayout();
        });

        $("#btn-load-layout").click(function(){
            console.log("load layout");
            self.loadLayout();
        });

        $('body').tooltip({
            selector: '[data-bs-toggle="tooltip"]',
            trigger: 'hover'
        })

        if (this.config.hideSaveLoadButtons){
            $("#save-load-buttons").hide();
        }
    }

    initializeTooltip(tooltip){
        const self = this;
        const popperInstance = Popper.createPopper($(tooltip).parent(), tooltip, {
            placement: 'bottom',
            modifiers: [
                {
                    name: 'offset',
                    options: {
                        offset: [0, 8],
                    },
                },
                {
                    name: 'flip',
                    options: {
                        fallbackPlacements: ['top', 'right', 'bottom', 'left'],
                    }
                }
            ],
        });
        $(tooltip).parent().on("mouseenter", function(){
            $(tooltip).show();
        });
        $(tooltip).parent().on("mouseleave", function(){
            $(tooltip).hide();
        });
    }
}

