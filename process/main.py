import pandas as pd

leases_df = pd.read_csv("../data/Leases.csv")

# Drop na rows for company name
# leases_df = pd.DataFrame(leases_df, columns=["company_name"]).dropna()

# Omit rows with na company_name
leases_df = leases_df[leases_df["company_name"].notna()]

# Remove columns with all na entries
remove_features = [
    "direct_availability_proportion",
    "direct_internal_class_rent",
    "direct_overall_rent",
    "sublet_available_space",
    "sublet_availability_proportion",
    "sublet_internal_class_rent",
    "sublet_overall_rent",
    "leases"
]
for feature in remove_features:
    leases_df = leases_df[leases_df[feature].notna()]

# Export
leases_df.to_csv("../data/cleaned_leases.csv", index=False)