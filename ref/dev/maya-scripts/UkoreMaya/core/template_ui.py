def get_menu_stylesheet():
    print("Getting menu stylesheet from CruxMaya.template_ui")
    stylesheet = """
                    QMenu {
                        background-color: #2b2b2b;
                        border: 1px solid #444;
                        padding: 2px;
                        border-radius: 2px;
                        font-size: 11px;
                        color: #ddd;
                    }
                    QMenu::item {
                        padding: 2px 4px 2px 4px;
                        margin: 1px 0;
                    }
                    QMenu::item:selected {            /* hover / selected */
                        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                        stop:0 #3a3a3a, stop:1 #996600);
                        color: white;
                    }
                    QMenu::separator {
                        height: 1px;
                        background: #444;
                        margin: 6px 0;
                    }
                    QMenu::icon {
                        padding-left: 2px;
                        padding-right: 2px;
                    }
                    QMenu::item:disabled {
                color: #555;                      /* สีตัวอักษรจางลง */
                background-color: transparent;    /* ไม่มี hover สี */}"""
    return stylesheet


def get_table_view_browser_stylesheet():
    stylesheet = """
    QTableView {
        background-color:qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(12, 12, 12, 255), stop:1 rgba(36, 36, 36, 255));
        color: #f0f0f0;
        border: 2px solid #444;
        gridline-color: #555;
        outline: none;
        alternate-background-color: #333;
        padding:0px;
    }

    QHeaderView::section {
        background-color: #3a3a3a;
        color: #ffffff;
        font-weight: bold;
        border: 1px solid #555;
    }

    QTableView::item {
        padding: 0px;
    }

    QTableView::item:selected {
    background-color:qlineargradient(spread:pad, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(243, 159, 89, 255), stop:1 rgba(197, 131, 76, 255));
    color:black;
        font: bold;
    }
    """

    return stylesheet
