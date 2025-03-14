# csv data from

# case incidence rate per 1M
# https://immunizationdata.who.int/global/wiise-detail-page/pertussis-reported-cases-and-incidence?GROUP=Countries&YEAR=

# vac coverage Official Numbers Pertussis-containing vaccine 3d Dose
# https://immunizationdata.who.int/global/wiise-detail-page/diphtheria-tetanus-toxoid-and-pertussis-(dtp)-vaccination-coverage?GROUP=Countries&ANTIGEN=DTPCV3&YEAR=&CODE=


import pandas as pd
import plotly.graph_objects as go
from dowhy import CausalModel
import numpy as np

# Load data
vac_coverage_df = pd.read_csv(r"C:\PERT-py\DTP vac coverage 2025-04-03 15-23 UTC.csv", encoding='ISO-8859-1', on_bad_lines='skip', delimiter=';')
reported_cases_df = pd.read_csv(r"C:\PERT-py\DTP reported cases and incidence 2025-04-03 15-25 RATE.csv", encoding='ISO-8859-1', on_bad_lines='skip', delimiter=';')

filename_plot_text = "Dowhy causal estimate on mean vac coverage and cases pertussis"
year_range_text = "2000-2023"

# Clean up column names
vac_coverage_df.columns = vac_coverage_df.columns.str.strip()
reported_cases_df.columns = reported_cases_df.columns.str.strip()

# Normalize country names (strip spaces and convert to lowercase)
vac_coverage_df.set_index('Country', inplace=True)
reported_cases_df.set_index('Country', inplace=True)

vac_coverage_df.index = vac_coverage_df.index.str.lower()
reported_cases_df.index = reported_cases_df.index.str.lower()

# Remove thousands dots and replace commas with periods for numeric conversion
vac_coverage_df = vac_coverage_df.replace({r'\.': '', ',': '.'}, regex=True)
reported_cases_df = reported_cases_df.replace({r'\.': '', ',': '.'}, regex=True)

# Convert columns (except the 'Country' index) to numeric
vac_coverage_df = vac_coverage_df.apply(pd.to_numeric, errors='coerce')
reported_cases_df = reported_cases_df.apply(pd.to_numeric, errors='coerce')

# Filter columns for years >= 1980
vac_coverage_df = vac_coverage_df.loc[:, vac_coverage_df.columns.astype(int) >= 2000]
reported_cases_df = reported_cases_df.loc[:, reported_cases_df.columns.astype(int) >= 2000]

# Find common countries between the two datasets
common_countries = vac_coverage_df.index.intersection(reported_cases_df.index)

# Lists for mean values, causal effects, and years used
mean_vac = []
mean_cases = []
causal_effects = []
years_used = []
country_annotations = []

# Create or open log file to write years used for causal effect
log_file_path = fr"C:\PERT-py\C) {filename_plot_text} valid years for dowhy calc {year_range_text}.txt"

with open(log_file_path, "w") as log_file:
    # Iterate through common countries for causal analysis
    for country in common_countries:
        # Get valid years for vaccination coverage
        valid_vac_years = vac_coverage_df.columns[~vac_coverage_df.loc[country].isna() & (vac_coverage_df.loc[country] != 0)]
        valid_vac = vac_coverage_df.loc[country, valid_vac_years].values

        # Get valid years for reported cases
        valid_cases_years = reported_cases_df.columns[~reported_cases_df.loc[country].isna() & (reported_cases_df.loc[country] != 0)]
        valid_cases = reported_cases_df.loc[country, valid_cases_years].values

        # Find the common years
        common_years = valid_vac_years.intersection(valid_cases_years)
        
        if len(common_years) == 0:
            print(f"Skipping {country} due to no common valid years.")
            continue

        # Filter valid data for the common years
        valid_vac = vac_coverage_df.loc[country, common_years].values
        valid_cases = reported_cases_df.loc[country, common_years].values

        # Calculate mean values for the country
        mean_vac_country = valid_vac.mean()
        mean_cases_country = valid_cases.mean()

        # Create the dataset for causal analysis
        data = pd.DataFrame({
            'vac': valid_vac,
            'cases': valid_cases
        })

        # Define causal graph (example)
        causal_graph = """
        digraph {
            vac -> cases;
        }
        """

        # Initialize causal model
        model = CausalModel(
            data=data,
            treatment='vac',  # Treatment variable (vaccination coverage)
            outcome='cases',  # Outcome variable (reported cases)
            graph=causal_graph  # Causal graph
        )

        # Perform causal inference
        identified_estimand = model.identify_effect()

        try:
            # Estimate the causal effect using backdoor linear regression
            causal_estimate = model.estimate_effect(
                identified_estimand,
                method_name="backdoor.linear_regression",  # Specify the method
                test_significance=True
            )
            print(f"Causal estimate for {country}: {causal_estimate.value}")

            # Append results to lists
            mean_vac.append(mean_vac_country)
            mean_cases.append(mean_cases_country)
            causal_effects.append(causal_estimate.value)
            years_used.append(list(common_years))
            country_annotations.append(f"Years: {', '.join(map(str, common_years))}")

            # Log the years for each country
            log_file.write(f"Country: {country.capitalize()}\n")
            log_file.write(f"Years used for causal analysis: {', '.join(map(str, common_years))}\n\n")

        except Exception as e:
            print(f"Error for {country}: {e}")
            continue

# Winsorization: Clip extreme values (outliers) at 5th and 95th percentiles
if len(causal_effects) > 0:
    # Calculate the 99.2th percentile (upper bound for outliers)
    upper_percentile_causal = np.percentile(causal_effects, 99.2)
    upper_percentile_vac = np.percentile(mean_vac, 99.2)
    upper_percentile_cases = np.percentile(mean_cases, 99.2)
    
    # Apply Winsorization only for extreme high values (above the 99.2 percentile)
    causal_effects_winsorized = [min(effect, upper_percentile_causal) for effect in causal_effects]
    mean_vac_winsorized = [min(vac, upper_percentile_vac) for vac in mean_vac]
    mean_cases_winsorized = [min(cases, upper_percentile_cases) for cases in mean_cases]
    
    # Create plot
    fig = go.Figure()

    # Add scatter plot for mean vaccination coverage with secondary y-axis
    fig.add_trace(go.Scatter(
        x=common_countries[:len(mean_vac_winsorized)],
        y=mean_vac_winsorized,
        mode='markers',
        name='Mean Vaccination Coverage (%) clipped',
        marker=dict(color='blue', size=5),  # Smaller circles
        yaxis="y2"  # Use the secondary y-axis for this trace
    ))

    # Add scatter plot for causal effect (Winsorized)
    fig.add_trace(go.Scatter(
        x=common_countries[:len(causal_effects_winsorized)],
        y=causal_effects_winsorized,
        mode='markers',
        name='Causal Effect Vac Coverage on Cases clipped',
        marker=dict(color='green', size=5),  # Smaller circles
    ))

    # Add scatter plot for reported cases on the third y-axis
    fig.add_trace(go.Scatter(
        x=common_countries[:len(mean_cases_winsorized)],
        y=mean_cases_winsorized,
        mode='markers',
        name='Mean Reported Cases/1M clipped)',
        marker=dict(color='red', size=5),  # Smaller circles
        yaxis="y3"  # Use the third y-axis for this trace
    ))
    
    # Add horizontal line at y = 0.95 on the secondary y-axis
    fig.add_trace(go.Scatter(
        x=common_countries[:len(mean_vac_winsorized)],  # Same x-axis range as other data
        y=[95] * len(common_countries[:len(mean_vac_winsorized)]),  # Constant y-value of 0.95
        mode='lines',  # A line instead of markers
        name="Line at 95 (Vac Coverage)",
        line=dict(color='red', dash='dot', width=1),  # Red dotted line
        yaxis="y2"  # Use the secondary y-axis
    ))

    # Layout settings with secondary y-axis for vaccination coverage
    fig.update_layout(
        title=f"Dowhy Causal Effect estimation Vaccination Coverage on Reported Cases Pertussis({year_range_text})",
        xaxis_title="Country",
        showlegend=True,
        
        yaxis=dict(
            title="Causal Effect of Vaccination Coverage on Cases",
            side="left",
            autorange=True,  # Automatically adjust the range
            position=0.05
        ),
        
        # Secondary y-axis for vaccination coverage
        yaxis2=dict(
            title="avg vac coverage %",
            side="right",
            overlaying="y",
            autorange=True,  # Automatically adjust the range
            tickformat=".1f",  # Format ticks to two decimal places
            tickmode='auto',  # Automatically adjust tick positions
            position=0.95
        ),
        
        # Third y-axis for reported cases
        yaxis3=dict(
            title="avg cases/1M",
            side="right",
            overlaying="y",
            autorange=True,  # Automatically adjust the range
            tickformat=".1f",  # Format ticks to two decimal places
            tickmode='auto',  # Automatically adjust tick positions
            position=1  # Position the third axis to the far right
        ),
        
        # Adjust spacing and margin
        margin=dict(l=40, r=60, t=40, b=40),
        
        # Reposition the legend
        legend=dict(
            orientation="v",
            xanchor="left",
            x=1.05,
            yanchor="top",
            y=1,
            font=dict(size=10)
        ),

        # Clip the x-axis labels to 15 characters
        xaxis=dict(
            tickmode="array",
            tickvals=common_countries[:len(mean_vac_winsorized)],
            ticktext=[country[:15] for country in common_countries[:len(mean_vac_winsorized)]],
            tickfont=dict(
                size=11,  # Adjust the font size here
                family='Arial',  # You can set a different font family if needed
                color='black'  # You can also change the font color
            )
        ),

       

    )

    # Save the plot
    fig.write_html(fr"C:\PERT-py\C) {filename_plot_text} {year_range_text}.html")

    # Show the plot
    fig.show()

    print(fr"C:\PERT-py\C) {filename_plot_text} {year_range_text}.html has been saved.")
else:
    print("No valid data to plot.")
