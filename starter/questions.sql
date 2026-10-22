-- Gameglory ETL - SQL questions.
-- Run on the database AFTER loading batch_1 and batch_2:
--     sqlite3 gameglory.db < questions.sql
-- Write your query under each question. Put the result (or its first rows) into README.
-- Keep the requested sort order: it makes results comparable.

-- Q1. Top-10 tags by number of games.
--     Columns: tag, games_count. Order: games_count DESC, tag ASC.
select gt.tag,
       count(*) as games_count
from game_tags gt
group by gt.tag
order by games_count desc, gt.tag asc
limit 10;


-- Q2. For each release year from 2018 to 2026: number of games, number of free games
--     and the average price of PAID games in USD (rounded to 2 decimals).
--     Columns: year, games, free_games, avg_paid_price_usd. Order: year.
select g.year,
       count(*) as games,
       sum(case when g.price_usd = 0 then 1 else 0 end) as free_games,
       round(avg(case when g.price_usd > 0 then g.price_usd end), 2) as avg_paid_price_usd
from games g
where g.year between 2018 and 2026
group by g.year
order by g.year;


-- Q3. Top-10 games by number of reviews loaded into your database.
--     For each: title, reviews count, share of recommended reviews in % (1 decimal)
--     and positive_pct from the second source (stats.csv) for comparison.
--     Order: reviews count DESC, title ASC.
select g.title,
       count(r.review_id) as reviews_count,
       round(100.0 * sum(case when r.voted_up = 1 then 1 else 0 end) / count(r.review_id), 1) as pct_recommended,
       s.positive_pct
from games g
join reviews r on r.game_id = g.game_id
left join stats s on s.game_id = g.game_id
group by g.game_id, g.title, s.positive_pct
order by reviews_count desc, g.title asc
limit 10;


-- Q4. (Optional) Take the 5 tags with the most games (as in Q1). For each of them show the top-3 games
--     by owners (from stats.csv). Games without owners are skipped.
--     Columns: tag, rank, title, owners. Order: tag, rank. Ties in owners: by title.
--     Hint: window function ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...).
with top_tags as (
    select gt.tag,
           count(*) as games_count
    from game_tags gt
    group by gt.tag
    order by games_count desc, gt.tag asc
    limit 5
),
ranked as (
    select tt.tag,
           g.title,
           s.owners,
           row_number() over (
               partition by tt.tag
               order by s.owners desc, g.title asc
           ) as rn
    from top_tags tt
    join game_tags gt on gt.tag = tt.tag
    join games g on g.game_id = gt.game_id
    join stats s on s.game_id = g.game_id
    where s.owners is not null
)
select tag, rn as rank, title, owners
from ranked
where rn <= 3
order by tag asc, rn asc;


-- Q5. Price dynamics. Using price_history, find the games whose price changed between exports.
--     Columns: title, old_price, new_price, change_pct (1 decimal).
--     Show the 10 biggest price drops (order: change_pct ASC, title ASC).
--     Additionally (a separate query): how many games became cheaper, how many more expensive.
--     Hint: LAG() OVER (PARTITION BY ... ORDER BY ...).
with price_pairs as (
    select ph.game_id,
           g.title,
           ph.observed_at,
           ph.price_usd,
           lag(ph.price_usd) over (
               partition by ph.game_id
               order by ph.observed_at
           ) as prev_price
    from price_history ph
    join games g on g.game_id = ph.game_id
)
select title,
       round(prev_price, 2) as old_price,
       round(price_usd, 2) as new_price,
       round(100.0 * (price_usd - prev_price) / prev_price, 1) as change_pct
from price_pairs
where prev_price is not null
  and prev_price > 0
  and price_usd <> prev_price
order by change_pct asc, title asc
limit 10;
with price_pairs as (
    select ph.game_id,
           ph.observed_at,
           ph.price_usd,
           lag(ph.price_usd) over (
               partition by ph.game_id
               order by ph.observed_at
           ) as prev_price
    from price_history ph
)
select
    sum(case when price_usd < prev_price then 1 else 0 end) as became_cheaper,
    sum(case when price_usd > prev_price then 1 else 0 end) as became_more_expensive
from price_pairs
where prev_price is not null
  and price_usd <> prev_price;
