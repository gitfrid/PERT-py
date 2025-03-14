# csv data from

# case incidence rate per 1M
# https://immunizationdata.who.int/global/wiise-detail-page/pertussis-reported-cases-and-incidence?GROUP=Countries&YEAR=

# vac coverage Official Numbers Pertussis-containing vaccine 3d Dose
# https://immunizationdata.who.int/global/wiise-detail-page/diphtheria-tetanus-toxoid-and-pertussis-(dtp)-vaccination-coverage?GROUP=Countries&ANTIGEN=DTPCV3&YEAR=&CODE=


import pandas as pd
import plotly.graph_objects as go

# Load the data with error handling
vac_coverage_df = pd.read_csv(r"C:\PERT-py\DTP vac coverage 2025-04-03 15-23 UTC.csv", encoding='ISO-8859-1', on_bad_lines='skip', delimiter=';')
reported_cases_df = pd.read_csv(r"C:\PERT-py\DTP reported cases and incidence 2025-04-03 15-25 RATE.csv", encoding='ISO-8859-1', on_bad_lines='skip', delimiter=';')


# Clean column names
vac_coverage_df.columns = vac_coverage_df.columns.str.strip()
reported_cases_df.columns = reported_cases_df.columns.str.strip()

# Set 'Country' as the index for both DataFrames
vac_coverage_df.set_index('Country', inplace=True)
reported_cases_df.set_index('Country', inplace=True)

# Clean country names by stripping extra spaces
vac_coverage_df.index = vac_coverage_df.index.str.strip()
reported_cases_df.index = reported_cases_df.index.str.strip()

# Normalize country names (strip spaces and convert to lowercase) for comparison
vac_coverage_df.index = vac_coverage_df.index.str.lower()
reported_cases_df.index = reported_cases_df.index.str.lower()

# Remove thousands dots and replace commas with periods for all values in the dataframes
vac_coverage_df = vac_coverage_df.replace({r'\.': '', ',': '.'}, regex=True)
reported_cases_df = reported_cases_df.replace({r'\.': '', ',': '.'}, regex=True)

# Convert columns (except the 'Country' index) to numeric, forcing errors to NaN
vac_coverage_df = vac_coverage_df.apply(pd.to_numeric, errors='coerce')
reported_cases_df = reported_cases_df.apply(pd.to_numeric, errors='coerce')

# Filter columns to include only years from 1980 onwards
vac_coverage_df = vac_coverage_df.loc[:, vac_coverage_df.columns.astype(int) >= 1980]
reported_cases_df = reported_cases_df.loc[:, reported_cases_df.columns.astype(int) >= 1980]

# Find common countries between both datasets
common_countries = vac_coverage_df.index.intersection(reported_cases_df.index)

# Sort countries alphabetically
common_countries = sorted(common_countries)

# Create traces for both datasets (vaccination coverage and reported cases)
vac_coverage_traces = []
reported_cases_traces = []

# For each country, create both the vaccination coverage trace and reported cases trace
for country in common_countries:
    # Truncate the country name for the legend if it's too long (e.g., first 20 characters)
    legend_name = f'{country[:20]}...' if len(country) > 20 else country
    
    # Plot the vaccination coverage data
    trace_vac_coverage = go.Scatter(
        x=vac_coverage_df.columns,  # Year columns
        y=vac_coverage_df.loc[country],  # Values for this country
        mode='lines',
        name=f'{legend_name} - Vac Cover',  # Use the truncated name here
        yaxis='y2',
        visible=True  # Initially visible
    )
    
    # Plot the reported cases data
    trace_reported_cases = go.Scatter(
        x=reported_cases_df.columns,  # Year columns
        y=reported_cases_df.loc[country],  # Values for this country
        mode='lines',
        name=f'{legend_name} - case incidence/1M',  # Use the truncated name here
        yaxis='y1',
        visible=False  # Initially hidden
    )
    
    # Add traces to the respective lists
    vac_coverage_traces.append(trace_vac_coverage)
    reported_cases_traces.append(trace_reported_cases)

# Layout with two y-axes and legend visibility
layout = go.Layout(
    title='Pertussis vaccination coverage vs reported case incidence rate for different countries',
    xaxis=dict(title='Year'),
    yaxis=dict(title='cases/1M', 
               side='left',
               tickformat=".0f"
    ),
    yaxis2=dict(
        title='Vaccination Coverage (%)',
        side='right',
        overlaying='y1',
        tickformat=".0f",  # Format the numbers to show without thousands separator
        tickmode='auto',  # Automatically adjust tick positions
        showgrid=True,  # Show grid lines on the right y-axis
        ticksuffix=' ',  # Optional: Adds space after tick values (for better readability)
        tickprefix='',  # Optional: Remove any prefix for the right y-axis ticks
    ),
    showlegend=True,  # Make sure legend is shown
    legend=dict(
        x=1.05,  # Move the legend a little further to the right (beyond the plot area)
        y=1,  # Align legend at the top right
        traceorder='normal',  # Ensure traces are in the correct order
        orientation='v',  # Make legend vertical
        bgcolor='rgba(255, 255, 255, 0.7)',  # Optional: Add a transparent background for readability
        bordercolor='black',  # Optional: Border color around the legend
        borderwidth=1,  # Optional: Border width around the legend
        itemwidth=30,  # Adjust the width of each legend item to fit more compactly
        itemsizing='trace',  # Ensure each legend item adjusts to its content
        tracegroupgap=5,  # Adjusts the gap between groups of traces in the legend
        font=dict(
            size=10  # Smaller font size for the legend items (adjust as needed)
        ),
    ),
    updatemenus=[
        # Dropdown menu to select visibility of reported cases, vaccination coverage, or both
        dict(
            type='dropdown',
            buttons=[
                dict(
                    label='Show Vaccination Coverage',
                    method='update',
                    args=[{'visible': [True] * len(vac_coverage_traces) + [False] * len(reported_cases_traces)},
                          {'title': 'Pertussis vaccination coverage'}]
                ),
                dict(
                    label='Show Reported Cases',
                    method='update',
                    args=[{'visible': [False] * len(vac_coverage_traces) + [True] * len(reported_cases_traces)},
                          {'title': 'Reported Cases Incidence Rate'}]
                ),
                dict(
                    label='Show Both',
                    method='update',
                    args=[{
                        'visible': [True] * len(vac_coverage_traces) + [True] * len(reported_cases_traces)
                    },
                          {'title': 'Pertussis Vaccination Coverage and Reported Cases'}]
                ),
            ],
            direction='down',
            pad={'r': 10, 't': 10},
            showactive=True,  # Make sure the active button is visible
            x=0.8,  # Position the dropdown a little further to the right
            xanchor='left',
            y=1.1,  # Position the dropdown lower down
            yanchor='top',
        ),
    ]
)

# Create the figure
fig = go.Figure(data=vac_coverage_traces + reported_cases_traces, layout=layout)

# Save the plot to an HTML file
fig.write_html(r"C:\PERT-py\D) PERT vaccination_vs_reported_cases_dropdown_1980_2023.html")

print("Plot has been saved to 'vaccination_vs_reported_cases.html'.")

# Show the plot (uncomment if you want to display it in a browser)
# fig.show()
