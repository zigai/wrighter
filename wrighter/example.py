import sys

from options import BrowserLaunchOptions, ContextOptions, WrighterOptions
from wrighter import Wrigher

launch_options = BrowserLaunchOptions(headless=False,)
context_options = ContextOptions(permissions=['Geolocation'])
wrighter_options = WrighterOptions()

w = Wrigher(
    launch_options=launch_options,
    context_options=context_options,
    options=wrighter_options,
)
w.display_options()
w.stop()
