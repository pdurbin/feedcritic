DROP TABLE podcasts;

CREATE TABLE podcasts
(
  id serial NOT NULL,
  slug character varying(255) NOT NULL,
  name text NOT NULL,
  description text,
  feed_url text,
  rating bigint,
  every boolean,
  dead boolean,
  CONSTRAINT podcasts_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);

ALTER TABLE podcasts OWNER TO postgres;

COPY podcasts(slug,rating,every,dead,name,feed_url) FROM '/tmp/podcasts.tsv' WITH (DELIMITER E'\t', FORMAT CSV, HEADER true);
