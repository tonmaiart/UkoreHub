from core.theme import DEFAULT_THEME_NAME, build_stylesheet, get_theme, list_theme_names


def test_list_theme_names_includes_default():
    assert DEFAULT_THEME_NAME in list_theme_names()


def test_get_theme_known_name():
    theme = get_theme(DEFAULT_THEME_NAME)
    assert theme.background


def test_get_theme_unknown_name_falls_back_to_default():
    theme = get_theme("does-not-exist")
    assert theme == get_theme(DEFAULT_THEME_NAME)


def test_build_stylesheet_nonempty():
    theme = get_theme(DEFAULT_THEME_NAME)
    stylesheet = build_stylesheet(theme)
    assert isinstance(stylesheet, str)
    assert stylesheet.strip()
    assert theme.background in stylesheet
