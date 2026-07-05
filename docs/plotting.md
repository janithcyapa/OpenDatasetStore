# Plotting

`OpenDatasetStore` is designed to produce beautiful, presentation-ready visualizations by default. To achieve this, it tightly integrates with Plotly and natively configures a global dark mode theme for all visualizations generated within your environment.

## 1. Global Plotly Theme

Simply importing the plotting module from `OpenDatasetStore` will automatically set the global Plotly template to `"plotly_dark"`. This means any Plotly chart you generate using `plotly.express` or `plotly.graph_objects` will automatically inherit this dark theme without requiring explicit configuration in every plot.

If you wish to change the theme back to the default or another theme, you can use the built-in helper function:

```python
from open_dataset_store.plotting import set_plot_theme
import plotly.express as px

# By default, because open_dataset_store is loaded, this will be Dark Mode
fig = px.scatter(x=[1, 2, 3], y=[4, 5, 6])
fig.show()

# Switch back to the standard white theme
set_plot_theme('plotly')
```

## 2. The DataPlotter Utility

For quick, standardized charting, `OpenDatasetStore` provides a `DataPlotter` class (also aliased as `PlottingMethods`) which simplifies creating common interactive charts. 

These methods automatically handle data validation (accepting DataFrames, lists of dictionaries, or JSON strings) and provide options to return the raw trace or HTML strings for embedding.

```python
from open_dataset_store.plotting import DataPlotter

# Create a bar chart
fig = DataPlotter.bar(
    data=df, 
    x_col='category', 
    y_col='sales', 
    color_col='region', 
    title='Regional Sales'
)
fig.show()

# Other available chart types:
# DataPlotter.piechart(...)
# DataPlotter.histogram(...)
# DataPlotter.histogram_2d(...)
# DataPlotter.scatter_3d(...)
# DataPlotter.box_violin(...)
# DataPlotter.scatter(...)
# DataPlotter.bubble(...)
# DataPlotter.heatmap(...)
# DataPlotter.distplot(...)
```

All `DataPlotter` charts inherently respect the global `"plotly_dark"` theme configuration.
