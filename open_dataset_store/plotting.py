import json
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff

# Set global theme natively for the package
pio.templates.default = "plotly_dark"
pio.renderers.default = "colab+vscode+notebook_connected"

def set_plot_theme(theme_name: str = "plotly_dark"):
    """Easily switch the global Plotly theme for all visualisations."""
    pio.templates.default = theme_name


class DataPlotter:
    """
    Standalone plotting engine for easy chart generation.
    Pass a dataframe `data` to any method to generate a Plotly chart.
    """

    @staticmethod
    def _data_validate(data, message_dict):
        """
        Universal data validator for all plotter methods.
        Accepts None, empty strings, DataFrames, lists of records, or JSON strings.
        Returns a dict with 'status' ('success'/'error'), and either 'data' (list of records)
        or an updated 'message_dict' with the error reason.
        """
        # 1. Handle empty/None input
        if data is None or (isinstance(data, str) and not data):
            message_dict.update({'message': 'No data'})
            return {'status': 'error', 'message_dict': message_dict}

        # 2. Check if data is a DataFrame
        if isinstance(data, pd.DataFrame):
            if data.empty:
                message_dict.update({'message': 'No data'})
                return {'status': 'error', 'message_dict': message_dict}
            return {'status': 'success', 'data': data.to_dict(orient='records')}

        # 3. Check if data is a list (records)
        if isinstance(data, list):
            if not data:
                message_dict.update({'message': 'No data'})
                return {'status': 'error', 'message_dict': message_dict}
            return {'status': 'success', 'data': data}

        # 4. Handle JSON string input
        try:
            parsed_data = json.loads(data)
            # Support both {'records': [...]} structure OR raw list of records
            records = parsed_data.get('records') if isinstance(parsed_data, dict) else parsed_data

            if not records:
                message_dict.update({'message': 'No data'})
                return {'status': 'error', 'message_dict': message_dict}

            return {'status': 'success', 'data': records}

        except (json.JSONDecodeError, TypeError):
            message_dict.update({'message': 'Invalid data format'})
            return {'status': 'error', 'message_dict': message_dict}

    @staticmethod
    def _handle_return(fig_or_traces, layout_kwargs, as_trace, as_html=False):

        if isinstance(fig_or_traces, go.Figure):
            fig = fig_or_traces
            fig.update_layout(**layout_kwargs)
            if as_trace:
                return list(fig.data)
            if as_html:
                return fig.to_html(full_html=False, include_plotlyjs='cdn')
            return fig
        else:
            traces = fig_or_traces
            if not isinstance(traces, list) and not isinstance(traces, tuple):
                traces = [traces]
            if as_trace:
                return traces if len(traces) > 1 else traces[0]
            fig = go.Figure(data=traces)
            fig.update_layout(**layout_kwargs)
            if as_html:
                return fig.to_html(full_html=False, include_plotlyjs='cdn')
            return fig

    @classmethod
    def bar(cls, data, x_col, y_col, color_col=None, title="Bar Chart", config=None, as_trace=False, as_html=False):
        """
        Generates an interactive Plotly Bar Chart.
        
        Parameters
        ----------
        data : pandas.DataFrame or list
            The dataset containing the values to plot.
        x_col : str
            The column name for the X-axis (categories).
        y_col : str
            The column name for the Y-axis (values).
        color_col : str, optional
            The column name for color grouping.
        title : str, default "Bar Chart"
            The title of the generated chart.
        config : dict, optional
            Additional kwargs for plotly.express.bar.
        as_trace : bool, default False
            If True, returns raw Plotly traces instead of a Figure.
        as_html : bool, default False
            If True, returns a standalone HTML string for embedding.
            
        Returns
        -------
        plotly.graph_objects.Figure, list, or str
            The generated chart, trace, or HTML string.
        """
        config = config or {}
        c_col = color_col if color_col else (x_col if x_col in data.columns else None)
        fig = px.bar(data, x=x_col, y=y_col, color=c_col, **config)
        return cls._handle_return(fig, {"title": title}, as_trace, as_html)

    @classmethod
    def piechart(cls, data, names_col, values_col, color_col=None, title="Pie Chart", config=None, as_trace=False, as_html=False):
        """
        Generates an interactive Plotly Pie Chart.
        
        Parameters
        ----------
        data : pandas.DataFrame or list
            The dataset containing the values to plot.
        names_col : str
            The column name for the slice categories.
        values_col : str
            The column name for the slice values.
        color_col : str, optional
            The column name for color mapping.
        title : str, default "Pie Chart"
            The title of the generated chart.
        config : dict, optional
            Additional kwargs for plotly.express.pie.
        as_trace : bool, default False
            If True, returns raw Plotly traces instead of a Figure.
        as_html : bool, default False
            If True, returns a standalone HTML string for embedding.
            
        Returns
        -------
        plotly.graph_objects.Figure, list, or str
            The generated chart, trace, or HTML string.
        """
        config = config or {}
        c_col = color_col if color_col else names_col
        fig = px.pie(data, names=names_col, values=values_col, color=c_col, **config)
        return cls._handle_return(fig, {"title": title}, as_trace, as_html)

    @classmethod
    def histogram(cls, data, x_col, color_col=None, title="Histogram", config=None, as_trace=False, as_html=False):
        """
        Generates an interactive Plotly Histogram.
        
        Parameters
        ----------
        data : pandas.DataFrame or list
            The dataset containing the values to plot.
        x_col : str
            The column name for the X-axis values.
        color_col : str, optional
            The column name for color grouping/stacking.
        title : str, default "Histogram"
            The title of the generated chart.
        config : dict, optional
            Additional kwargs for plotly.express.histogram.
        as_trace : bool, default False
            If True, returns raw Plotly traces instead of a Figure.
        as_html : bool, default False
            If True, returns a standalone HTML string for embedding.
            
        Returns
        -------
        plotly.graph_objects.Figure, list, or str
            The generated chart, trace, or HTML string.
        """
        config = config or {}
        fig = px.histogram(data, x=x_col, color=color_col, **config)
        return cls._handle_return(fig, {"title": title}, as_trace, as_html)

    @classmethod
    def histogram_2d(cls, data, x_col, y_col, title="2D Histogram", config=None, as_trace=False, as_html=False):
        """
        Generates an interactive Plotly 2D Density Heatmap (Histogram).
        
        Parameters
        ----------
        data : pandas.DataFrame or list
            The dataset containing the values to plot.
        x_col : str
            The column name for the X-axis values.
        y_col : str
            The column name for the Y-axis values.
        title : str, default "2D Histogram"
            The title of the generated chart.
        config : dict, optional
            Additional kwargs for plotly.express.density_heatmap.
        as_trace : bool, default False
            If True, returns raw Plotly traces instead of a Figure.
        as_html : bool, default False
            If True, returns a standalone HTML string for embedding.
            
        Returns
        -------
        plotly.graph_objects.Figure, list, or str
            The generated chart, trace, or HTML string.
        """
        config = config or {}
        fig = px.density_heatmap(data, x=x_col, y=y_col, color_continuous_scale="Viridis", **config)
        return cls._handle_return(fig, {"title": title}, as_trace, as_html)

    @classmethod
    def scatter_3d(cls, data, x_col, y_col, z_col, color_col=None, title="3D Scatter Plot", config=None, as_trace=False, as_html=False):
        """
        Generates an interactive Plotly 3D Scatter Plot.
        
        Parameters
        ----------
        data : pandas.DataFrame or list
            The dataset containing the values to plot.
        x_col : str
            The column name for the X-axis values.
        y_col : str
            The column name for the Y-axis values.
        z_col : str
            The column name for the Z-axis values.
        color_col : str, optional
            The column name for color mapping.
        title : str, default "3D Scatter Plot"
            The title of the generated chart.
        config : dict, optional
            Additional kwargs for plotly.express.scatter_3d.
        as_trace : bool, default False
            If True, returns raw Plotly traces instead of a Figure.
        as_html : bool, default False
            If True, returns a standalone HTML string for embedding.
            
        Returns
        -------
        plotly.graph_objects.Figure, list, or str
            The generated chart, trace, or HTML string.
        """
        config = config or {}
        c_col = color_col if color_col else z_col
        fig = px.scatter_3d(data, x=x_col, y=y_col, z=z_col, color=c_col, **config)
        return cls._handle_return(fig, {"title": title}, as_trace, as_html)

    @classmethod
    def box_violin(cls, data, y_col, x_col=None, color_col=None, title="Violin & Box Plot", config=None, as_trace=False, as_html=False):
        """
        Generates an interactive Plotly Violin Plot with overlaid Box Plots.
        
        Parameters
        ----------
        data : pandas.DataFrame or list
            The dataset containing the values to plot.
        y_col : str
            The column name for the Y-axis (numerical distributions).
        x_col : str, optional
            The column name for the X-axis (categorical groupings).
        color_col : str, optional
            The column name for color mapping.
        title : str, default "Violin & Box Plot"
            The title of the generated chart.
        config : dict, optional
            Additional kwargs for plotly.express.violin.
        as_trace : bool, default False
            If True, returns raw Plotly traces instead of a Figure.
        as_html : bool, default False
            If True, returns a standalone HTML string for embedding.
            
        Returns
        -------
        plotly.graph_objects.Figure, list, or str
            The generated chart, trace, or HTML string.
        """
        config = config or {}
        c_col = color_col if color_col else x_col
        fig = px.violin(data, y=y_col, x=x_col, color=c_col, box=True, points="all", **config)
        return cls._handle_return(fig, {"title": title}, as_trace, as_html)

    @classmethod
    def scatter(cls, data, x_col, y_col, color_col=None, title="Scatter Plot", config=None, as_trace=False, as_html=False):
        """
        Generates an interactive Plotly 2D Scatter Plot.
        
        Parameters
        ----------
        data : pandas.DataFrame or list
            The dataset containing the values to plot.
        x_col : str
            The column name for the X-axis values.
        y_col : str
            The column name for the Y-axis values.
        color_col : str, optional
            The column name for color grouping.
        title : str, default "Scatter Plot"
            The title of the generated chart.
        config : dict, optional
            Additional kwargs for plotly.express.scatter.
        as_trace : bool, default False
            If True, returns raw Plotly traces instead of a Figure.
        as_html : bool, default False
            If True, returns a standalone HTML string for embedding.
            
        Returns
        -------
        plotly.graph_objects.Figure, list, or str
            The generated chart, trace, or HTML string.
        """
        config = config or {}
        fig = px.scatter(data, x=x_col, y=y_col, color=color_col, **config)
        return cls._handle_return(fig, {"title": title}, as_trace, as_html)

    @classmethod
    def bubble(cls, data, x_col, y_col, size_col, color_col=None, title="Bubble Chart", config=None, as_trace=False, as_html=False):
        """
        Generates an interactive Plotly Bubble Chart (Scatter plot with size).
        
        Parameters
        ----------
        data : pandas.DataFrame or list
            The dataset containing the values to plot.
        x_col : str
            The column name for the X-axis values.
        y_col : str
            The column name for the Y-axis values.
        size_col : str
            The column name determining the size of the bubbles.
        color_col : str, optional
            The column name for color mapping.
        title : str, default "Bubble Chart"
            The title of the generated chart.
        config : dict, optional
            Additional kwargs for plotly.express.scatter.
        as_trace : bool, default False
            If True, returns raw Plotly traces instead of a Figure.
        as_html : bool, default False
            If True, returns a standalone HTML string for embedding.
            
        Returns
        -------
        plotly.graph_objects.Figure, list, or str
            The generated chart, trace, or HTML string.
        """
        config = config or {}
        c_col = color_col if color_col else size_col
        fig = px.scatter(data, x=x_col, y=y_col, size=size_col, color=c_col, **config)
        return cls._handle_return(fig, {"title": title}, as_trace, as_html)

    @classmethod
    def heatmap(cls, z_matrix, x_labels, y_labels, title="Heatmap", config=None, as_trace=False, as_html=False):
        """
        Generates an interactive Plotly Heatmap from a 2D matrix.
        
        Parameters
        ----------
        z_matrix : array-like
            A 2D array representing heatmap intensities.
        x_labels : list
            Labels for the X-axis columns.
        y_labels : list
            Labels for the Y-axis rows.
        title : str, default "Heatmap"
            The title of the generated chart.
        config : dict, optional
            Additional kwargs for plotly.graph_objects.Heatmap.
        as_trace : bool, default False
            If True, returns raw Plotly traces instead of a Figure.
        as_html : bool, default False
            If True, returns a standalone HTML string for embedding.
            
        Returns
        -------
        plotly.graph_objects.Figure, list, or str
            The generated chart, trace, or HTML string.
        """
        config = config or {}
        trace = go.Heatmap(z=z_matrix, x=x_labels, y=y_labels, colorscale='Viridis', **config)
        return cls._handle_return(trace, {"title": title}, as_trace, as_html)

    @classmethod
    def distplot(cls, data, col_names, title="Distplot", config=None, as_trace=False, as_html=False):
        """
        Generates an interactive Plotly Distribution Plot (KDE + Histogram).
        
        Parameters
        ----------
        data : pandas.DataFrame
            The dataset containing the values to plot.
        col_names : list of str
            List of numerical column names to plot distributions for.
        title : str, default "Distplot"
            The title of the generated chart.
        config : dict, optional
            Additional kwargs for plotly.figure_factory.create_distplot.
        as_trace : bool, default False
            If True, returns raw Plotly traces instead of a Figure.
        as_html : bool, default False
            If True, returns a standalone HTML string for embedding.
            
        Returns
        -------
        plotly.graph_objects.Figure, list, or str
            The generated chart, trace, or HTML string.
        """
        config = config or {}
        hist_data = [data[col].dropna() for col in col_names]
        fig = ff.create_distplot(hist_data, col_names, **config)
        return cls._handle_return(fig, {"title": title}, as_trace, as_html)

PlottingMethods = DataPlotter
