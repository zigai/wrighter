from playwright.sync_api import BrowserContext, Page
from stdl.str_u import FG, colored

from wrighter.plugin import EVENT_DUNDER, Plugin, context, page


class PluginManager:
    def __init__(self, wrighter) -> None:
        self.wrighter = wrighter
        self.plugins: list[Plugin] = []

    def add_plugin(self, plugin: Plugin, *, existing=True):
        """
        Adds a plugin to the current instance.

        Args:
            plugin (Plugin): The plugin to add.
            existing (bool, optional): If `True`, adds the plugin to all existing pages and contexts.
                Defaults to `True`.

        Returns:
            None
        """
        self.plugins.append(plugin)
        if existing:
            for page in self.wrighter.pages:
                plugin.add_to_page(page)
            for ctx in self.wrighter.contexts:
                plugin.add_to_context(ctx)

    def remove_plugin(self, plugin: Plugin, *, existing=True) -> None:
        """
        Remove a plugin from the current instance.

        Args:
            plugin (Plugin): The plugin to remove.
            existing (bool, optional): If `True`, remove the plugin from all existing pages and contexts.
                Defaults to `True`.

        Returns:
            None
        """
        self.plugins.remove(plugin)
        if existing:
            for page in self.wrighter.pages:
                plugin.remove_from_page(page)
            for ctx in self.wrighter.contexts:
                plugin.remove_from_context(ctx)

    def remove_all_plugins(self, *, existing=True) -> None:
        """
        Remove all plugin from the current instance.

        Args:
            existing (bool, optional): If `True`, alose remove all the plugin all from existing pages and contexts.
                Defaults to `True`.

        Returns:
            None
        """
        for plugin in self.plugins:
            self.remove_plugin(plugin, existing=existing)
        self.plugins.clear()

    def page_apply_plugins(self, page: Page):
        """Add all plugins to a page"""
        for plugin in self.plugins:
            plugin.add_to_page(page)

    def context_apply_plugins(self, ctx: BrowserContext):
        """Add all plugins to a context"""
        for plugin in self.plugins:
            plugin.add_to_context(ctx)

    def get_plugins_by_class(self, cls: Plugin) -> list[Plugin]:
        plugins = []
        for i in self.plugins:
            if isinstance(i, cls):  # type:ignore
                plugins.append(i)
        return plugins

    def print_plugins(self):
        print(colored("Plugins", FG.LIGHT_BLUE) + ":")
        for plugin in self.plugins:
            print(f"\t{plugin.description}")
        if not self.plugins:
            print("No plugins added.")


__all__ = ["PluginManager"]
