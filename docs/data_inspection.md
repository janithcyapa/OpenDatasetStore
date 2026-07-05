# Data Inspection & Sanitation

`OpenDatasetStore` comes with a built-in suite of tools for data inspection, cleaning, and preprocessing. These methods are designed to be stateless: they accept a pandas DataFrame (`df`) as an argument and return a modified copy or perform an action (like plotting). This ensures that your raw data remains untouched until you explicitly save the processed data.

All of these tools are accessible directly on your `store` instance.

## 1. Summarizing Data

To get a quick overview of a DataFrame's structure, missing values, and data types, you can use `get_df_summary`:

```python
# df is a pandas DataFrame you've retrieved via store.get_entry_raw_data()
store.get_df_summary(df)

# For detailed statistical metrics (min, max, mean, standard deviation, etc.)
store.get_df_summary(df, detailed=True)
```

## 2. Interactive Dashboards

You can generate a comprehensive, interactive Plotly dashboard to visualize the distributions of both numeric and categorical columns.

```python
# Generate a full dashboard for all columns
store.summary_plot(df)

# Generate a dashboard for specific columns only
store.summary_plot(df, columns=['age', 'blood_pressure', 'diagnosis'])
```

## 3. Handling Missing Data & Duplicates

Identify and handle missing data easily.

```python
# View rows that contain any missing data
missing_rows = store.get_missing_data(df, axis='rows')

# Impute missing values using the median for numeric columns
df_clean = store.modify_missing_values(df, strategy='median')

# Impute missing values with a constant for specific columns
df_clean = store.modify_missing_values(df, columns=['status'], strategy='constant', fill_value='Unknown')

# Drop exact duplicate rows
df_clean = store.modify_duplicates(df_clean)
```

## 4. Anomaly & Outlier Detection

The library includes built-in Interquartile Range (IQR) outlier detection.

```python
# Identify outliers (prints a report but does not modify the DataFrame)
store.modify_outliers(df)

# Automatically drop any rows containing outliers in numeric columns
df_clean = store.modify_outliers(df, find_and_delete=True)
```

## 5. Statistical Tests & Associations

Perform advanced bivariate and multivariate statistical tests directly from the store.

```python
# Generate an interactive scatter/box/histogram based on data types
store.plot_relationship(df, 'age', 'blood_pressure')

# Compute correlation (Pearson, Cramér's V, or ANOVA Eta) and plot it
correlation_value = store.plot_correlation(df, 'age', 'diagnosis')

# Compute and plot a unified global association matrix (Heatmap) for all columns
assoc_matrix = store.plot_all_associations_heatmap(df)
```

Advanced Multivariate Tests (Chronological Stability):
```python
# Test if the multivariate mean drifts over time (MANOVA)
results = store.test_constant_mean(df, chunks=10)

# Test if the multivariate covariance structure is stable (Box's M)
results = store.test_constant_covariance(df, chunks=5)

# Test for serial row independence (Multivariate Ljung-Box)
results = store.test_row_independence(df)
```

## 6. Data Normalization & Extraction

```python
# Normalize numeric data using MinMax scaling
df_scaled = store.modify_normalize_data(df, columns=['age'], method='minmax')

# Extract specific subset based on types or indices
df_subset = store.extract_data(df, column_type='numerical')
```
