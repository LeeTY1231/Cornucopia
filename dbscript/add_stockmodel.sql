CREATE TABLE public.stockmodel (
	stockid varchar NOT NULL,
	name varchar NULL,
	"location" varchar NULL,
	symbol varchar NULL,
	industry varchar NULL,
	ipo_date date NULL,
	downipo_date date NULL,
	CONSTRAINT stockmodel_pk PRIMARY KEY (stockid)
);
COMMENT ON TABLE public.stockmodel IS '股票基础数据';

-- Column comments

COMMENT ON COLUMN public.stockmodel."location" IS '公司所在区域';
COMMENT ON COLUMN public.stockmodel.symbol IS '代表在深市还是沪市上市';
COMMENT ON COLUMN public.stockmodel.industry IS '公司所属行业';
COMMENT ON COLUMN public.stockmodel.ipo_date IS '公司上市时间';
COMMENT ON COLUMN public.stockmodel.downipo_date IS '公司退市时间';
