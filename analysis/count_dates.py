import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- Configuration ---
file_path = "disease_data_with_biocuration_date.tsv"
# We want to check for dates *after* XXX
cutoff_date = pd.Timestamp("2024-01-01")
histogram_output_file = "biocuration_date_histogram.png"

try:
    # Read the tab-separated file into a pandas DataFrame
    df = pd.read_csv(file_path, sep="\t")

    # --- Data Processing ---
    # Convert the 'earliest_biocuration_date' column to datetime objects.
    # The `errors='coerce'` argument will turn any unparseable entries into 'NaT' (Not a Time).
    df["earliest_biocuration_date"] = pd.to_datetime(
        df["earliest_biocuration_date"], errors="coerce"
    )

    # Filter out rows where the date could not be parsed
    valid_dates_df = df.dropna(subset=["earliest_biocuration_date"])

    # --- Counting ---
    # Count lines with a date AFTER the cutoff date
    count_after_cutoff = (valid_dates_df["earliest_biocuration_date"] > cutoff_date).sum()

    # Count lines with a date ON or BEFORE the cutoff date
    count_before_cutoff = (valid_dates_df["earliest_biocuration_date"] <= cutoff_date).sum()

    # --- Reporting Results ---
    print(f"--- Analysis of: {file_path} ---")
    print(f"Total entries read: {len(df)}")
    print(f"Entries with a valid date: {len(valid_dates_df)}")
    print("-" * 35)

    print(f"Entries with biocuration date AFTER  {cutoff_date.date()}: {count_after_cutoff}")
    print(f"Entries with biocuration date ON or BEFORE {cutoff_date.date()}: {count_before_cutoff}")
    print("-" * 35)

    # --- Histogram Generation ---
    print(f"Generating histogram from 2009 to 2025...")
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(14, 7))

    # Define the bins to be each year from 2009 to 2025
    bins = pd.date_range(start="2009-01-01", end="2026-01-01", freq="AS")  # 'AS' is 'Year Start'

    ax.hist(
        valid_dates_df["earliest_biocuration_date"], bins=bins, edgecolor="black", color="#2b7288"
    )

    # Formatting the plot
    ax.set_title("Distribution of Earliest Biocuration Dates", fontsize=16)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Number of Entries", fontsize=12)

    # Set x-axis limits and format the ticks to show only the year
    ax.set_xlim(pd.Timestamp("2009-01-01"), pd.Timestamp("2025-12-31"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.xticks(rotation=45)

    plt.tight_layout()

    # Save the plot to a file
    plt.savefig(histogram_output_file)
    print(f"Histogram saved to '{histogram_output_file}'")

    # Display the plot
    plt.show()


except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found. Please ensure it's in the same directory.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
