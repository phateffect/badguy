CREATE TABLE ground_hours (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  date DATE NOT NULL,
  venue_id INTEGER NOT NULL,
  ground_id INTEGER NOT NULL,
  ground_name TEXT NOT NULL,
  hour SMALLINT NOT NULL,
  available BOOLEAN NOT NULL,
  price NUMERIC NOT NULL,

  UNIQUE(date, hour, venue_id, ground_id)
);
