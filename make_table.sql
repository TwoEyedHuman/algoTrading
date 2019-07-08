--drop table if exists prices;

create table prices (
    price_sk integer primary key
    ,symb varchar(5) not null
    ,ts timestamp not null
    ,price decimal(18,4) not null
    ,ask decimal(18,4)
    ,bid decimal(18,4)
    ,cum_day_vol integer
);

drop table if exists orders;

create table orders (
    orderId integer primary key
    ,symb varchar(5)
    ,oDate timestamp
    ,vol decimal(18,4)
    ,avgPrice decimal(18,4)
    ,status varchar(16)
    ,filled boolean
);

insert into orders values (0, 'NULL', '1900-01-01', 0, 0, 'Submitted', false);
