CREATE TABLE public.stocktimesharing (
	stockid varchar NULL,
	"date" date NULL,
	price decimal NULL,
	avg_price decimal NULL,
	volume decimal NULL,
	amount decimal NULL,
	id bigserial NOT NULL,
	CONSTRAINT stocktimesharing_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.stocktimesharing IS '个股分时行情';
