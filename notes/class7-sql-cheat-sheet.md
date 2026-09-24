# Class 7 companion — DataCamp "SQL Basics Cheat Sheet"
Reference handout accompanying [class7-slides.md](class7-slides.md) (the DuckDB section in
particular runs plain SQL inside Python). Uses a sample `airbnb_listings` table
(`id, city, country, number_of_rooms, year_listed`) throughout.

## Querying tables
```sql
SELECT * FROM airbnb_listings;                          -- all columns
SELECT city FROM airbnb_listings;                        -- one column
SELECT city, year_listed FROM airbnb_listings;            -- multiple columns
SELECT id, city FROM airbnb_listings ORDER BY number_of_rooms ASC;   -- sort ascending
SELECT id, city FROM airbnb_listings ORDER BY number_of_rooms DESC;  -- sort descending
SELECT * FROM airbnb_listings LIMIT 5;                    -- first 5 rows
SELECT DISTINCT city FROM airbnb_listings;                -- unique values
```

## Filtering — numeric columns
```sql
WHERE number_of_rooms >= 3     -- 3 or more
WHERE number_of_rooms > 3      -- more than 3
WHERE number_of_rooms = 3      -- exactly 3
WHERE number_of_rooms <= 3     -- 3 or fewer
WHERE number_of_rooms < 3      -- fewer than 3
WHERE number_of_rooms BETWEEN 3 AND 6   -- inclusive range
```

## Filtering — text columns
```sql
WHERE city = 'Paris'
WHERE country IN ('USA', 'France')
WHERE city LIKE 'j%' AND city NOT LIKE '%t'   -- starts with 'j', does not end in 't'
```

## Filtering — multiple columns / missing data
```sql
WHERE city = 'Paris' AND number_of_rooms > 3
WHERE city = 'Paris' OR year_listed > 2012
WHERE number_of_rooms IS NULL          -- missing
WHERE number_of_rooms IS NOT NULL      -- not missing
```

## Aggregating
```sql
SELECT SUM(number_of_rooms) FROM airbnb_listings;   -- total
SELECT AVG(number_of_rooms) FROM airbnb_listings;   -- average
SELECT MAX(number_of_rooms) FROM airbnb_listings;   -- highest
SELECT MIN(number_of_rooms) FROM airbnb_listings;   -- lowest
```

## Grouping, filtering, and sorting
```sql
-- total/average/max/min rooms per country
SELECT country, SUM(number_of_rooms) FROM airbnb_listings GROUP BY country;
SELECT country, AVG(number_of_rooms) FROM airbnb_listings GROUP BY country;
SELECT country, MAX(number_of_rooms) FROM airbnb_listings GROUP BY country;
SELECT country, MIN(number_of_rooms) FROM airbnb_listings GROUP BY country;

-- alias + sort by the aggregated column
SELECT country, AVG(number_of_rooms) AS avg_rooms
FROM airbnb_listings GROUP BY country ORDER BY avg_rooms ASC;

-- filter the input rows BEFORE grouping (WHERE), then group
SELECT country, AVG(number_of_rooms)
FROM airbnb_listings WHERE country IN ('USA', 'Japan') GROUP BY country;

-- count rows per group
SELECT country, COUNT(id) AS number_of_listings
FROM airbnb_listings GROUP BY country;

-- filter groups AFTER aggregating (HAVING, not WHERE)
SELECT year_listed FROM airbnb_listings
GROUP BY year_listed HAVING COUNT(id) > 100;
```
**Key distinction**: `WHERE` filters rows before grouping; `HAVING` filters groups after
aggregation (e.g. "years with more than 100 listings" needs `HAVING COUNT(id) > 100`, not `WHERE`).

## Relevance to Class 7
DuckDB (from the main slide deck) lets you run exactly this SQL syntax directly against a
pandas DataFrame inside Python (`duckdb.query("SELECT ... FROM df ...").df()`), which is why
this cheat sheet is a useful quick reference during the DuckDB portion of the lecture.
