import pandas as pd
import numpy as np
try:
    from IPython.display import display
except ImportError:
    display = print

class DataInspectorMixin:
    """
    Mixin for data cleaning, preprocessing, and modification.
    """
    def get_df_summary(self, df, detailed=False):
        """
        Generates and displays a structural summary of the loaded dataset.
        
        Parameters
        ----------
        detailed : bool, default False
            If True, calculates and appends statistical metrics (Min, Max, Mean, Std Dev) 
            for numerical columns, and frequency metrics (Unique Values, Most Frequent) 
            for categorical columns.
            
        Returns
        -------
        pandas.DataFrame or None
            A DataFrame containing the summary metadata. Returns None if no data is loaded.
        """
        if df is None:
            print("Error: No data loaded.")
            return None
        
        summary_data = []
        for col in df.columns:
            col_data = df[col]
            summary_dict = {
                'Column Name': col,
                'Data Type': str(col_data.dtype),
                'Total Records': len(col_data),
                'Missing Values': col_data.isnull().sum()
            }
            
            if detailed:
                if pd.api.types.is_numeric_dtype(col_data):
                    summary_dict['Min'] = col_data.min()
                    summary_dict['Max'] = col_data.max()
                    summary_dict['Mean'] = col_data.mean()
                    summary_dict['Std Dev'] = col_data.std()
                    summary_dict['Unique Values'] = np.nan
                    summary_dict['Most Frequent'] = np.nan
                else:
                    summary_dict['Min'] = np.nan
                    summary_dict['Max'] = np.nan
                    summary_dict['Mean'] = np.nan
                    summary_dict['Std Dev'] = np.nan
                    summary_dict['Unique Values'] = col_data.nunique()
                    summary_dict['Most Frequent'] = col_data.mode()[0] if not col_data.mode().empty else np.nan
            
            summary_data.append(summary_dict)
        
        self.summary_df = pd.DataFrame(summary_data)
        print(f"--- Data Summary {'(Detailed)' if detailed else ''} ---")
        display(self.summary_df)
        return self.summary_df

    def get_missing_data(self, df, axis='rows'):
        """
        Isolates and displays portions of the dataset containing missing (NaN) values.
        
        Parameters
        ----------
        axis : {'rows', 'columns'}, default 'rows'
            The dimension to filter on.
            - 'rows': Returns only rows that contain at least one NaN value.
            - 'columns': Returns the entire dataset but exclusively for columns containing NaNs.
            
        Returns
        -------
        pandas.DataFrame or None
            The filtered DataFrame containing the missing data.
        """
        if df is None: return print("No data loaded.")
        if axis == 'rows':
            missing_mask = df.isnull().any(axis=1)
            missing_data = df[missing_mask]
            if missing_data.empty: print("✨ No missing data found in rows!")
            else:
                print(f"🔍 Found {len(missing_data)} rows with missing values.")
                display(missing_data.head())
            return missing_data
        elif axis == 'columns':
            missing_mask = df.isnull().any(axis=0)
            missing_data = df.loc[:, missing_mask]
            if missing_data.empty: print("✨ No missing data found in columns!")
            else:
                print(f"🔍 Found {missing_data.shape[1]} columns with missing values.")
                display(missing_data.head())
            return missing_data
        else:
            print("Invalid axis. Choose 'rows' or 'columns'.")

    def extract_data(self, df, columns=None, column_type=None, index_column=None, row_indices=None, row_ranges=None):
        """
        Extracts a customized subset of the working dataset based on complex slicing parameters.
        The extracted subset is stored in `self.selected_df` and displayed.
        
        Parameters
        ----------
        columns : list of str, optional
            A specific list of column names to extract.
        column_type : {'numerical', 'categorical'}, optional
            Automatically filters columns by their data type. Ignored if `columns` is provided.
        index_column : str, optional
            A column name to pin to the front of the extracted dataset (useful for IDs/labels).
        row_indices : list of int, optional
            A list of specific row index numbers to extract.
        row_ranges : list of tuple, optional
            A list of tuples defining (start, end) inclusive row index bounds to extract.
            
        Returns
        -------
        pandas.DataFrame or None
            The newly extracted DataFrame subset (`self.selected_df`).
        """
        if df is None: return print("No data loaded.")
        extracted = df.copy()
        
        selected_rows = []
        if row_indices: selected_rows.extend(row_indices)
        if row_ranges:
            for r in row_ranges: selected_rows.extend(list(range(r[0], r[1] + 1)))
        if selected_rows:
            selected_rows = list(set(selected_rows))
            extracted = extracted.loc[extracted.index.intersection(selected_rows)]
            
        selected_cols = []
        if columns: selected_cols = columns
        elif column_type == 'numerical': selected_cols = extracted.select_dtypes(include=[np.number]).columns.tolist()
        elif column_type == 'categorical': selected_cols = extracted.select_dtypes(exclude=[np.number]).columns.tolist()
        else: selected_cols = extracted.columns.tolist()
            
        if index_column and index_column in df.columns:
            if index_column in selected_cols: selected_cols.remove(index_column)
            selected_cols.insert(0, index_column)
            
        selected_cols = [c for c in selected_cols if c in extracted.columns]
        extracted = extracted[selected_cols]
        
        print(f"✅ Data extracted into new dataframe: {extracted.shape[0]} rows, {extracted.shape[1]} columns.")
        display(extracted.head())
        return extracted

    def delete_rows(self, df, indices, summary=False):
        """
        Permanently deletes specific rows from the working dataset (`df`) by their index.
        The index is automatically reset after deletion.
        
        Parameters
        ----------
        indices : list of int
            A list of row indices to remove.
        summary : bool, default False
            If True, automatically triggers `get_summary()` after deletion.
            
        Returns
        -------
        None
            Modifies `df` in-place.
        """
        if df is None: return print("No data loaded.")
        existing_indices = [i for i in indices if i in df.index]
        df = df.drop(index=existing_indices).reset_index(drop=True)
        print(f"🗑️ Deleted {len(existing_indices)} rows. New count: {len(df)}")
        if summary: self.get_df_summary(df)
        return df

    def delete_columns(self, df, columns, summary=False):
        """
        Permanently deletes specific columns from the working dataset (`df`).
        
        Parameters
        ----------
        columns : list of str
            A list of column names to remove.
        summary : bool, default False
            If True, automatically triggers `get_summary()` after deletion.
            
        Returns
        -------
        None
            Modifies `df` in-place.
        """
        if df is None: return print("No data loaded.")
        existing_cols = [c for c in columns if c in df.columns]
        df = df.drop(columns=existing_cols)
        print(f"🗑️ Deleted {len(existing_cols)} columns. Remaining count: {len(df.columns)}")
        if summary: self.get_df_summary(df)
        return df

    # --- DATA MODIFIERS ---

    def modify_missing_values(self, df, columns=None, strategy='median', fill_value=None):
        """
        Imputes missing values (NaNs) in specified columns using statistical estimators or constants.
        
        Parameters
        ----------
        columns : list of str or str, optional
            A list of column names to impute. If None, targets all columns containing NaNs.
        strategy : {'mean', 'median', 'mode', 'constant'}, default 'median'
            The mathematical strategy used to derive the fill value.
            - 'mean': Uses the arithmetic average (numeric columns only).
            - 'median': Uses the exact middle value (numeric columns only).
            - 'mode': Uses the most frequently occurring value (all types).
            - 'constant': Uses the user-defined `fill_value`.
        fill_value : any, optional
            The static value to inject when using the 'constant' strategy.
            
        Returns
        -------
        None
            Modifies `df` in-place.
        """
        if df is None: return print("No data loaded.")
        target_cols = columns if columns else df.columns[df.isnull().any()].tolist()
        if isinstance(target_cols, str): target_cols = [target_cols]
        
        for col in target_cols:
            if col not in df.columns: continue
            
            is_numeric = pd.api.types.is_numeric_dtype(df[col])
            if strategy == 'mean' and is_numeric:
                df[col] = df[col].fillna(df[col].mean())
            elif strategy == 'median' and is_numeric:
                df[col] = df[col].fillna(df[col].median())
            elif strategy == 'mode':
                df[col] = df[col].fillna(df[col].mode()[0])
            elif strategy == 'constant':
                df[col] = df[col].fillna(fill_value)
                
        print(f"🛠️ Missing values imputed using '{strategy}' strategy for: {target_cols}")
        return df

    def modify_duplicates(self, df):
        """
        Scans the entire dataset for completely identical rows and permanently removes them,
        retaining only the first occurrence. Automatically resets the row index.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
            Modifies `df` in-place and prints the number of dropped rows.
        """
        if df is None: return print("No data loaded.")
        initial_count = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        dropped = initial_count - len(df)
        print(f"✨ Removed {dropped} duplicate rows. New row count: {len(df)}")
        return df

    def modify_outliers(self, df, columns=None, find_and_delete=False):
        """
        Detects anomalies in numerical data using the Interquartile Range (IQR) bounding logic.
        Values falling below Q1 - 1.5*IQR or above Q3 + 1.5*IQR are flagged.
        
        Parameters
        ----------
        columns : list of str or str, optional
            Specific numerical columns to check. If None, sweeps all numerical columns automatically.
        find_and_delete : bool, default False
            If True, automatically deletes any rows containing at least one flagged outlier. 
            If False, only prints a diagnostic report detailing the outlier frequencies.
            
        Returns
        -------
        None
            Modifies `df` in-place only if `find_and_delete` is True.
        """
        if df is None: return print("No data loaded.")
        target_cols = columns if columns else df.select_dtypes(include=[np.number]).columns.tolist()
        if isinstance(target_cols, str): target_cols = [target_cols]
        all_outliers = set()

        for col in target_cols:
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))]
            all_outliers.update(outliers.index.tolist())
            if len(outliers) > 0:
                print(f"🚨 {col}: Found {len(outliers)} outliers.")

        if all_outliers:
            if find_and_delete:
                df = df.drop(index=list(all_outliers)).reset_index(drop=True)
                print(f"🗑️ Deleted {len(all_outliers)} outlier rows total.")
            else:
                print("Outliers identified but not deleted. Pass find_and_delete=True to remove them.")
        else:
            print("✅ No outliers found.")
        return df

    def modify_normalize_data(self, df, columns, method, replace=True):
        """
        Applies mathematical transformations to data arrays for standardization or machine learning prep.
        Features strict type-checking to prevent processing categorical logic on numeric floats.
        
        Parameters
        ----------
        columns : list of str or str
            The column names to transform.
        method : {'minmax', 'standard', 'robust', 'uniform', 'ordinal', 'onehot', 'minmax_ordinal'}
            The scaler algorithm to apply:
            - Numeric bounds: 'minmax', 'standard' (Z-score), 'robust' (IQR-scaled).
            - Categorical mappings: 'uniform' (0-1 scaled codes), 'ordinal' (0-N integers), 
              'onehot' (explodes into binary matrix), 'minmax_ordinal' (minmax scaled ordinal).
        replace : bool, default True
            If True, overrides the original column with the newly scaled data. 
            If False, appends the transformed data as new distinct columns suffixed with `_{method}`.
            
        Returns
        -------
        None
            Modifies `df` in-place.
        """
        if df is None: return print("No data loaded.")
        if isinstance(columns, str): columns = [columns]
        
        numeric_methods = ['minmax', 'standard', 'robust']
        categorical_methods = ['uniform', 'ordinal', 'onehot', 'minmax_ordinal']
        method = method.lower().strip()
        
        from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler, OrdinalEncoder, OneHotEncoder
        
        for col in columns:
            if col not in df.columns:
                print(f"⚠️ Column '{col}' not found. Skipping.")
                continue
                
            is_numeric = pd.api.types.is_numeric_dtype(df[col])
            
            if is_numeric and method not in numeric_methods:
                raise ValueError(f"Method '{method}' is not suitable for numeric column '{col}'. Use one of {numeric_methods}.")
            if not is_numeric and method not in categorical_methods:
                raise ValueError(f"Method '{method}' is not suitable for categorical column '{col}'. Use one of {categorical_methods}.")
                
            col_data = df[[col]].copy()
            
            # Fill NaNs temporarily for fitting
            if col_data.isnull().any().any():
                if is_numeric:
                    col_data = col_data.fillna(col_data.median())
                else:
                    col_data = col_data.fillna("Missing")
            
            new_data = {}
            if method == 'minmax':
                new_data[col] = MinMaxScaler().fit_transform(col_data)[:, 0]
            elif method == 'standard':
                new_data[col] = StandardScaler().fit_transform(col_data)[:, 0]
            elif method == 'robust':
                new_data[col] = RobustScaler().fit_transform(col_data)[:, 0]
            elif method == 'uniform':
                codes = df[col].astype('category').cat.codes
                max_code = codes.max()
                new_data[col] = (codes / max_code) if max_code > 0 else 0.0
            elif method == 'ordinal':
                new_data[col] = OrdinalEncoder().fit_transform(col_data)[:, 0]
            elif method == 'onehot':
                encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
                encoded = encoder.fit_transform(col_data)
                for i, name in enumerate(encoder.get_feature_names_out([col])):
                    new_data[name] = encoded[:, i]
            elif method == 'minmax_ordinal':
                encoded = OrdinalEncoder().fit_transform(col_data)
                new_data[col] = MinMaxScaler().fit_transform(encoded)[:, 0]
                
            if replace:
                df = df.drop(columns=[col])
                for k, v in new_data.items():
                    df[k] = v
            else:
                for k, v in new_data.items():
                    new_name = f"{k}_{method}" if method != 'onehot' else k
                    df[new_name] = v
        return df

    def summary_plot(self, df, columns=None,
                     numeric_plots=None,
                     categorical_plots=None,
                     separate_plots=False, subplot_cols=3):
        """
        Creates a comprehensive multi-row Plotly visualization dashboard.

        Parameters
        ----------
        columns : list[str] or None
            Specific column names to visualize. If None, uses all columns in df.
        numeric_plots : list[str] or None
            Plot types for numerical columns. Supported: 'violin', 'scatter',
            'histogram', 'distplot'. Defaults to ['violin', 'scatter', 'distplot'].
        categorical_plots : list[str] or None
            Plot types for categorical columns. Supported: 'pie', 'histogram', 'bar'.
            Defaults to ['pie', 'histogram'].
        separate_plots : bool
            If True, each column gets its own dedicated row of subplots.
            If False (default), all numerical columns share one set of plots and
            all categorical columns share another.
        subplot_cols : int
            Number of subplot columns per row (default 3).
        """
        if df is None:
            print("⚠️ No data loaded.")
            return

        # --- Defaults ---
        if numeric_plots is None:
            numeric_plots = ['violin', 'scatter', 'distplot']
        if categorical_plots is None:
            categorical_plots = ['pie', 'histogram']

        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import plotly.express as px
        import plotly.figure_factory as ff
        import math

        # --- Resolve & validate columns ---
        all_cols = df.columns.tolist()
        if columns is not None:
            invalid = [c for c in columns if c not in all_cols]
            if invalid:
                print(f"⚠️ Columns not found in data and skipped: {invalid}")
            cols = [c for c in columns if c in all_cols]
        else:
            cols = all_cols

        if not cols:
            print("⚠️ No valid columns to plot.")
            return

        colors = px.colors.qualitative.Vivid + px.colors.qualitative.Plotly

        # --- Helper: add a single plot trace to fig ---
        def _add_numeric_trace(fig, pt, col_name, row, col_idx, color):
            """Add a single numeric plot type to the figure."""
            data_series = df[col_name].dropna()
            if data_series.empty:
                return
            if pt == 'violin':
                fig.add_trace(
                    go.Violin(x=data_series, name=col_name, box_visible=True,
                              meanline_visible=True, points='all',
                              marker_color=color, showlegend=False),
                    row=row, col=col_idx)
            elif pt == 'scatter':
                fig.add_trace(
                    go.Scatter(x=data_series.index, y=data_series, mode='markers',
                               name=col_name, marker=dict(color=color, size=5,
                               opacity=0.7), showlegend=False),
                    row=row, col=col_idx)
            elif pt == 'histogram':
                fig.add_trace(
                    go.Histogram(x=data_series, name=col_name,
                                 marker_color=color, opacity=0.8,
                                 showlegend=False),
                    row=row, col=col_idx)
            elif pt == 'distplot':
                try:
                    if len(data_series) > 1:
                        fig_dist = ff.create_distplot(
                            [data_series.values], [col_name], colors=[color],
                            show_rug=False)
                        for trace in fig_dist['data']:
                            trace.xaxis = None
                            trace.yaxis = None
                            trace.showlegend = False
                            fig.add_trace(trace, row=row, col=col_idx)
                except Exception:
                    pass

        def _add_categorical_trace(fig, pt, col_name, row, col_idx, color):
            """Add a single categorical plot type to the figure."""
            val_counts = df[col_name].value_counts().reset_index()
            val_counts.columns = [col_name, 'count']
            if val_counts.empty:
                return
            if pt == 'pie':
                fig.add_trace(
                    go.Pie(labels=val_counts[col_name], values=val_counts['count'],
                           name=col_name, textinfo='percent+label', hole=0.3,
                           marker=dict(colors=px.colors.qualitative.Pastel)),
                    row=row, col=col_idx)
            elif pt in ('bar', 'histogram'):
                cat_colors = px.colors.qualitative.Set3[:len(val_counts)]
                fig.add_trace(
                    go.Bar(x=val_counts[col_name].astype(str),
                           y=val_counts['count'], name=col_name,
                           marker_color=cat_colors if len(cat_colors) == len(val_counts)
                           else color, showlegend=False),
                    row=row, col=col_idx)

        # =========================================================
        #  MODE 1: SEPARATE — each column gets its own row of plots
        # =========================================================
        if separate_plots:
            max_plot_cols = 0
            row_specs = []
            row_titles = []

            for col in cols:
                is_num = pd.api.types.is_numeric_dtype(df[col])
                plot_types = numeric_plots if is_num else categorical_plots
                max_plot_cols = max(max_plot_cols, len(plot_types))

                current_spec = []
                for pt in plot_types:
                    current_spec.append(
                        {"type": "domain"} if pt == 'pie' else {"type": "xy"})
                row_specs.append(current_spec)

                for pt in plot_types:
                    row_titles.append(f"{col} — {pt.capitalize()}")

            # Pad short rows with None so all rows have the same number of cols
            for spec_row in row_specs:
                while len(spec_row) < max_plot_cols:
                    spec_row.append(None)
                    row_titles.append("")

            if max_plot_cols == 0:
                print("⚠️ No plots to draw.")
                return

            fig = make_subplots(
                rows=len(cols), cols=max_plot_cols, specs=row_specs,
                subplot_titles=row_titles,
                vertical_spacing=max(0.02, 0.15 / len(cols)),
                horizontal_spacing=0.05)

            for i, col in enumerate(cols):
                row = i + 1
                is_num = pd.api.types.is_numeric_dtype(df[col])
                plot_types = numeric_plots if is_num else categorical_plots
                base_color = colors[i % len(colors)]

                for j, pt in enumerate(plot_types):
                    if is_num:
                        _add_numeric_trace(fig, pt, col, row, j + 1, base_color)
                    else:
                        _add_categorical_trace(fig, pt, col, row, j + 1, base_color)

            fig.update_layout(
                
                height=max(400, 300 * len(cols)),
                showlegend=False,
                title_text="Summary Dashboard — Separate View",
                title_x=0.5,
                bargap=0.15,
                # paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter, sans-serif"))
            fig.show()

        # =========================================================
        #  MODE 2: COMBINED — all numericals together, categoricals together
        # =========================================================
        else:
            num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
            cat_cols = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]

            plot_cells = []
            if num_cols:
                for pt in numeric_plots:
                    plot_cells.append({
                        "type": "xy", "name": pt, "group": "num",
                        "title": f"Numerical — {pt.capitalize()}"})
            if cat_cols:
                for pt in categorical_plots:
                    spec_type = "domain" if pt == 'pie' else "xy"
                    plot_cells.append({
                        "type": spec_type, "name": pt, "group": "cat",
                        "title": f"Categorical — {pt.capitalize()}"})

            if not plot_cells:
                print("⚠️ No valid plots to draw.")
                return

            rows = math.ceil(len(plot_cells) / subplot_cols)
            row_specs = []
            row_titles = []

            for r in range(rows):
                spec_row = []
                for c in range(subplot_cols):
                    idx = r * subplot_cols + c
                    if idx < len(plot_cells):
                        spec_row.append({"type": plot_cells[idx]["type"]})
                        row_titles.append(plot_cells[idx]["title"])
                    else:
                        spec_row.append(None)
                        row_titles.append("")
                row_specs.append(spec_row)

            fig = make_subplots(
                rows=rows, cols=subplot_cols, specs=row_specs,
                subplot_titles=row_titles,
                vertical_spacing=0.10, horizontal_spacing=0.06)

            for idx, cell in enumerate(plot_cells):
                row = (idx // subplot_cols) + 1
                col = (idx % subplot_cols) + 1
                pt = cell["name"]

                if cell["group"] == "num":
                    if pt == 'distplot':
                        # Distplot merges all numeric columns into one subplot
                        try:
                            valid = [c for c in num_cols
                                     if len(df[c].dropna()) > 1]
                            if valid:
                                hist_data = [df[c].dropna().values
                                             for c in valid]
                                clrs = [colors[i % len(colors)]
                                        for i in range(len(valid))]
                                fig_dist = ff.create_distplot(
                                    hist_data, valid, colors=clrs,
                                    show_rug=False)
                                for trace in fig_dist['data']:
                                    trace.xaxis = None
                                    trace.yaxis = None
                                    fig.add_trace(trace, row=row, col=col)
                        except Exception:
                            pass
                    else:
                        for i, c in enumerate(num_cols):
                            _add_numeric_trace(
                                fig, pt, c, row, col,
                                colors[i % len(colors)])

                elif cell["group"] == "cat":
                    if pt == 'pie' and len(cat_cols) == 1:
                        # Single categorical column → simple pie
                        _add_categorical_trace(
                            fig, 'pie', cat_cols[0], row, col, colors[0])
                    elif pt == 'pie' and len(cat_cols) > 1:
                        # Multiple categoricals → sunburst
                        try:
                            cat_df = df[cat_cols].fillna("Unknown").astype(str)
                            fig_sun = px.sunburst(cat_df, path=cat_cols)
                            sun_trace = fig_sun.data[0]
                            sun_trace.domain = None
                            fig.add_trace(sun_trace, row=row, col=col)
                        except Exception:
                            pass
                    elif pt in ('histogram', 'bar'):
                        for i, c in enumerate(cat_cols):
                            _add_categorical_trace(
                                fig, pt, c, row, col,
                                colors[i % len(colors)])

            fig.update_layout(
                
                height=max(450, 400 * rows),
                showlegend=True,
                title_text="Summary Dashboard — Combined View",
                title_x=0.5,
                bargap=0.15,
                barmode='group',
                # paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter, sans-serif"),
                legend=dict(orientation="h", yanchor="bottom",
                            y=-0.08, xanchor="center", x=0.5))
            fig.show()

    def plot_relationship(self, df, col1, col2):
        """
        Intelligently selects and displays the optimal interactive Plotly chart to visualize the 
        relationship between two specific columns based on their intrinsic data types.
        
        Parameters
        ----------
        col1 : str
            The first column to plot (usually mapped to the X-axis).
        col2 : str
            The second column to plot (usually mapped to the Y-axis/Color).
            
        Returns
        -------
        None
            Renders an interactive Plotly chart directly in the notebook output.
        """
        if df is None: return
        import plotly.express as px
        is_num1 = pd.api.types.is_numeric_dtype(df[col1])
        is_num2 = pd.api.types.is_numeric_dtype(df[col2])

        if is_num1 and is_num2:
            fig = px.scatter(df, x=col1, y=col2, title=f"Relationship: {col1} vs {col2}")
        elif is_num1 != is_num2:
            num, cat = (col1, col2) if is_num1 else (col2, col1)
            fig = px.box(df, x=cat, y=num, points="all", color=cat, title=f"Distribution of {num} by {cat}")
        else:
            fig = px.histogram(df, x=col1, color=col2, barmode="group", title=f"Relationship: {col1} vs {col2}")
        
        fig.update_layout()
        fig.show()

    def plot_correlation(self, df, col1, col2):
        """
        Auto-detects column data types and calculates the correct statistical association metric 
        between them, generating a tailored visualization.
        
        - Numeric vs Numeric: Pearson's r (Scatter plot)
        - Categorical vs Categorical: Cramér's V (Confusion Matrix Heatmap)
        - Categorical vs Numeric: Point-Biserial or One-Way ANOVA Eta (Box plot)
        
        Parameters
        ----------
        col1 : str
            The first column for correlation calculation.
        col2 : str
            The second column for correlation calculation.
            
        Returns
        -------
        float or str
            The computed correlation value (Pearson's r, Cramér's V) or a formatted string 
            containing the Eta/Point-Biserial statistics.
        """
        if df is None: return
        import plotly.express as px
        from scipy.stats import chi2_contingency, pointbiserialr, f_oneway
        
        valid_data = df[[col1, col2]].dropna()
        if valid_data.empty:
            print("No valid data without NaNs for these columns.")
            return

        is_num1 = pd.api.types.is_numeric_dtype(valid_data[col1])
        is_num2 = pd.api.types.is_numeric_dtype(valid_data[col2])

        if is_num1 and is_num2:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                corr = valid_data[col1].corr(valid_data[col2], method='pearson') if valid_data[col1].nunique() > 1 and valid_data[col2].nunique() > 1 else 0.0
            fig = px.scatter(valid_data, x=col1, y=col2, 
                             title=f"Pearson Correlation (r = {corr:.3f})")
            fig.update_layout()
            fig.show()
            return corr
        elif not is_num1 and not is_num2:
            confusion_matrix = pd.crosstab(valid_data[col1], valid_data[col2])
            val = 0.0
            if confusion_matrix.size > 0 and min(confusion_matrix.shape) > 1:
                chi2 = chi2_contingency(confusion_matrix)[0]
                n = confusion_matrix.sum().sum()
                if n > 0:
                    val = np.sqrt(chi2 / (n * (min(confusion_matrix.shape) - 1)))
            
            fig = px.imshow(confusion_matrix, text_auto=True, color_continuous_scale="viridis",
                            title=f"Cramér's V (V = {val:.3f}): {col1} vs {col2}")
            fig.update_layout()
            fig.show()
            return val
        else:
            cat_col, num_col = (col1, col2) if not is_num1 else (col2, col1)
            categories = valid_data[cat_col].unique()
            if len(categories) == 2:
                binary_cat = pd.get_dummies(valid_data[cat_col], drop_first=True).iloc[:, 0]
                corr, p_val = pointbiserialr(binary_cat, valid_data[num_col])
                title = f"Point-Biserial (r = {corr:.3f}, p = {p_val:.4f})"
            else:
                groups = [valid_data[valid_data[cat_col] == c][num_col] for c in categories]
                groups = [g for g in groups if len(g) > 0]
                if len(groups) > 1:
                    f_val, p_val = f_oneway(*groups)
                    grand_mean = valid_data[num_col].mean()
                    ss_total = ((valid_data[num_col] - grand_mean) ** 2).sum()
                    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
                    eta = np.sqrt(ss_between / ss_total) if ss_total > 0 else 0.0
                    title = f"Eta from ANOVA (η = {eta:.3f}, p = {p_val:.4f})"
                else:
                    eta = 0.0
                    title = f"Eta = {eta:.3f}"
                    
            fig = px.box(valid_data, x=cat_col, y=num_col, points="all", color=cat_col, title=title)
            fig.update_layout()
            fig.show()
            return title

    def plot_all_associations_heatmap(self, df):
        """
        Computes a unified global association matrix combining both numeric and categorical 
        relationships across the entire dataset. It handles dynamic metric selection 
        (Pearson, Cramér's V, ANOVA Eta) automatically.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        pandas.DataFrame
            A square DataFrame matrix containing the pairwise association strengths (0.0 to 1.0) 
            for all columns in the dataset.
        """
        if df is None: return print("Error: No data loaded.")
        import plotly.express as px
        from scipy.stats import chi2_contingency
        
        cols = df.columns
        n_cols = len(cols)
        
        assoc_matrix = pd.DataFrame(np.zeros((n_cols, n_cols)), index=cols, columns=cols)
        
        for i in range(n_cols):
            for j in range(i, n_cols):
                col1 = cols[i]
                col2 = cols[j]
                
                if i == j:
                    assoc_matrix.loc[col1, col2] = 1.0
                    continue
                
                valid_data = df[[col1, col2]].dropna()
                if valid_data.empty:
                    continue
                
                is_num1 = pd.api.types.is_numeric_dtype(valid_data[col1])
                is_num2 = pd.api.types.is_numeric_dtype(valid_data[col2])
                
                if is_num1 and is_num2:
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", RuntimeWarning)
                        val = valid_data[col1].corr(valid_data[col2], method='pearson') if valid_data[col1].nunique() > 1 and valid_data[col2].nunique() > 1 else 0.0
                    val = abs(val) if pd.notna(val) else 0.0
                elif not is_num1 and not is_num2:
                    confusion_matrix = pd.crosstab(valid_data[col1], valid_data[col2])
                    if confusion_matrix.size > 0 and min(confusion_matrix.shape) > 1:
                        chi2 = chi2_contingency(confusion_matrix)[0]
                        n = confusion_matrix.sum().sum()
                        val = np.sqrt(chi2 / (n * (min(confusion_matrix.shape) - 1))) if n > 0 else 0.0
                    else:
                        val = 0.0
                else:
                    cat_col, num_col = (col1, col2) if not is_num1 else (col2, col1)
                    categories = valid_data[cat_col].unique()
                    if len(categories) > 1:
                        groups = [valid_data[valid_data[cat_col] == c][num_col] for c in categories]
                        groups = [g for g in groups if len(g) > 0]
                        
                        grand_mean = valid_data[num_col].mean()
                        ss_total = ((valid_data[num_col] - grand_mean) ** 2).sum()
                        ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
                        
                        val = np.sqrt(ss_between / ss_total) if ss_total > 0 else 0.0
                    else:
                        val = 0.0
                
                assoc_matrix.loc[col1, col2] = round(val, 3)
                assoc_matrix.loc[col2, col1] = round(val, 3)
                
        print("--- Global Association Matrix ---")
        display(assoc_matrix)
        
        fig = px.imshow(
            assoc_matrix,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="viridis",
            title="<b>Unified Association Heatmap (Numeric & Categorical)</b>",
            labels=dict(color="Association Strength")
        )
        
        fig.update_layout(
            height=max(500, n_cols * 45),
            width=max(600, n_cols * 45),
            
        )
        
        fig.show()
        return assoc_matrix

    def test_constant_mean(self, df, columns=None, chunks=10, show_plot=True):
        """
        Performs a Multivariate Analysis of Variance (MANOVA) based test to evaluate whether 
        the structural mean of the dataset is stable across sequential chronological chunks.
        
        Parameters
        ----------
        columns : list of str, optional
            Numerical columns to include in the joint test. Defaults to all numeric columns.
        chunks : int, default 10
            The number of sequential segments to split the dataset into.
        show_plot : bool, default True
            If True, generates a line plot showing the drift of the chunk means over time.
            
        Returns
        -------
        dict
            A dictionary containing the statistical test results:
            {'wilks_lambda': float, 'chi2': float, 'p_value': float, 'df': int}
        """
        if df is None: 
            raise ValueError("Error: No data loaded.")

        target_cols = columns
        if target_cols is None:
            target_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'count' in target_cols: target_cols.remove('count')
        elif isinstance(target_cols, str):
            target_cols = [target_cols]
            
        analysis_df = df[target_cols].copy().dropna()
        n = len(analysis_df)
        m = len(target_cols)
        chunk_size = n // chunks
        if chunk_size < m:
            raise ValueError(f"Sample size per chunk ({chunk_size}) must be greater than features ({m}). Reduce chunks.")

        analysis_df['_chunk_label'] = np.minimum(np.arange(n) // chunk_size, chunks - 1)

        global_mean = analysis_df[target_cols].mean().values
        W = np.zeros((m, m))
        B = np.zeros((m, m))

        chunk_means = []
        
        for label, group in analysis_df.groupby('_chunk_label'):
            X_chunk = group[target_cols].values
            chunk_mean = X_chunk.mean(axis=0)
            chunk_means.append(chunk_mean)
            n_j = len(X_chunk)
            
            W += np.dot((X_chunk - chunk_mean).T, (X_chunk - chunk_mean))
            mean_diff = (chunk_mean - global_mean).reshape(-1, 1)
            B += n_j * np.dot(mean_diff, mean_diff.T)

        import scipy.stats
        epsilon = 1e-6 * np.eye(m)
        W_stable = W + epsilon
        T_stable = W + B + epsilon

        sign_W, log_det_W = np.linalg.slogdet(W_stable)
        sign_T, log_det_T = np.linalg.slogdet(T_stable)

        log_wilks = log_det_W - log_det_T
        wilks_lambda = np.exp(log_wilks)

        df_stat = m * (chunks - 1)
        scale_factor = n - 1 - (m + chunks) / 2
        chi2_calc = max(0.0, -scale_factor * log_wilks)
        p_value = 1.0 - scipy.stats.chi2.cdf(chi2_calc, df_stat)

        print(f"\n--- MANOVA Mean Homogeneity Test (g={chunks} chunks, m={m} features) ---")
        print(f"Wilks' Lambda (Λ): {wilks_lambda:.5f}")
        print(f"Chi-Square Statistic: {chi2_calc:.4f} | Degrees of Freedom: {df_stat}")
        print(f"P-Value: {p_value:.6f}")
        
        if p_value > 0.05:
            print("✅ Success: Fail to reject H0. First joint moment is stable.")
        else:
            print("🚨 Warning: Reject H0. Significant mean drift detected.")

        if show_plot:
            import plotly.graph_objects as go
            fig = go.Figure()
            for i, col in enumerate(target_cols):
                fig.add_trace(go.Scatter(
                    x=list(range(1, chunks + 1)),
                    y=[cm[i] for cm in chunk_means],
                    mode='lines+markers',
                    name=col
                ))
            fig.update_layout(
                title="Chunk Means Over Sequential Blocks",
                xaxis_title="Chunk Number",
                yaxis_title="Mean Value",
                
            )
            fig.show()

        return {"wilks_lambda": wilks_lambda, "chi2": chi2_calc, "p_value": p_value, "df": df_stat}

    def test_constant_covariance(self, df, columns=None, chunks=5, show_plot=True):
        """
        Performs Box's M-test to evaluate whether the multivariate covariance structure 
        is stable (homoscedastic) across sequential chronological chunks.
        
        Parameters
        ----------
        columns : list of str, optional
            Numerical columns to include in the joint test. Defaults to all numeric columns.
        chunks : int, default 5
            The number of sequential segments to split the dataset into.
        show_plot : bool, default True
            If True, generates a line plot showing the drift of feature variances over time.
            
        Returns
        -------
        dict
            A dictionary containing the statistical test results:
            {'M': float, 'chi2': float, 'p_value': float, 'df': int}
        """
        if df is None: 
            raise ValueError("Error: No data loaded.")

        target_cols = columns
        if target_cols is None:
            target_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'count' in target_cols: target_cols.remove('count')
        elif isinstance(target_cols, str):
            target_cols = [target_cols]

        analysis_df = df[target_cols].copy().dropna()
        n = len(analysis_df)
        m = len(target_cols)
        chunk_size = n // chunks
        
        if chunk_size <= m:
            raise ValueError(f"Degrees of freedom per chunk ({chunk_size - 1}) must be greater than number of dimensions ({m}). Reduce chunks.")

        analysis_df['_chunk_label'] = np.minimum(np.arange(n) // chunk_size, chunks - 1)
        
        S_chunks = []
        n_chunks = []
        log_det_S = 0.0
        pooled_S = np.zeros((m, m))
        total_df = 0
        
        epsilon = 1e-6 * np.eye(m)
        chunk_variances = []
        
        for label, group in analysis_df.groupby('_chunk_label'):
            X_chunk = group[target_cols].values
            n_j = len(X_chunk)
            S_j = np.cov(X_chunk, rowvar=False, ddof=1) + epsilon
            
            chunk_variances.append(np.diag(S_j))

            S_chunks.append(S_j)
            n_chunks.append(n_j)
            
            df_j = n_j - 1
            pooled_S += df_j * S_j
            total_df += df_j
            
            sign, logdet = np.linalg.slogdet(S_j)
            log_det_S += df_j * logdet

        pooled_S /= total_df
        sign_p, log_det_Sp = np.linalg.slogdet(pooled_S)

        M = total_df * log_det_Sp - log_det_S
        
        sum_inv_df = sum(1.0 / (nj - 1) for nj in n_chunks)
        inv_total_df = 1.0 / total_df
        numerator_C = 2.0 * m**2 + 3.0 * m - 1.0
        denominator_C = 6.0 * (m + 1.0) * (chunks - 1.0)
        C = (sum_inv_df - inv_total_df) * (numerator_C / denominator_C)
        
        chi2_calc = max(0.0, M * (1.0 - C))
        df_stat = (m * (m + 1) * (chunks - 1)) / 2.0
        import scipy.stats
        p_value = 1.0 - scipy.stats.chi2.cdf(chi2_calc, df_stat)

        print(f"\n--- Box's M Covariance Homogeneity Test (g={chunks} chunks, m={m} features) ---")
        print(f"Box's M Statistic: {M:.4f}")
        print(f"Asymptotic Chi-Square: {chi2_calc:.4f} | Degrees of Freedom: {int(df_stat)}")
        print(f"P-Value: {p_value:.6f}")
        
        if p_value > 0.001:
            print("✅ Success: Fail to reject H0. Covariance structure is stable.")
        else:
            print("🚨 Warning: Reject H0. Covariance drift detected.")

        if show_plot:
            import plotly.graph_objects as go
            fig = go.Figure()
            for i, col in enumerate(target_cols):
                fig.add_trace(go.Scatter(
                    x=list(range(1, chunks + 1)),
                    y=[cv[i] for cv in chunk_variances],
                    mode='lines+markers',
                    name=f"Var({col})"
                ))
            fig.update_layout(
                title="Chunk Variances Over Sequential Blocks",
                xaxis_title="Chunk Number",
                yaxis_title="Variance",
                
            )
            fig.show()

        return {"M": M, "chi2": chi2_calc, "p_value": p_value, "df": int(df_stat)}

    def test_row_independence(self, df, columns=None, max_lag=None, show_plot=True):
        """
        Implements a Multivariate Ljung-Box Portmanteau test for serial independence.
        Checks for autoregressive dependencies (autocorrelation) across sequential rows.
        
        Parameters
        ----------
        columns : list of str, optional
            Numerical columns to evaluate. Defaults to all numeric columns.
        max_lag : int, optional
            The maximum number of row-lags to check. Defaults to ceil(log(N)).
        show_plot : bool, default True
            If True, generates a bar chart displaying the pseudo-correlation metrics by lag.
            
        Returns
        -------
        dict
            A dictionary containing the statistical test results:
            {'Q_m': float, 'p_value': float, 'df': int}
        """
        if df is None: 
            raise ValueError("Error: No data loaded.")

        target_cols = columns
        if target_cols is None:
            target_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'count' in target_cols: target_cols.remove('count')
        elif isinstance(target_cols, str):
            target_cols = [target_cols]

        analysis_df = df[target_cols].copy().dropna()
        n = len(analysis_df)
        m = len(target_cols)
        
        if max_lag is None:
            max_lag = int(np.ceil(np.log(n)))
        
        X = analysis_df[target_cols].values
        X_centered = X - X.mean(axis=0)
        
        epsilon = 1e-6 * np.eye(m)
        Gamma_0 = (np.dot(X_centered.T, X_centered) / n) + epsilon
        
        try:
            inv_Gamma_0 = np.linalg.inv(Gamma_0)
        except np.linalg.LinAlgError:
            inv_Gamma_0 = np.linalg.pinv(Gamma_0)
        
        Q_m = 0.0
        lag_correlations = []
        
        for k in range(1, max_lag + 1):
            Gamma_k = np.dot(X_centered[k:].T, X_centered[:-k]) / n
            M_k = np.dot(np.dot(np.dot(Gamma_k.T, inv_Gamma_0), Gamma_k), inv_Gamma_0)
            trace_val = np.trace(M_k)
            lag_correlations.append(trace_val / m) # simple pseudo-correlation metric for the plot
            
            Q_m += trace_val / (n - k)
            
        Q_m *= (n ** 2)
        Q_m = max(0.0, Q_m)
        df_stat = (m ** 2) * max_lag
        import scipy.stats
        p_value = 1.0 - scipy.stats.chi2.cdf(Q_m, df_stat)

        print(f"\n--- Multivariate Ljung-Box Serial Independence Test (Lags Checked = {max_lag}) ---")
        print(f"Portmanteau Statistic Q_m(H): {Q_m:.4f}")
        print(f"Degrees of Freedom: {df_stat}")
        print(f"P-Value: {p_value:.6f}")
        
        if p_value > 0.05:
            print("✅ Success: Fail to reject H0. Rows are independent.")
        else:
            print("🚨 Warning: Reject H0. Serial dependency detected.")

        if show_plot:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=list(range(1, max_lag + 1)),
                y=lag_correlations,
                name="Multivariate Lag Correlation",
                marker_color="indianred"
            ))
            fig.update_layout(
                title="Multivariate Autocorrelation by Lag",
                xaxis_title="Lag k",
                yaxis_title="Trace Statistic (Normalized)",
                
            )
            fig.show()

        return {"Q_m": Q_m, "p_value": p_value, "df": df_stat}
