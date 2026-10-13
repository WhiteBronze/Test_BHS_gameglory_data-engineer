-- Gameglory ETL - SQL questions.
-- Run on the database AFTER loading batch_1 and batch_2:
--     sqlite3 gameglory.db < questions.sql
-- Write your query under each question. Put the result (or its first rows) into README.
-- Keep the requested sort order: it makes results comparable.

-- Q1. Top-10 tags by number of games.
--     Columns: tag, games_count. Order: games_count DESC, tag ASC.


-- Q2. For each release year from 2018 to 2026: number of games, number of free games
--     and the average price of PAID games in USD (rounded to 2 decimals).
--     Columns: year, games, free_games, avg_paid_price_usd. Order: year.


-- Q3. Top-10 games by number of reviews loaded into your database.
--     For each: title, reviews count, share of recommended reviews in % (1 decimal)
--     and positive_pct from the second source (stats.csv) for comparison.
--     Order: reviews count DESC, title ASC.


-- Q4. (Optional) Take the 5 tags with the most games (as in Q1). For each of them show the top-3 games
--     by owners (from stats.csv). Games without owners are skipped.
--     Columns: tag, rank, title, owners. Order: tag, rank. Ties in owners: by title.
--     Hint: window function ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...).


-- Q5. Price dynamics. Using price_history, find the games whose price changed between exports.
--     Columns: title, old_price, new_price, change_pct (1 decimal).
--     Show the 10 biggest price drops (order: change_pct ASC, title ASC).
--     Additionally (a separate query): how many games became cheaper, how many more expensive.
--     Hint: LAG() OVER (PARTITION BY ... ORDER BY ...).
