CREATE TABLE public.stockrealtime (
	id bigserial NOT NULL,
	stockid varchar NULL,
	price decimal NULL,
	"change" decimal NULL,
	change_pct decimal NULL,
	volume decimal NULL,
	amount decimal NULL,
	amplitude decimal NULL,
	turnover_rate decimal NULL,
	volume_ratio decimal NULL,
	cdt date NULL,
	CONSTRAINT stockrealtime_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.stockrealtime IS '个股实时模型';

-- Column comments

COMMENT ON COLUMN public.stockrealtime.price IS '最新价格';
COMMENT ON COLUMN public.stockrealtime."change" IS '涨跌额';
COMMENT ON COLUMN public.stockrealtime.change_pct IS '涨跌幅';
COMMENT ON COLUMN public.stockrealtime.volume IS '成交量';
COMMENT ON COLUMN public.stockrealtime.amount IS '成交额';
COMMENT ON COLUMN public.stockrealtime.amplitude IS '振幅';
COMMENT ON COLUMN public.stockrealtime.turnover_rate IS '换手率';
COMMENT ON COLUMN public.stockrealtime.volume_ratio IS '量比';
