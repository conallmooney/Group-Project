import wbgapi as wb

df = wb.data.DataFrame(
    ["FP.CPI.TOTL.ZG", "NY.GDP.MKTP.KD.ZG"],   #inflation, GDP growth
    time=range(2018, 2025),
    skipAggs=True,   #drop groupings like "Euro area" and "World"
    labels=True,
)
print(df.shape)
print(df.head(10))
