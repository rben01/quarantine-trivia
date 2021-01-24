# %%
import pandas as pd

DATE = "Date"
START_DATE = "Start Date"
END_DATE = "End Date"
PRESIDENCY_PERIOD_COL = "Presidency[a].1"
PRESIDENT_COL = "President.1"
JOIN_PRODUCT_COL = "Join_"
MATCH_COL = "Match_"

# %%
with open("./natl_parks_table.html") as f:
    natl_parks_df: pd.DataFrame = pd.read_html(f, flavor="lxml")[0]


natl_parks_df["Date"] = pd.to_datetime(
    natl_parks_df["Date established as park[5][10]"].str.extract(
        r"^(.*?\d{4})", expand=False
    )
)
natl_parks_df[JOIN_PRODUCT_COL] = 0

natl_parks_df

# %%
with open("./presidents_table.html") as f:
    presidents_df: pd.DataFrame = pd.read_html(f, flavor="lxml")[0].iloc[:-1]

presidents_df[START_DATE] = pd.to_datetime(
    presidents_df[PRESIDENCY_PERIOD_COL]
    .str.extract(r"^([\w\s,]*?\d{4})", expand=False)
    .str.strip()
)
presidents_df[END_DATE] = pd.to_datetime(
    presidents_df[PRESIDENCY_PERIOD_COL]
    .str.extract(r"([\w\s,]*?\d{4})$", expand=False)
    .str.strip()
).fillna(pd.Timestamp.now().normalize() + pd.Timedelta(days=10))

presidents_df = presidents_df.drop_duplicates([PRESIDENT_COL, START_DATE, END_DATE])
presidents_df[JOIN_PRODUCT_COL] = 0

presidents_df

# %%
joined_df = natl_parks_df.merge(presidents_df, how="inner", on=JOIN_PRODUCT_COL)
joined_df[MATCH_COL] = (joined_df[DATE] >= joined_df[START_DATE]) & (
    joined_df[DATE] < joined_df[END_DATE]
)
joined_df.groupby(PRESIDENT_COL)[MATCH_COL].sum().sort_values()


# %%
