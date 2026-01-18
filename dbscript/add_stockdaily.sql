CREATE TABLE public.stockdaily (
	id uuid NOT NULL,
	stockid varchar NOT NULL,
	"date" date NOT NULL,
	openprice decimal NOT NULL,
	closeprice decimal NULL,
	highprice decimal NULL,
	lowprice decimal NULL,
	change_gross decimal NULL,
	change_pct decimal NULL,
	gross decimal NULL,
	amount decimal NULL,
	turnover_rate decimal NULL,
	cdt date NULL,
	CONSTRAINT stockdaily_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.stockdaily IS '代表个股日线行情';

-- Column comments

COMMENT ON COLUMN public.stockdaily.openprice IS '代表开盘价';
COMMENT ON COLUMN public.stockdaily.closeprice IS '代表收盘价';
COMMENT ON COLUMN public.stockdaily.highprice IS '代表最高价';
COMMENT ON COLUMN public.stockdaily.lowprice IS '代表最低价';
COMMENT ON COLUMN public.stockdaily.change_gross IS '代表涨跌额是多少';
COMMENT ON COLUMN public.stockdaily.change_pct IS '代表涨跌幅是多少';
COMMENT ON COLUMN public.stockdaily.gross IS '成交量';
COMMENT ON COLUMN public.stockdaily.amount IS '成交额';
COMMENT ON COLUMN public.stockdaily.turnover_rate IS '换手率';
