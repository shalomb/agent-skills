from pages import Page


def ids_of(html, prefix=""):
    return [i for i in Page(html).ids if i.startswith(prefix)]
