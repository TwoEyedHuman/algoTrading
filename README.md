Algo(rithmic) Trading
Brandon Locke

The purpose of this project it is build a basic automated trading platform. It uses Interactive Brokers API to execute paper trades, and uses a postgres database to track stock prices and trades.

There are two basic strategies setup:
(1) a fixed price threshold for a fixed stock

(2) determining the most volatile stock the previous day and setting a fixed price threshold for this stock
