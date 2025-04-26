import pandas as pd

leases_df = pd.read_csv("../data/Leases.csv")

# Drop na rows for company name
# leases_df = pd.DataFrame(leases_df, columns=["company_name"]).dropna()

# Omit rows with na company_name
# leases_df = leases_df[leases_df["company_name"].notna()]

# Remove columns with all na entries
remove_features = [
    "direct_availability_proportion",
    "direct_internal_class_rent",
    "direct_overall_rent",
    "sublet_available_space",
    "sublet_availability_proportion",
    "sublet_internal_class_rent",
    "sublet_overall_rent",
    "company_name",
]
for feature in remove_features:
    leases_df = leases_df[leases_df[feature].notna()]


leases_by_rba = leases_df["RBA"]
leases_by_rba.head()

leases_by_rba.to_csv("../data/leases_by_rba.csv")

# Drop RBA and space_type
leases_df = leases_df.drop(columns=[
    "RBA", "space_type", "leasing", "monthsigned", "building_name", "building_id", "address", "region", "city"
], axis=1)

leases_by_rba.to_csv("./data/leases_by_rba.csv")