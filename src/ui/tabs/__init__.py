"""Main dashboard tabs."""
from src.ui.tabs.data import render_data_tab
from src.ui.tabs.status import render_status_tab
from src.ui.tabs.growth import render_rda_flow_tab
from src.ui.tabs.forecast import render_forecast_tab

__all__ = [
    "render_data_tab",
    "render_status_tab",
    "render_rda_flow_tab",
    "render_forecast_tab",
]
